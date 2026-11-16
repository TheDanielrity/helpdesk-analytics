"""Pruebas sin escrituras SQL: conversiones, límites y atomicidad."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import pandas as pd

from src.load_to_sql import (Column, LoadError, contracts, convert, execute_script,
                             inspect_tables, insert_rows, lock_empty, quality_baseline,
                             split_batches, transaction, verify_values)


class ConversionTests(unittest.TestCase):
    def test_decimal_exact_16_places_and_large_integer_part(self):
        column = Column("duration", "DECIMAL(38,16)", True)
        self.assertEqual(convert("123.1234567890123456", column), "123.1234567890123456")
        self.assertEqual(convert("-181782.279", column), "-181782.2790000000000000")
        value = "9999999999999999999999.9999999999999999"
        self.assertEqual(convert(value, column), value)
        for bad in ("1.00000000000000001", "1e22", "NaN", "Infinity", "bad", 1.5):
            with self.subTest(bad=bad), self.assertRaises(LoadError):
                convert(bad, column)

    def test_integer_exact_no_float(self):
        column = Column("id", "BIGINT", False)
        for value in ("9007199254740993", "9223372036854775807", "-9223372036854775808"):
            self.assertEqual(convert(value, column), int(value))
        for value in ("9223372036854775808", "1.2", pd.NA):
            with self.assertRaises(LoadError):
                convert(value, column)

    def test_timestamp_100ns_and_explicit_utc(self):
        column = Column("created", "DATETIMEOFFSET(7)", True)
        self.assertEqual(convert("2022-01-01 01:02:03.1234567+00:00", column), "2022-01-01T01:02:03.1234567+00:00")
        self.assertEqual(convert("2022-01-01T01:02:03Z", column), "2022-01-01T01:02:03.0000000+00:00")
        for value in ("2022-01-01 01:02:03", "2022-01-01T01:02:03-05:00", "2022-01-01T01:02:03.123456789Z"):
            with self.assertRaises(LoadError):
                convert(value, column)

    def test_null_text_and_flags(self):
        text = Column("id__raw", "NVARCHAR(256)", True)
        for value in (None, pd.NA, float("nan")):
            self.assertIsNone(convert(value, text))
        for value in ("unknown", "NA", "null", "  original  "):
            self.assertEqual(convert(value, text), value)
        bit = Column("dq_test", "BIT", False)
        self.assertIs(convert("False", bit), False)
        self.assertIs(convert("True", bit), True)
        with self.assertRaises(LoadError):
            convert("unknown", bit)
        with self.assertRaises(LoadError):
            convert("😀" * 129, text)


class SqlFlowTests(unittest.TestCase):
    def test_go_not_in_literals_or_comments(self):
        text = "SELECT 'first\nGO\nlast';\n/*\nGO\n*/\nGO -- end\nSELECT [GO], 'it''s GO';\ngo\n"
        batches = split_batches(text)
        self.assertEqual(len(batches), 2)
        self.assertIn("first\nGO\nlast", batches[0])
        for bad in ("SELECT 1\nGO 2\n", "SELECT 'not closed", ":r other.sql"):
            with self.assertRaises(LoadError):
                split_batches(bad)

    def test_script_stops_on_error_and_rolls_back(self):
        connection = MagicMock()
        cursor = connection.cursor.return_value
        cursor.nextset.return_value = False
        cursor.execute.side_effect = [RuntimeError("DDL failure"), None]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "example.sql"
            path.write_text("SELECT 1;\nGO\nSELECT 2;\n", encoding="utf-8")
            with self.assertRaises(RuntimeError):
                execute_script(connection, path)
        self.assertEqual(cursor.execute.call_count, 2)
        self.assertIn("ROLLBACK", cursor.execute.call_args.args[0])

    def test_no_commit_on_critical_failure(self):
        connection = MagicMock(autocommit=True)
        with self.assertRaises(LoadError):
            with transaction(connection):
                raise LoadError("validation failed")
        calls = [c.args[0] for c in connection.cursor.return_value.execute.call_args_list]
        self.assertIn("BEGIN TRANSACTION", calls[0])
        self.assertIn("ROLLBACK TRANSACTION", calls[-1])
        self.assertNotIn("COMMIT TRANSACTION;", calls)

    def test_commit_only_after_validation_and_pilot_rollback(self):
        connection = MagicMock(autocommit=True)
        with transaction(connection):
            self.assertNotIn("COMMIT TRANSACTION;", [c.args[0] for c in connection.cursor.return_value.execute.call_args_list])
        self.assertEqual(connection.cursor.return_value.execute.call_args.args[0], "COMMIT TRANSACTION;")
        with transaction(connection, commit=False):
            pass
        self.assertEqual(connection.cursor.return_value.execute.call_args.args[0], "ROLLBACK TRANSACTION;")

    def test_nonempty_table_refused_before_inserts(self):
        connection = MagicMock()
        connection.cursor.return_value.execute.return_value.fetchone.return_value = (1,)
        with self.assertRaisesRegex(LoadError, "Tabla con datos"):
            lock_empty(connection)
        connection.cursor.return_value.executemany.assert_not_called()

    def test_incompatible_schema_is_not_modified(self):
        connection = MagicMock()
        connection.cursor.return_value.execute.return_value.fetchone.return_value = ("V",)
        with self.assertRaisesRegex(LoadError, "incompatible"):
            inspect_tables(connection, {"issues": [Column("id", "BIGINT", False)]})
        self.assertEqual(connection.cursor.return_value.execute.call_count, 1)

    def test_parameter_batches_preserve_audit_and_nulls(self):
        schema = [Column("id", "BIGINT", False), Column("wf_total_time", "DECIMAL(38,16)", True),
                  Column("created", "DATETIMEOFFSET(7)", True), Column("id__raw", "NVARCHAR(256)", True)]
        frame = pd.DataFrame([["1", "1.1234567890123456", "2020-01-01T00:00:00Z", " 1.0 "],
                              ["2", pd.NA, pd.NA, pd.NA]], columns=[c.name for c in schema])
        connection = MagicMock()
        insert_rows(connection, "issues", frame, schema, 1, True)
        cursor = connection.cursor.return_value
        self.assertTrue(cursor.fast_executemany)
        self.assertEqual(cursor.executemany.call_count, 2)
        sql, batch = cursor.executemany.call_args_list[0].args
        self.assertEqual(sql.count("?"), 4)
        self.assertNotIn("1.1234567890123456", sql)
        self.assertEqual(batch[0][1], "1.1234567890123456")
        self.assertEqual(batch[0][3], " 1.0 ")
        self.assertEqual(cursor.executemany.call_args_list[1].args[1][0], (2, None, None, None))

    def test_full_comparison_detects_precision_change(self):
        columns = [Column("id", "BIGINT", False), Column("wf_total_time", "DECIMAL(38,16)", True)]
        frame = pd.DataFrame([["1", "1.1234567890123456"]], columns=[c.name for c in columns])
        connection = MagicMock()
        connection.cursor.return_value.fetchmany.side_effect = [[(1, "1.1234567890123450")], []]
        with self.assertRaisesRegex(LoadError, "Valor distinto"):
            verify_values(connection, "issues", frame, columns)

    def test_real_contract_and_quality_baseline(self):
        schema = contracts()
        self.assertEqual([len(c) for c in schema.values()], [102, 28])
        flags, nulls = quality_baseline()
        self.assertEqual(flags["issues"]["dq_negative_duration"], 55)
        self.assertEqual(flags["issues"]["dq_duration_mismatch"], 374)
        self.assertEqual(nulls["issue_change_history"]["value"], 1840)


if __name__ == "__main__":
    unittest.main()
