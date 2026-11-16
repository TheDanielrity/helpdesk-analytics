"""Carga inicial conservadora: python -m src.load_to_sql --create-schema.

Sólo carga tablas vacías. Todas las filas se comparan antes de COMMIT.
Los CSV se leen como texto para evitar pérdida de precisión por float.
"""
import argparse
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, localcontext
import hashlib
import json
from pathlib import Path
import re
import sys
from time import perf_counter

import pandas as pd
import pyodbc

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.clean_data import ROOT, read_csv
from src.sql_connection import connect

DATABASE = "HelpDeskAnalytics"
TABLES = (("issues", "issues", 66691, 102),
          ("issues_change_history", "issue_change_history", 257508, 28))


class LoadError(ValueError):
    """Error controlado; nunca incluye credenciales ni cadenas de conexión."""


def require(condition, message):
    if not condition:
        raise LoadError(message)


@dataclass(frozen=True)
class Column:
    name: str
    kind: str
    nullable: bool


def contracts():
    """El DDL revisado es el contrato; no inferir tipos durante la carga."""
    text = (ROOT / "sql/02_create_tables.sql").read_text(encoding="utf-8")
    result = {}
    pattern = r"^\s*\[([a-z_]+)\] (BIGINT|BIT|DATETIMEOFFSET\(7\)|DECIMAL\(38,16\)|NVARCHAR\(256\)) (NOT NULL|NULL),?\s*$"
    for _, table, _, count in TABLES:
        body = text.split(f"CREATE TABLE [stg].[{table}] (", 1)[1].split("    );", 1)[0]
        columns = [Column(n, k, null == "NULL") for n, k, null in re.findall(pattern, body, re.M)]
        require(len(columns) == count, f"Contrato incompleto: {table}")
        result[table] = columns
    return result


def split_batches(sql):
    """GO aislado (con comentario opcional); respeta strings y comentarios.

    Soporta el subconjunto usado por los dos scripts. Rechaza GO n y sqlcmd.
    """
    batches, lines = [], []
    state, depth = None, 0
    for line in sql.splitlines(keepends=True):
        if state is None and depth == 0:
            if re.fullmatch(r"\s*GO\s*(?:--[^\n]*)?\s*", line, re.I):
                if "".join(lines).strip():
                    batches.append("".join(lines))
                lines = []
                continue
            require(not re.match(r"\s*(?:GO\s+\d|:|!!)", line, re.I), "Separador sqlcmd no soportado")
        lines.append(line)
        i = 0
        while i < len(line):
            pair, char = line[i:i+2], line[i]
            if depth:
                if pair == "/*":
                    depth += 1; i += 2; continue
                if pair == "*/":
                    depth -= 1; i += 2; continue
            elif state:
                closing = "]" if state == "[" else state
                if char == closing:
                    if i + 1 < len(line) and line[i+1] == closing:
                        i += 2; continue
                    state = None
            elif pair == "--":
                break
            elif pair == "/*":
                depth = 1; i += 2; continue
            elif char in ("'", '"', "["):
                state = char
            i += 1
    require(state is None and depth == 0, "SQL con literal/comentario sin cerrar")
    if "".join(lines).strip():
        batches.append("".join(lines))
    return batches


def execute_script(connection, path):
    cursor = connection.cursor()
    try:
        for batch in split_batches(path.read_text(encoding="utf-8")):
            cursor.execute(batch)
            while cursor.nextset():
                pass
    except BaseException:
        cursor.execute("IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;")
        raise
    finally:
        cursor.close()


def utc_text(value):
    require(isinstance(value, str) and bool(re.search(r"(?:Z|\+00:00)$", value)), "Fecha sin UTC explícito")
    try:
        stamp = pd.Timestamp(value)
        require(not pd.isna(stamp) and stamp.nanosecond % 100 == 0, "Fecha excede precisión de 100 ns")
    except (ValueError, OverflowError) as error:
        raise LoadError("Fecha UTC inválida") from error
    fraction = stamp.microsecond * 10 + stamp.nanosecond // 100
    return stamp.strftime("%Y-%m-%dT%H:%M:%S") + f".{fraction:07d}+00:00"


def convert(value, column):
    if value is None or pd.isna(value):
        require(column.nullable, f"NULL prohibido: {column.name}")
        return None
    if column.kind == "BIT":
        require(value in ("True", "False"), f"Booleano inválido: {column.name}")
        return value == "True"
    if column.kind.startswith("NVARCHAR"):
        require(isinstance(value, str) and len(value.encode("utf-16-le")) // 2 <= 256,
                f"Texto excede NVARCHAR(256): {column.name}")
        return value
    if column.kind.startswith("DATETIMEOFFSET"):
        return utc_text(value)
    require(isinstance(value, str), f"Se requiere número textual exacto: {column.name}")
    try:
        number = Decimal(value)
        require(number.is_finite(), f"Número no finito: {column.name}")
        if column.kind == "BIGINT":
            require(number == number.to_integral_value() and -(2**63) <= number < 2**63,
                    f"BIGINT inválido: {column.name}")
            return int(number)
        with localcontext() as context:
            context.prec = 50
            require(abs(number) < Decimal(10)**22, f"DECIMAL fuera de rango: {column.name}")
            exact = number.quantize(Decimal("1e-16"))
            require(exact == number, f"DECIMAL requeriría redondeo: {column.name}")
            return format(exact, ".16f")
    except InvalidOperation as error:
        raise LoadError(f"Número inválido: {column.name}") from error


def input_frames(schema):
    result = {}
    for dataset, table, expected, _ in TABLES:
        frame = read_csv(ROOT / "data/processed" / f"{dataset}_clean.csv")
        require(list(frame) == [c.name for c in schema[table]], f"Columnas CSV incompatibles: {table}")
        require(len(frame) == expected, f"Conteo CSV inesperado: {table}")
        for col in schema[table]:
            for value in frame[col.name].unique():
                convert(value, col)
        ids = frame.id.map(int)
        require(ids.is_unique, f"IDs CSV duplicados: {table}")
        result[table] = frame.iloc[ids.argsort()].reset_index(drop=True)
    require(result["issue_change_history"].issueid.map(int).isin(result["issues"].id.map(int)).all(), "CSV con huérfanos")
    return result


def sql_shape(row):
    name, kind, length, precision, scale, nullable, identity, computed, default, usertype = row
    require(not identity and not computed and default == 0 and not usertype, f"Columna con comportamiento ajeno al contrato: {name}")
    types = {"bigint": "BIGINT", "bit": "BIT", "nvarchar": f"NVARCHAR({length // 2})",
             "datetimeoffset": f"DATETIMEOFFSET({scale})", "decimal": f"DECIMAL({precision},{scale})"}
    require(kind in types, f"Tipo no permitido: {name}")
    return Column(name, types[kind], bool(nullable))


def inspect_tables(connection, schema, *, allow_missing=False, empty=True):
    cursor = connection.cursor()
    counts = {}
    for table, columns in schema.items():
        object_name = f"stg.{table}"
        obj = cursor.execute("SELECT type FROM sys.objects WHERE object_id=OBJECT_ID(?)", object_name).fetchone()
        if obj is None:
            require(allow_missing, f"Falta tabla {object_name}")
            counts[table] = None
            continue
        require(obj[0].strip() == "U", f"Objeto existente incompatible: {object_name}")
        actual = cursor.execute("""SELECT c.name,t.name,c.max_length,c.precision,c.scale,c.is_nullable,
            c.is_identity,c.is_computed,c.default_object_id,t.is_user_defined
            FROM sys.columns c JOIN sys.types t ON c.user_type_id=t.user_type_id
            WHERE c.object_id=OBJECT_ID(?) ORDER BY c.column_id""", object_name).fetchall()
        require([sql_shape(r) for r in actual] == columns, f"Esquema incompatible: {object_name}")
        indexes = cursor.execute("""SELECT i.name,i.is_primary_key,i.is_unique,i.type,i.is_disabled,
            i.has_filter,ic.key_ordinal,c.name,ic.is_included_column,ic.is_descending_key
            FROM sys.indexes i JOIN sys.index_columns ic ON i.object_id=ic.object_id AND i.index_id=ic.index_id
            JOIN sys.columns c ON c.object_id=ic.object_id AND c.column_id=ic.column_id
            WHERE i.object_id=OBJECT_ID(?) AND i.index_id>0 ORDER BY i.name,ic.index_column_id""", object_name).fetchall()
        pk = [r for r in indexes if r[1]]
        require(len(pk) == 1 and tuple(pk[0][2:]) == (True, 1, False, False, 1, "id", False, False), f"PK incompatible: {table}")
        if table == "issue_change_history":
            ix = [r for r in indexes if r[0] == "IX_history_issueid_created"]
            require(len(ix) == 2 and [r[7] for r in ix] == ["issueid", "created"] and
                    all(not r[1] and not r[2] and r[3] == 2 and not r[4] and not r[5] and not r[8] and not r[9] for r in ix), "Índice histórico incompatible")
        extra = [r for r in indexes if not r[1] and r[0] != "IX_history_issueid_created"]
        require(not extra, f"Índices adicionales requieren revisión: {table}")
        special = cursor.execute("""SELECT
            (SELECT COUNT(*) FROM sys.triggers WHERE parent_id=OBJECT_ID(?) AND is_disabled=0),
            (SELECT COUNT(*) FROM sys.check_constraints WHERE parent_object_id=OBJECT_ID(?)),
            (SELECT temporal_type FROM sys.tables WHERE object_id=OBJECT_ID(?))""", object_name, object_name, object_name).fetchone()
        require(tuple(special) == (0, 0, 0), f"Triggers/CHECK/temporal no contemplados: {table}")
        counts[table] = cursor.execute(f"SELECT COUNT_BIG(*) FROM [stg].[{table}]").fetchone()[0]
        if empty:
            require(counts[table] == 0, f"Tabla con datos: {object_name}; carga cancelada")
    if counts.get("issue_change_history") is not None:
        fk = cursor.execute("""SELECT pc.name,rs.name,rt.name,rc.name,fk.is_disabled,fk.is_not_trusted,
            fk.delete_referential_action,fk.update_referential_action
            FROM sys.foreign_keys fk JOIN sys.foreign_key_columns f ON fk.object_id=f.constraint_object_id
            JOIN sys.columns pc ON pc.object_id=f.parent_object_id AND pc.column_id=f.parent_column_id
            JOIN sys.tables rt ON rt.object_id=f.referenced_object_id JOIN sys.schemas rs ON rs.schema_id=rt.schema_id
            JOIN sys.columns rc ON rc.object_id=f.referenced_object_id AND rc.column_id=f.referenced_column_id
            WHERE fk.parent_object_id=OBJECT_ID(N'stg.issue_change_history')""").fetchall()
        require([tuple(r) for r in fk] == [("issueid", "stg", "issues", "id", False, False, 0, 0)], "FK incompatible o no confiable")
    cursor.close()
    return counts


def prepare(schema, create):
    connection = connect(database="master")
    actions = []
    try:
        cursor = connection.cursor()
        version = cursor.execute("SELECT CAST(SERVERPROPERTY('ProductVersion') AS nvarchar(128))").fetchone()[0]
        exists = cursor.execute("SELECT DB_ID(?)", DATABASE).fetchone()[0] is not None
        if not exists:
            require(create, "Base ausente; ejecutar con --create-schema")
            execute_script(connection, ROOT / "sql/01_create_database.sql")
            actions.append("01_create_database.sql ejecutado (base ausente)")
        cursor.execute("USE [HelpDeskAnalytics]")
        before = inspect_tables(connection, schema, allow_missing=True)
        if any(n is None for n in before.values()):
            require(create, "Tablas ausentes; ejecutar con --create-schema")
            execute_script(connection, ROOT / "sql/02_create_tables.sql")
            actions.append("02_create_tables.sql ejecutado (tablas ausentes)")
        inspect_tables(connection, schema)
        return {"version": version, "before": before, "database_existed": exists, "ddl": actions}
    finally:
        connection.close()


@contextmanager
def transaction(connection, *, commit=True):
    require(connection.autocommit, "La carga controla BEGIN/COMMIT explícitamente")
    cursor = connection.cursor()
    cursor.execute("SET XACT_ABORT ON; SET NOCOUNT ON; SET LOCK_TIMEOUT 10000; BEGIN TRANSACTION;")
    try:
        yield
    except BaseException:
        cursor.execute("IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;")
        raise
    else:
        cursor.execute("COMMIT TRANSACTION;" if commit else "ROLLBACK TRANSACTION;")
    finally:
        cursor.close()


def lock_empty(connection):
    for _, table, _, _ in TABLES:
        count = connection.cursor().execute(f"SELECT COUNT_BIG(*) FROM [stg].[{table}] WITH (TABLOCKX,HOLDLOCK)").fetchone()[0]
        require(count == 0, f"Tabla con datos: stg.{table}; carga cancelada")


def insert_statement(table, columns):
    require(table in {t[1] for t in TABLES}, "Tabla fuera del contrato")
    names = ",".join(f"[{c.name}]" for c in columns)
    # Transporte Unicode explícito: evita conversiones a float y SQL_TYPE_TIMESTAMP sin offset.
    params = [f"CONVERT({c.kind}, ?)" if c.kind.startswith(("DECIMAL", "DATETIMEOFFSET")) else "?" for c in columns]
    return f"INSERT INTO [stg].[{table}] ({names}) VALUES ({','.join(params)})"


def insert_rows(connection, table, frame, columns, batch_size, fast):
    cursor = connection.cursor()
    cursor.fast_executemany = fast
    sizes = [(pyodbc.SQL_BIGINT, 0, 0) if c.kind == "BIGINT" else
             (pyodbc.SQL_BIT, 0, 0) if c.kind == "BIT" else
             (pyodbc.SQL_WVARCHAR, 40, 0) if c.kind.startswith(("DECIMAL", "DATETIMEOFFSET")) else
             (pyodbc.SQL_WVARCHAR, 256, 0) for c in columns]
    cursor.setinputsizes(sizes)
    statement = insert_statement(table, columns)
    try:
        for start in range(0, len(frame), batch_size):
            batch = [tuple(convert(v, c) for v, c in zip(row, columns))
                     for row in frame.iloc[start:start+batch_size].itertuples(index=False, name=None)]
            cursor.executemany(statement, batch)
            if start % 20000 == 0:
                print(f"{table}: {min(start+batch_size,len(frame))}/{len(frame)} filas enviadas", flush=True)
    finally:
        cursor.close()


def verify_values(connection, table, frame, columns):
    """Compara cada celda, con tipos canónicos y filas ordenadas por PK."""
    expressions = [f"CONVERT(varchar(40), [{c.name}], 127)" if c.kind.startswith("DATETIMEOFFSET") else
                   f"CONVERT(varchar(40), [{c.name}])" if c.kind.startswith("DECIMAL") else f"[{c.name}]" for c in columns]
    cursor = connection.cursor()
    cursor.execute(f"SELECT {','.join(expressions)} FROM [stg].[{table}] ORDER BY [id]")
    expected = iter(frame.itertuples(index=False, name=None))
    checked = 0
    try:
        while True:
            rows = cursor.fetchmany(2000)
            if not rows:
                break
            for actual in rows:
                source = next(expected, None)
                require(source is not None, f"Filas SQL adicionales: {table}")
                for value, stored, col in zip(source, actual, columns):
                    wanted = convert(value, col)
                    if stored is not None and col.kind.startswith("DATETIMEOFFSET"):
                        stored = utc_text(stored)
                    require(wanted == stored, f"Valor distinto en {table}.{col.name}, id={source[0]}")
                checked += 1
        require(next(expected, None) is None, f"Faltan filas SQL: {table}")
        return checked * len(columns)
    finally:
        cursor.close()


def quality_baseline():
    """Lee los conteos dq_* y nulos originales del reporte de Fase 2."""
    current, flags, nulls = None, {}, {}
    text = (ROOT / "reports/data_quality.md").read_text(encoding="utf-8")
    for line in text.splitlines():
        if line in ("## issues", "## issues_change_history"):
            current = "issues" if line == "## issues" else "issue_change_history"
            flags[current], nulls[current] = {}, {}
        if current and line.startswith("| "):
            fields = [p.strip() for p in line.split("|")[1:-1]]
            if len(fields) == 3 and fields[0].startswith("dq_") and fields[1].isdigit():
                flags[current][fields[0]] = int(fields[1])
            elif len(fields) == 3 and fields[1].isdigit() and fields[2].isdigit():
                nulls[current][fields[0]] = int(fields[2])
    require(set(flags) == {t[1] for t in TABLES} and all(flags.values()) and all(nulls.values()), "Reporte de calidad incompleto")
    return flags, nulls


def validate(connection, frames, schema, baseline=None):
    results = {}
    for table, frame in frames.items():
        columns = schema[table]
        cursor = connection.cursor()
        count, distinct = cursor.execute(f"SELECT COUNT_BIG(*),COUNT_BIG(DISTINCT [id]) FROM [stg].[{table}]").fetchone()
        require(count == len(frame) and distinct == count, f"Conteo/PK incorrectos: {table}")
        null_expr = [f"SUM(CONVERT(bigint,CASE WHEN [{c.name}] IS NULL THEN 1 ELSE 0 END))" for c in columns]
        null_row = cursor.execute(f"SELECT {','.join(null_expr)} FROM [stg].[{table}]").fetchone()
        nulls = dict(zip([c.name for c in columns], [int(v or 0) for v in null_row]))
        require(nulls == {c: int(frame[c].isna().sum()) for c in frame}, f"NULL distintos: {table}")
        bits = [c.name for c in columns if c.kind == "BIT"]
        expressions = [f"SUM(CONVERT(bigint,[{c}]))" for c in bits]
        flags = dict(zip(bits, map(int, cursor.execute(f"SELECT {','.join(expressions)} FROM [stg].[{table}]").fetchone())))
        require(flags == {c: int(frame[c].eq("True").sum()) for c in bits}, f"Flags distintos: {table}")
        durations = [c.name for c in columns if c.kind.startswith("DECIMAL")]
        negatives = {}
        if durations:
            expressions = [f"SUM(CONVERT(bigint,CASE WHEN [{c}]<0 THEN 1 ELSE 0 END))" for c in durations]
            negatives = dict(zip(durations, map(int, cursor.execute(f"SELECT {','.join(expressions)} FROM [stg].[{table}]").fetchone())))
            for c in durations:
                require(negatives[c] == sum(Decimal(v) < 0 for v in frame[c].dropna()), f"Negativos distintos: {c}")
        if baseline:
            old_flags, old_nulls = baseline
            require(flags == old_flags[table], f"Indicadores no coinciden con data_quality.md: {table}")
            require(all(nulls.get(c) == n for c, n in old_nulls[table].items()), f"NULL no coinciden con data_quality.md: {table}")
        cells = verify_values(connection, table, frame, columns)
        results[table] = {"rows": count, "duplicate_ids": count-distinct, "nulls": nulls,
                          "flags": flags, "negatives": negatives, "exact_cells": cells}
        print(f"Validado {table}: {count} filas / {cells} celdas exactas", flush=True)
        cursor.close()
    orphans = connection.cursor().execute("""SELECT COUNT_BIG(*) FROM stg.issue_change_history h
        LEFT JOIN stg.issues i ON i.id=h.issueid WHERE i.id IS NULL""").fetchone()[0]
    require(orphans == 0, "Histórico con huérfanos")
    results["orphans"] = orphans
    return results


def representative(frames, schema):
    result = {}
    for table, frame in frames.items():
        indices = {0, len(frame)-1}
        for col in schema[table]:
            series = frame[col.name]
            for mask in (series.isna(), series.notna()):
                if mask.any():
                    indices.add(int(mask[mask].index[0]))
            if col.kind == "BIT":
                matches = series.eq("True")
                if matches.any():
                    indices.add(int(matches[matches].index[0]))
            if col.kind.startswith("DECIMAL"):
                values = series.dropna().map(Decimal)
                if len(values):
                    indices.update((int(values.idxmin()), int(values.idxmax())))
                    indices.add(int(values.map(lambda v: -v.as_tuple().exponent).idxmax()))
            if col.kind.startswith("DATETIMEOFFSET"):
                matches = series.str.contains(r"\.\d*[1-9]\d*", na=False)
                if matches.any():
                    indices.add(int(matches[matches].index[0]))
        result[table] = frame.loc[sorted(indices)]
    parents = frames["issues"].id.isin(result["issue_change_history"].issueid)
    ids = set(result["issues"].id) | set(frames["issues"].loc[parents, "id"])
    result["issues"] = frames["issues"].loc[frames["issues"].id.isin(ids)]
    return result


def hashes():
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted((ROOT / "data").glob("*/*.csv"))}


def write_report(details, path):
    lines = ["# Importación SQL Server — Fase 3.3", "", f"Fecha UTC: {details['started']}", "",
             f"Estado: **{details['status']}**. Duración total: {details['seconds']:.3f} s.", "",
             "Datos originales/procesados leídos sin modificaciones. No se imprimen credenciales.", ""]
    if "error" in details:
        lines += [f"Error: {details['error']}", ""]
    if "preparation" in details:
        prep = details["preparation"]
        lines += [f"SQL Server: {prep['version']}. Base existente antes: {prep['database_existed']}.", "",
                  "DDL: " + ("; ".join(prep["ddl"]) or "Objetos existentes verificados; sin DDL") + ".", ""]
    lines += ["## Conversión y transacciones", "",
              "Pandas string con sólo campos vacíos como ausencias → None/SQL NULL. BIGINT exacto y BIT True/False→1/0. NVARCHAR conserva texto, unknown y __raw sin strip. DECIMAL se valida con Decimal (contexto de 50 dígitos), sin float ni redondeo, y se transporta como Unicode de 16 decimales con CONVERT(DECIMAL(38,16), ?). Fechas UTC canónicas de 7 decimales se transportan como Unicode con CONVERT(DATETIMEOFFSET(7), ?); lectura explícita como ISO evita pérdida del offset en ODBC.", "",
              "Inserciones parametrizadas, setinputsizes explícitos y lotes acotados. Primero tickets, luego eventos. Prueba representativa con filas reales y ROLLBACK; después carga completa con BEGIN TRANSACTION y bloqueos TABLOCKX/HOLDLOCK sobre ambas tablas vacías. Ante error previo al COMMIT: ROLLBACK completo. Se compara cada celda, NULL, flag y negativo y el reporte de Fase 2 antes de confirmar. Se comprueban PK, FK confiable e índice en el catálogo.", "",
              "## Ejecución", "", "```json", json.dumps({k:v for k,v in details.items() if k not in {"validation", "hashes", "error"}}, ensure_ascii=False, indent=2), "```", ""]
    if "validation" in details:
        v = details["validation"]
        lines += ["## Conteos e integridad", "", "| Tabla | Antes | Después | IDs duplicados | Celdas exactas |", "|---|---:|---:|---:|---:|"]
        for _, table, _, _ in TABLES:
            r = v[table]
            before = details["preparation"]["before"][table]
            lines.append(f"| stg.{table} | {0 if before is None else before} | {r['rows']} | {r['duplicate_ids']} | {r['exact_cells']} |")
        lines += ["", f"Huérfanos: {v['orphans']}. Conteos NULL/indicadores coinciden con CSV y reports/data_quality.md. Todas las celdas fueron verificadas, incluyendo las muestras de precisión, UTC, negativos y auditoría."]
        for _, table, _, _ in TABLES:
            lines += ["", f"## {table}: NULL, calidad y negativos", "", "| Columna | NULL conservados | True conservados | Negativos conservados |", "|---|---:|---:|---:|"]
            r = v[table]
            for c,n in r["nulls"].items():
                lines.append(f"| {c} | {n} | {r['flags'].get(c, '—')} | {r['negatives'].get(c, '—')} |")
    lines += ["", "## Huellas de archivos", "", "```json", json.dumps(details.get("hashes", {}), indent=2), "```", "",
              "Las anomalías de Fase 2 permanecen; una importación correcta conserva esas advertencias. El éxito confirma fidelidad de almacenamiento, no resuelve sus causas de negocio.", "",
              "Referencias: [pyodbc Cursor](https://github.com/mkleehammer/pyodbc/wiki/Cursor), [GO](https://learn.microsoft.com/en-us/sql/t-sql/language-elements/sql-server-utilities-statements-go)."]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines)+"\n", encoding="utf-8")


def run(*, create=False, batch_size=1000, fast=True):
    require(1 <= batch_size <= 10000, "batch-size debe estar entre 1 y 10000")
    start = perf_counter()
    details = {"started": datetime.now(timezone.utc).isoformat(), "status": "NO CONFIRMADA",
               "batch_size": batch_size, "fast_executemany": fast, "pyodbc": pyodbc.version,
               "hashes": hashes()}
    connection, committing = None, False
    report = ROOT / "reports/sql_load_report.md"
    try:
        schema = contracts()
        frames = input_frames(schema)
        baseline = quality_baseline()
        details["preparation"] = prepare(schema, create)
        print("Base y esquema verificados; tablas vacías.", flush=True)
        connection = connect(database=DATABASE)
        details["odbc_driver"] = connection.getinfo(pyodbc.SQL_DRIVER_NAME)
        details["odbc_version"] = connection.getinfo(pyodbc.SQL_DRIVER_VER)
        sample = representative(frames, schema)
        pilot_start = perf_counter()
        with transaction(connection, commit=False):
            lock_empty(connection)
            for table, frame in sample.items():
                insert_rows(connection, table, frame, schema[table], batch_size, fast)
            validate(connection, sample, schema)
        details["pilot"] = {"rows": {t:len(f) for t,f in sample.items()}, "result": "EXACTO; ROLLBACK",
                            "seconds": round(perf_counter()-pilot_start, 3)}
        print("Prueba de compatibilidad exacta y revertida.", flush=True)
        load_start = perf_counter()
        with transaction(connection):
            lock_empty(connection)
            inspect_tables(connection, schema)
            for table, frame in frames.items():
                insert_rows(connection, table, frame, schema[table], batch_size, fast)
            details["insert_seconds"] = round(perf_counter()-load_start, 3)
            check_start = perf_counter()
            details["validation"] = validate(connection, frames, schema, baseline)
            require(details["hashes"] == hashes(), "CSV modificados durante la carga")
            details["validation_seconds"] = round(perf_counter()-check_start, 3)
            committing = True
        details["status"] = "COMMIT CONFIRMADO"
        details["load_seconds"] = round(perf_counter()-load_start, 3)
        connection.close()
        connection = connect(database=DATABASE)
        details["persisted_counts"] = inspect_tables(connection, schema, empty=False)
        require(details["persisted_counts"] == {t:len(f) for t,f in frames.items()}, "Conteos tras COMMIT inesperados")
        print("COMMIT confirmado y conteos comprobados desde otra conexión.", flush=True)
    except BaseException as error:
        if details["status"] == "COMMIT CONFIRMADO":
            details["status"] = "COMMIT CONFIRMADO; comprobación posterior incompleta"
        elif committing:
            details["status"] = "COMMIT SIN CONFIRMACIÓN; inspeccionar servidor antes de reintentar"
        else:
            details["status"] = "CARGA CANCELADA; sin COMMIT"
        if isinstance(error, pyodbc.Error):
            details["error"] = f"ODBC SQLSTATE={error.args[0] if error.args else 'desconocido'}"
        elif isinstance(error, LoadError):
            details["error"] = str(error)
        else:
            details["error"] = type(error).__name__
        # Conservar evidencia de una carga previa exitosa al rechazar un reintento.
        if report.exists():
            report = report.with_name("sql_load_attempt_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f") + ".md")
        print(details["status"] + ": " + details["error"], flush=True)
        return_code = 1
    else:
        return_code = 0
    finally:
        if connection is not None:
            connection.close()
        details["seconds"] = perf_counter()-start
        write_report(details, report)
        print(f"Reporte: {report}", flush=True)
    return return_code


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--create-schema", action="store_true", help="Ejecuta DDL sólo para objetos ausentes")
    parser.add_argument("--batch-size", type=int, default=1000)
    parser.add_argument("--no-fast", action="store_true", help="Usar executemany convencional; mantiene todas las validaciones")
    args = parser.parse_args()
    raise SystemExit(run(create=args.create_schema, batch_size=args.batch_size, fast=not args.no_fast))
