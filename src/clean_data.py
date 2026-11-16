"""Limpieza conservadora de HelpDesk; ejecutar desde cualquier directorio."""

import argparse
from decimal import Decimal, InvalidOperation
import hashlib
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATES = {"issues": ("started", "ended", "issue_created", "issue_resolution_date", "last_change_date"),
         "issues_change_history": ("created",)}
IDS = {"issues": ("id", "issue_num"),
       "issues_change_history": ("id", "issueid", "change_group_id")}
TEXT = {"issues": ("issue_proj", "issue_reporter", "issue_assignee", "issue_type", "issue_priority", "issue_resolution", "issue_status"),
        "issues_change_history": ("field", "value")}
REQUIRED = {"issues": set(DATES["issues"] + IDS["issues"] + TEXT["issues"] + ("wf_total_time",)),
            "issues_change_history": set(DATES["issues_change_history"] + IDS["issues_change_history"] + TEXT["issues_change_history"])}


def read_csv(path):
    # Sólo el campo vacío representa ausencia: 'NA', 'null' y 'unknown' son texto.
    return pd.read_csv(path, dtype="string", keep_default_na=False, na_values=[""])


def integer(value):
    """Sin float intermedio, truncamiento ni desbordamiento de Int64."""
    if pd.isna(value):
        return pd.NA
    try:
        number = Decimal(value)
        if number.is_finite() and number == number.to_integral_value() and -(2**63) <= number < 2**63:
            return int(number)
    except (InvalidOperation, ValueError):
        pass
    return pd.NA


def clean_frame(raw, dataset):
    missing = REQUIRED[dataset] - set(raw.columns)
    if missing:
        raise ValueError(f"{dataset}: faltan columnas obligatorias: {sorted(missing)}")
    if any(c.startswith("dq_") or c.endswith("__raw") for c in raw.columns):
        raise ValueError("La entrada contiene columnas reservadas dq_* o *__raw")
    out = raw.copy()
    out["dq_source_row"] = range(2, len(out) + 2)
    out["dq_duplicate_row"] = raw.duplicated(keep=False)
    changes = {}
    for column in IDS[dataset]:
        out[column + "__raw"] = raw[column]
        out[column] = raw[column].map(integer).astype("Int64")
        out[f"dq_invalid_{column}"] = raw[column].notna() & out[column].isna()
        out[f"dq_missing_{column}"] = raw[column].isna()
    out["dq_duplicate_id"] = out.id.notna() & out.id.duplicated(keep=False)
    for column in DATES[dataset]:
        out[column + "__raw"] = raw[column]
        out[column] = pd.to_datetime(raw[column], utc=True, errors="coerce", format="ISO8601")
        out[f"dq_invalid_{column}"] = raw[column].notna() & out[column].isna()
        out[f"dq_missing_{column}"] = raw[column].isna()
        out[f"dq_naive_{column}"] = raw[column].notna() & ~raw[column].str.contains(r"(?:Z|[+-]\d{2}:?\d{2})$", na=False)
    for column in TEXT[dataset]:
        stripped = raw[column].str.strip()
        # No convertir campos de sólo espacios en ausencias nuevas.
        changed = raw[column].notna() & stripped.ne("") & raw[column].ne(stripped)
        if changed.any():
            out[column + "__raw"] = raw[column]
            out.loc[changed, column] = stripped[changed]
        changes[column] = int(changed.sum())
    out["dq_missing_optional"] = raw[[c for c in raw if c not in IDS[dataset]]].isna().any(axis=1)
    if dataset == "issues":
        duration_columns = [c for c in raw if c.startswith("wf_")]
        numbers = raw[duration_columns].apply(pd.to_numeric, errors="coerce")
        out["dq_invalid_duration"] = (raw[duration_columns].notna() & numbers.isna()).any(axis=1)
        out["dq_negative_workflow_duration"] = numbers.lt(0).any(axis=1)
        elapsed = (out.ended - out.started).dt.total_seconds()
        out["dq_negative_elapsed"] = elapsed.lt(0)
        out["dq_negative_duration"] = out.dq_negative_elapsed | out.dq_negative_workflow_duration
        out["dq_duration_comparable"] = elapsed.notna() & numbers.wf_total_time.notna()
        out["dq_duration_mismatch"] = out.dq_duration_comparable & (numbers.wf_total_time - elapsed).abs().gt(1e-6)
        out["dq_resolution_before_creation"] = out.issue_resolution_date.lt(out.issue_created)
        out["dq_last_change_before_creation"] = out.last_change_date.lt(out.issue_created)
        out["dq_start_before_creation"] = out.started.lt(out.issue_created)
        out["dq_end_after_last_change"] = out.ended.gt(out.last_change_date)
        out["dq_duplicate_project_number"] = out.issue_proj.notna() & out.issue_num.notna() & out.duplicated(["issue_proj", "issue_num"], keep=False)
    return out, changes


def clean_datasets(issues, history):
    tickets, ticket_changes = clean_frame(issues, "issues")
    events, event_changes = clean_frame(history, "issues_change_history")
    events["dq_orphan_issue"] = events.issueid.notna() & ~events.issueid.isin(tickets.id.dropna())
    tickets["dq_no_history"] = ~tickets.id.isin(events.issueid.dropna())
    # Evitar un join que multiplique filas cuando existen claves duplicadas.
    unique = tickets.loc[tickets.id.notna() & ~tickets.dq_duplicate_id].set_index("id")
    events["dq_parent_ambiguous"] = events.issueid.isin(tickets.loc[tickets.dq_duplicate_id, "id"])
    events["dq_event_before_creation"] = events.created.lt(events.issueid.map(unique.issue_created))
    events["dq_event_after_last_change"] = events.created.gt(events.issueid.map(unique.last_change_date))
    informational = {"dq_source_row", "dq_missing_optional", "dq_no_history", "dq_duration_comparable"}
    for frame in (tickets, events):
        flags = [c for c in frame if c.startswith("dq_") and c not in informational and not c.startswith("dq_missing_")]
        required_missing = [f"dq_missing_{c}" for c in ("id", "issueid", "change_group_id") if f"dq_missing_{c}" in frame]
        frame["dq_has_problem"] = frame[flags + required_missing].fillna(False).any(axis=1)
    return tickets, events, {"issues": ticket_changes, "issues_change_history": event_changes}


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def run(raw_dir=ROOT / "data/raw", output_dir=ROOT / "data/processed", report=ROOT / "reports/data_quality.md"):
    raw_dir, output_dir, report = Path(raw_dir), Path(output_dir), Path(report)
    paths = [raw_dir / f"{name}.csv" for name in REQUIRED]
    destinations = [output_dir / f"{name}_clean.csv" for name in REQUIRED] + [report]
    protected = (ROOT / "data/raw").resolve()
    for dest in destinations:
        if dest.resolve() in [p.resolve() for p in paths] or dest.resolve().is_relative_to(protected) or dest.resolve().is_relative_to(raw_dir.resolve()):
            raise ValueError("Los resultados no pueden escribirse dentro de raw ni sobre entradas")
    hashes = [sha256(p) for p in paths]
    inputs = [read_csv(p) for p in paths]
    tickets, events, changes = clean_datasets(*inputs)
    output_dir.mkdir(parents=True, exist_ok=True)
    lines = ["# Calidad de datos — HelpDesk Analytics", "", "Generado por `src/clean_data.py`. Python " + sys.version.split()[0] + "; Pandas " + pd.__version__ + ".", "",
             "## Tratamiento y reproducción", "", "Ejecutar `python src/clean_data.py`; pruebas: `python -m unittest discover -s tests -v`.", "",
             "Se conservan orden, filas y columnas originales. IDs: Decimal exacto → Int64 nullable; fechas ISO8601 → UTC. Valores inválidos producen NA/NaT y un indicador; las columnas `__raw` conservan el texto previo. Fechas sin zona se interpretan UTC y se señalan: falta confirmar su zona real.", "",
             "Sólo se recortan espacios externos no vacíos en campos de códigos/categorías documentados; no se cambian espacios internos, mayúsculas ni categorías. Se preservan unknown y nulos; sólo campos CSV vacíos se leen como nulos. Duraciones originales se conservan textualmente; su conversión numérica es auxiliar para validar, sin reemplazos ni recortes a cero.", "",
             "## Resultados", "", "| Dataset | Entrada | Salida | Conservación |", "|---|---:|---:|---|"]
    for name, original, frame, path in zip(REQUIRED, inputs, (tickets, events), destinations):
        frame.to_csv(path, index=False)
        lines.append(f"| {name} | {len(original)} | {len(frame)} | {'SUPERADA' if len(original) == len(frame) else 'FALLIDA'} |")
    for name, original, frame in zip(REQUIRED, inputs, (tickets, events)):
        lines += ["", f"## {name}", "", "Columnas obligatorias: SUPERADA.", "", "| Indicador / validación | Registros | Estado |", "|---|---:|---|"]
        for column in frame:
            if column.startswith("dq_") and column != "dq_source_row":
                count = int(frame[column].sum())
                info = column in {"dq_missing_optional", "dq_no_history", "dq_duration_comparable"} or column.startswith("dq_missing_") and column not in {"dq_missing_id", "dq_missing_issueid", "dq_missing_change_group_id"}
                lines.append(f"| {column} | {count} | {'INFORMATIVA' if info else 'FALLIDA' if count else 'SUPERADA'} |")
        lines += ["", "Recortes de espacios por columna: " + ", ".join(f"{c}={n}" for c, n in changes[name].items()) + ".", "", "| Columna original | Nulos entrada | Nulos salida |", "|---|---:|---:|"]
        lines += [f"| {c} | {original[c].isna().sum()} | {frame[c].isna().sum()} |" for c in original]
        problem = frame.loc[frame.dq_has_problem, ["dq_source_row", "id"]].head(10)
        lines += ["", "Muestra de problemas (fila lógica CSV, id): " + str(list(problem.itertuples(index=False, name=None))) + "."]
    unchanged = hashes == [sha256(p) for p in paths]
    lines += ["", "## Trazabilidad de entradas", "", f"Originales sin cambios (SHA-256 antes/después): {'SUPERADA' if unchanged else 'FALLIDA'}.", ""]
    lines += [f"- `{p.name}`: `{digest}`" for p, digest in zip(paths, hashes)]
    lines += ["", "## Decisiones y limitaciones", "", "Las validaciones fallidas describen datos pendientes de revisión; no se fuerza su aprobación. `dq_has_problem` agrupa anomalías, no ausencias opcionales ni falta de histórico. Cada indicador cuenta filas y puede solaparse con otros. `dq_source_row` identifica el registro lógico original (cabecera=1).", "",
              "`dq_duration_mismatch` compara wf_total_time con ended-started en segundos, tolerancia absoluta 0.000001 s, sólo con ambos valores disponibles. No comparables no significa validación superada; consultar dq_duration_comparable y los indicadores de fechas faltantes/ inválidas. Se revisan todos los wf_* para negativos. No se infieren unidades adicionales ni se calcula una duración corregida.", "",
              "FEATURES.md documenta started/ended para snapshots, pero EXAMPLE.md y el CSV los contienen en issues. Las diferencias pueden obedecer a reglas de agregación desconocidas: requieren confirmación del proveedor. No se exige que resolución coincida con fin ni que un evento posterior a resolución sea inválido: puede haber reaperturas. Eventos fuera de creación/último cambio se señalan para revisión; padres duplicados impiden evaluarlos de forma inequívoca.", "",
              "La clave primaria validada es id en ambos archivos; change_group_id puede repetirse legítimamente y issue_num sólo se evalúa junto al proyecto. Las colisiones proyecto/número se señalan sin reasignar claves. Los tickets sin histórico no implican un huérfano del histórico. Los negativos de wf_* no implican necesariamente ended anterior a started.", "",
              "Nulos opcionales y unknown se conservan sin imputación. No se unifican categorías ni se eliminan duplicados, huérfanos o negativos. CSV no almacena tipos: al recargar usar el lector de este módulo y convertir fechas/IDs explícitamente. No se implementan SQL Server ni Power BI."]
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"issues: {len(tickets)}; history: {len(events)}; problemas: {tickets.dq_has_problem.sum()}/{events.dq_has_problem.sum()}; reporte: {report}")
    return tickets, events


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=ROOT / "data/raw")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data/processed")
    parser.add_argument("--report", type=Path, default=ROOT / "reports/data_quality.md")
    args = parser.parse_args()
    try:
        run(args.raw_dir, args.output_dir, args.report)
    except (OSError, ValueError, pd.errors.ParserError) as error:
        parser.exit(1, f"Error: {error}\n")
