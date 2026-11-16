"""Validación del contrato SQL sin conectar ni modificar datos."""
import re
import unittest

from src.clean_data import ROOT, read_csv
from src.prepare_sql_schema import profile
from src.sql_connection import connection_string


class ConnectionTests(unittest.TestCase):
    def test_windows_and_secure_defaults(self):
        result = connection_string({"SQL_SERVER": "localhost"})
        self.assertIn("Encrypt={yes}", result)
        self.assertIn("TrustServerCertificate={no}", result)
        self.assertIn("Trusted_Connection={yes}", result)
        self.assertNotIn("PWD=", result)

    def test_sql_credentials_escaped(self):
        result = connection_string({"SQL_SERVER": "localhost", "SQL_AUTH": "sql", "SQL_USER": "test", "SQL_PASSWORD": "x};y"})
        self.assertIn("PWD={x}};y}", result)
        self.assertNotIn("Trusted_Connection", result)

    def test_missing_configuration_rejected(self):
        for env in ({}, {"SQL_SERVER": "x", "SQL_AUTH": "other"}, {"SQL_SERVER": "x", "SQL_AUTH": "sql"}, {"SQL_SERVER": "x", "SQL_ENCRYPT": "perhaps"}):
            with self.assertRaises(ValueError):
                connection_string(env)


class SchemaTests(unittest.TestCase):
    def test_tsql_parser(self):
        try:
            from sqlfluff.core import FluffConfig, Linter
        except ImportError:
            self.skipTest("Instalar requirements-dev.txt para parser T-SQL")
        config = FluffConfig(configs={"core": {"dialect": "tsql", "templater": "raw"}})
        for name in ("01_create_database.sql", "02_create_tables.sql"):
            sql = (ROOT / "sql" / name).read_text(encoding="utf-8")
            parsed = Linter(config=config).parse_string(sql)
            self.assertIsNotNone(parsed.tree)
            self.assertFalse(parsed.violations, str(parsed.violations))

    def test_ddl_complete_and_values_fit(self):
        ddl = (ROOT / "sql/02_create_tables.sql").read_text(encoding="utf-8")
        frames = []
        for dataset, table, expected in (("issues", "issues", 102), ("issues_change_history", "issue_change_history", 28)):
            path = ROOT / "data/processed" / f"{dataset}_clean.csv"
            if not path.exists():
                self.skipTest("CSV locales no disponibles")
            frame = read_csv(path)
            frames.append(frame)
            columns = profile(frame, dataset)
            self.assertEqual(len(columns), expected)
            body = ddl.split(f"CREATE TABLE [stg].[{table}] (", 1)[1].split("    );", 1)[0]
            names = re.findall(r"^\s*\[([^]]+)\]\s+(?:BIGINT|BIT|DATETIMEOFFSET|DECIMAL|NVARCHAR)", body, re.MULTILINE)
            self.assertEqual(names, list(frame.columns))
            for column, kind, nullable, *_ in columns:
                self.assertIn(f"[{column}] {kind} {'NULL' if nullable else 'NOT NULL'}", body)
        self.assertTrue(frames[1].issueid.isin(frames[0].id).all())
        self.assertIn("FOREIGN KEY ([issueid]) REFERENCES [stg].[issues] ([id])", ddl)

    def test_no_destructive_or_import_statements(self):
        for name in ("01_create_database.sql", "02_create_tables.sql"):
            ddl = (ROOT / "sql" / name).read_text(encoding="utf-8")
            code = re.sub(r"--[^\n]*", "", ddl)
            self.assertIsNone(re.search(r"\b(DROP|DELETE|TRUNCATE|INSERT|MERGE|BULK)\b", code, re.IGNORECASE))
        ignore = (ROOT / ".gitignore").read_text()
        self.assertIn("\n.env\n", ignore)
        self.assertIn("!.env.example", ignore)
        self.assertIn("*.csv", ignore)


if __name__ == "__main__":
    unittest.main()
