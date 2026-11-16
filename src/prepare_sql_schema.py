"""Perfila CSV sin modificarlos y genera DDL y diccionario de columnas."""
from decimal import Decimal
import hashlib
import re

import pandas as pd

from src.clean_data import DATES, IDS, ROOT, TEXT, read_csv


def sql_type(column, dataset):
    if column.endswith("__raw"):
        return "NVARCHAR(256)"
    if column == "dq_source_row" or column in IDS[dataset]:
        return "BIGINT"
    if column.startswith("dq_"):
        return "BIT"
    if column in DATES[dataset]:
        return "DATETIMEOFFSET(7)"
    if column.startswith("wf_"):
        return "DECIMAL(38,16)"
    if column.startswith("wfe_") or column in {"issue_contr_count", "issue_comments_count", "processing_steps"}:
        return "BIGINT"
    if column in TEXT[dataset]:
        return "NVARCHAR(256)"
    raise ValueError(f"Columna sin asignación explícita: {dataset}.{column}")


def profile(frame, dataset):
    result = []
    for column in frame:
        kind = sql_type(column, dataset)
        values = frame[column].dropna()
        maximum_length = max((len(x.encode("utf-16-le")) // 2 for x in values.unique()), default=0)
        scale = None
        if kind.startswith("NVARCHAR"):
            assert maximum_length <= 256, (column, maximum_length)
        elif kind in {"BIGINT", "DECIMAL(38,16)"}:
            numbers = [Decimal(v) for v in values.unique()]
            assert all(n.is_finite() for n in numbers), column
            scale = max((max(0, -n.as_tuple().exponent) for n in numbers), default=0)
            if kind == "BIGINT":
                assert all(n == n.to_integral_value() and -(2**63) <= n < 2**63 for n in numbers), column
            else:
                assert scale <= 16 and all(abs(n) < Decimal(10)**22 for n in numbers), column
        elif kind == "BIT":
            assert set(values.unique()) <= {"True", "False"}, column
        else:
            converted = pd.to_datetime(values, utc=True, format="ISO8601", errors="raise")
            assert converted.notna().all()
            assert all(re.search(r"(?:\+00:00|Z)$", v) for v in values.unique()), column
            assert all(n % 100 == 0 for n in converted.array.asi8), column
        required = column == "id" or column in {"issueid", "change_group_id", "dq_source_row"} or kind == "BIT"
        if required:
            assert frame[column].notna().all(), column
        result.append((column, kind, not required, int(frame[column].isna().sum()), maximum_length, scale))
    assert frame.id.is_unique and frame.id.notna().all()
    return result


def main():
    ddl = ["-- Generado con python -m src.prepare_sql_schema; no contiene carga de datos.",
           "-- Las tablas existentes no se alteran: comparar con el diccionario antes de reutilizarlas.",
           "USE [HelpDeskAnalytics];", "GO",
           "IF DB_NAME() <> N'HelpDeskAnalytics' THROW 50001, 'La base actual debe ser HelpDeskAnalytics.', 1;",
           "SET XACT_ABORT ON;",
           "IF SCHEMA_ID(N'stg') IS NULL EXEC(N'CREATE SCHEMA [stg] AUTHORIZATION [dbo];');",
           "BEGIN TRANSACTION;"]
    report = ["# Diseño SQL Server — Fase 3.1", "", "Perfil exhaustivo de los CSV procesados. No se han importado filas ni ejecutado los scripts DDL.", "",
              "CSV no tiene tipos físicos; los tipos siguientes son tipos lógicos verificados sobre todos los valores no vacíos, sin inferencia float. Longitud en unidades UTF-16. La nulabilidad es el contrato de carga; se permiten nulos de campos opcionales aunque hoy no existan.", ""]
    frames = []
    for dataset, table in (("issues", "issues"), ("issues_change_history", "issue_change_history")):
        path = ROOT / "data/processed" / f"{dataset}_clean.csv"
        before = hashlib.sha256(path.read_bytes()).hexdigest()
        frame = read_csv(path)
        frames.append(frame)
        columns = profile(frame, dataset)
        report += [f"## stg.{table}", "", f"Fuente: `{path.name}`; {len(frame)} registros; {len(columns)} columnas; SHA-256 `{before}`.", "",
                   "| Columna real | Tipo SQL validado | Nullable | Nulos | Longitud máxima | Escala observada |", "|---|---|---|---:|---:|---:|"]
        ddl += [f"IF OBJECT_ID(N'stg.{table}', N'U') IS NULL", "BEGIN", f"    CREATE TABLE [stg].[{table}] ("]
        declarations = []
        for c, kind, nullable, nulls, length, scale in columns:
            declarations.append(f"        [{c}] {kind} {'NULL' if nullable else 'NOT NULL'}")
            report.append(f"| {c} | {kind} | {'sí' if nullable else 'no'} | {nulls} | {length} | {scale if scale is not None else '—'} |")
        declarations.append(f"        CONSTRAINT [PK_{table}] PRIMARY KEY CLUSTERED ([id])")
        if table == "issue_change_history":
            declarations.append("        CONSTRAINT [FK_history_issues] FOREIGN KEY ([issueid]) REFERENCES [stg].[issues] ([id])")
        ddl += [",\n".join(declarations), "    );", "END;"]
        assert before == hashlib.sha256(path.read_bytes()).hexdigest()
    assert frames[1].issueid.isin(frames[0].id).all()
    ddl += ["-- Línea temporal por ticket y soporte de la clave foránea.",
            "IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'stg.issue_change_history') AND name = N'IX_history_issueid_created')",
            "    CREATE INDEX [IX_history_issueid_created] ON [stg].[issue_change_history] ([issueid], [created]);",
            "COMMIT TRANSACTION;", "GO"]
    report += ["", "## Contrato y decisiones", "",
               "Claves id no nulas y únicas en ambas fuentes; todos los issueid existen en issues.id. Relación 1:N, FK sin cascadas. Cargar primero tickets. No hay UNIQUE sobre proyecto/issue_num (65 filas con colisiones), ni sobre change_group_id (agrupa cambios).",
               "", "BIGINT: identificadores validados, contadores integrales y fila de procedencia. DECIMAL(38,16): todos los wf_* en segundos, incluidos negativos y artefactos decimales existentes; hasta 16 decimales observados, 22 posiciones enteras disponibles. Nunca FLOAT ni redondeos para estos datos.",
               "", "DATETIMEOFFSET(7): conserva zona UTC y admite 100 ns; todos los valores actuales caben sin pérdida. NVARCHAR(256): códigos, categorías y __raw, longitud UTF-16 verificada; margen explícito para futuras entradas. BIT: todos los indicadores booleanos; dq_source_row es BIGINT. No se añaden valores por defecto.",
               "", "PK clustered por id en cada tabla y un solo índice adicional (issueid, created) para joins y línea temporal. Los filtros de fecha/prioridad/proyecto se evaluarán con planes reales antes de añadir índices. Ningún índice sobre flags aislados o texto de auditoría.",
               "", "No se imponen CHECK temporales ni de duración positiva: impedirían conservar anomalías válidamente señaladas. Las columnas opcionales son NULL y unknown permanece texto. El staging tipado representa la entrega validada actual: futuras claves inválidas, huérfanas o duplicadas requieren cuarentena separada, sin borrar registros ni desactivar restricciones para forzar una carga.",
               "", "Los __raw presentes se conservan íntegramente; no se inventan columnas __raw ausentes del CSV. DECIMAL conserva valor numérico, no formato textual (.0, notación científica); el CSV inmutable y su hash conservan esa representación. Al importar se convertirán vacíos a None, booleanos explícitamente a 0/1 y números con Decimal, nunca con float. Las fechas se enviarán en ISO8601 con offset explícito para evitar pérdida de zona por ODBC.",
               "", "Ejecución repetida: CREATE DATABASE y CREATE TABLE sólo si faltan; no migra ni verifica tablas preexistentes. Antes de reutilizar una base existente comparar sys.columns, sys.types, sys.key_constraints, sys.foreign_keys y sys.indexes con este contrato. Un error de índices/tabla revierte la transacción por XACT_ABORT. No ejecutar dentro de otra transacción.",
               "", "Referencias: [datetimeoffset](https://learn.microsoft.com/en-us/sql/t-sql/data-types/datetimeoffset-transact-sql), [decimal](https://learn.microsoft.com/en-us/sql/t-sql/data-types/decimal-and-numeric-transact-sql)."]
    (ROOT / "sql/02_create_tables.sql").write_text("\n".join(ddl) + "\n", encoding="utf-8")
    (ROOT / "reports/sql_schema.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print("Perfil y DDL generados: 2 tablas; claves, relación, tipos, longitudes y precisión validados; CSV intactos.")


if __name__ == "__main__":
    main()
