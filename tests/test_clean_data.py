"""Pruebas sintéticas adversas y verificación de la entrega real."""
import tempfile
from pathlib import Path
import unittest

import pandas as pd

from src.clean_data import REQUIRED, ROOT, clean_datasets, clean_frame, integer, read_csv, run


def fixture():
    issues = pd.DataFrame({c: pd.Series([pd.NA], dtype="string") for c in sorted(REQUIRED["issues"])})
    for c, value in {"id": "1.0", "issue_num": "2.0", "issue_proj": "P", "started": "2020-01-01T01:00:00+01:00", "ended": "2019-12-31T23:59:50Z", "issue_created": "2020-01-01T00:00:00Z", "last_change_date": "2020-01-02T00:00:00Z", "wf_total_time": "-10", "issue_priority": "unknown"}.items():
        issues[c] = pd.Series([value], dtype="string")
    history = pd.DataFrame({"id": ["10.0"], "issueid": ["1.0"], "change_group_id": ["20.0"], "field": [" status "], "value": [pd.NA], "created": ["2020-01-01T00:00:00Z"]}, dtype="string")
    return issues, history


class CleaningTests(unittest.TestCase):
    def test_conservation_dates_negative_and_missing(self):
        issues, history = fixture()
        tickets, events, _ = clean_datasets(issues, history)
        self.assertEqual((len(tickets), len(events)), (1, 1))
        self.assertEqual(str(tickets.id.dtype), "Int64")
        self.assertEqual(tickets.started[0], pd.Timestamp("2020-01-01T00:00:00Z"))
        self.assertEqual(str(tickets.started.dt.tz), "UTC")
        self.assertTrue(tickets.dq_negative_duration[0])
        self.assertFalse(tickets.dq_duration_mismatch[0])
        self.assertEqual(tickets.wf_total_time[0], "-10")
        self.assertEqual(tickets.issue_priority[0], "unknown")
        self.assertTrue(pd.isna(tickets.issue_resolution_date[0]))
        self.assertFalse(tickets.dq_invalid_issue_resolution_date[0])
        self.assertTrue(pd.isna(events.value[0]))
        self.assertEqual(events.field[0], "status")
        self.assertEqual(events.field__raw[0], " status ")

    def test_invalid_values_and_exact_ids(self):
        for bad in ("1.5", "inf", "NaN", "9223372036854775808", "bad"):
            self.assertTrue(pd.isna(integer(bad)))
        self.assertEqual(integer("9007199254740993.0"), 9007199254740993)
        issues, _ = fixture()
        issues.loc[0, "started"] = "invalid"
        issues.loc[0, "id"] = "1.5"
        out, _ = clean_frame(issues, "issues")
        self.assertTrue(out.dq_invalid_id[0])
        self.assertTrue(out.dq_invalid_started[0])
        self.assertEqual(out.started__raw[0], "invalid")

    def test_duplicate_keys_orphans_and_temporal(self):
        issues, history = fixture()
        duplicate = pd.concat([issues, issues], ignore_index=True)
        tickets, events, _ = clean_datasets(duplicate, history)
        self.assertTrue(tickets.dq_duplicate_id.all())
        self.assertTrue(events.dq_parent_ambiguous[0])
        history.loc[0, "issueid"] = "999"
        tickets, events, _ = clean_datasets(issues, history)
        self.assertTrue(events.dq_orphan_issue[0])
        history.loc[0, "issueid"] = "1"
        history.loc[0, "created"] = "2019-01-01T00:00:00Z"
        _, events, _ = clean_datasets(issues, history)
        self.assertTrue(events.dq_event_before_creation[0])
        issues.loc[0, "wf_total_time"] = "20"
        tickets, _, _ = clean_datasets(issues, history)
        self.assertTrue(tickets.dq_duration_mismatch[0])

    def test_schema_and_protect_raw(self):
        issues, _ = fixture()
        with self.assertRaisesRegex(ValueError, "obligatorias"):
            clean_frame(issues.drop(columns="id"), "issues")
        with self.assertRaisesRegex(ValueError, "raw"):
            run(output_dir=ROOT / "data/raw")

    def test_csv_missing_tokens_and_reproducibility(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            token_file = root / "tokens.csv"
            token_file.write_text('a,b,c,d\nunknown,,NA,null\n', encoding="utf-8")
            values = read_csv(token_file)
            self.assertTrue(pd.isna(values.b[0]))
            self.assertEqual(list(values.loc[0, ["a", "c", "d"]]), ["unknown", "NA", "null"])
            raw = root / "raw"
            raw.mkdir()
            for name, frame in zip(REQUIRED, fixture()):
                frame.to_csv(raw / f"{name}.csv", index=False)
            run(raw, root / "out", root / "report.md")
            before = (root / "out/issues_clean.csv").read_bytes()
            run(raw, root / "out", root / "report.md")
            self.assertEqual(before, (root / "out/issues_clean.csv").read_bytes())


class RealDataTests(unittest.TestCase):
    def test_real_delivery(self):
        paths = [ROOT / "data/raw" / f"{n}.csv" for n in REQUIRED]
        if not all(p.exists() for p in paths):
            self.skipTest("CSV reales no disponibles")
        raw = [read_csv(p) for p in paths]
        tickets, events, _ = clean_datasets(*raw)
        self.assertEqual((len(tickets), len(events)), (66691, 257508))
        for original, frame, name in zip(raw, (tickets, events), REQUIRED):
            self.assertEqual(len(original), len(frame))
            self.assertTrue(frame.id.notna().all())
            self.assertTrue(frame.id.is_unique)
            saved = read_csv(ROOT / "data/processed" / f"{name}_clean.csv")
            self.assertEqual(len(saved), len(original))
            self.assertEqual(saved.id.tolist(), frame.id.astype("string").tolist())
        self.assertFalse(events.dq_orphan_issue.any())
        self.assertEqual(int(tickets.dq_negative_workflow_duration.sum()), 55)
        self.assertEqual(int(tickets.dq_negative_elapsed.sum()), 0)
        self.assertEqual(int(tickets.dq_duration_mismatch.sum()), 374)
        self.assertEqual(int(tickets.issue_priority.eq("unknown").sum()), int(raw[0].issue_priority.eq("unknown").sum()))
        for column in raw[0]:
            self.assertTrue(tickets.loc[raw[0][column].isna(), column].isna().all())


if __name__ == "__main__":
    unittest.main()
