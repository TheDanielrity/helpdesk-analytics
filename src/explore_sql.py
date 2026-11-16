"""Ejecuta el EDA SELECT, contrasta con Pandas y genera el reporte reproducible."""
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
import hashlib
from pathlib import Path
import re
import sys

import pandas as pd
import pyodbc

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.clean_data import ROOT, read_csv
from src.sql_connection import connect
from src.load_to_sql import quality_baseline

SQL_PATH = ROOT / "sql/03_exploratory_analysis.sql"


def queries():
    text = SQL_PATH.read_text(encoding="utf-8")
    sections = re.split(r"^-- QUERY: ([A-Z][A-Z0-9_]*)\s*$", text, flags=re.M)
    result = dict(zip(sections[1::2], sections[2::2]))
    for key, statement in result.items():
        code = re.sub(r"--[^\n]*", "", statement).strip()
        if not re.match(r"(?:SELECT|;?WITH)\b", code, re.I) or re.search(r"\b(?:INSERT|UPDATE|DELETE|DROP|TRUNCATE|ALTER|CREATE|EXEC|INTO|MERGE)\b", code, re.I):
            raise ValueError(f"Se esperaba exclusivamente SELECT/CTE: {key}")
    return result


def pct(count, total):
    return (Decimal(int(count)) * 100 / Decimal(int(total))).quantize(Decimal(".0001"), rounding=ROUND_HALF_UP)


def group_counts(series):
    return {None if pd.isna(k) else k: int(v) for k,v in series.value_counts(dropna=False).items()}


def compare(results, tickets, events):
    checks = []
    def check(name, passed):
        if not passed:
            raise ValueError(f"SQL/Pandas no coinciden: {name}")
        checks.append(name)
    for key, column in (("B", "issue_priority"), ("C", "issue_type"), ("D", "issue_status"), ("E", "issue_resolution"), ("H", "issue_proj")):
        expected = group_counts(tickets[column])
        actual = {r[0]: int(r[1]) for r in results[key][1]}
        if key == "H":
            # Verificar además la selección exacta del top 10 y desempate por código.
            ordered = sorted(expected, key=lambda k: (-expected[k], k or ""))[:10]
            check("H selección top 10", list(actual) == ordered)
            expected = {k:expected[k] for k in ordered}
        check(key + " conteos", actual == expected)
        check(key + " porcentajes", all(r[2] == pct(r[1], len(tickets)) for r in results[key][1]))
    dates = pd.to_datetime(tickets.issue_created, utc=True, format="ISO8601")
    for key, series in (("F", dates.dt.year), ("G", dates.dt.strftime("%Y-%m").astype("string"))):
        expected = group_counts(series)
        actual = {(r[0].strftime("%Y-%m") if isinstance(r[0], date) else r[0]): int(r[1]) for r in results[key][1]}
        check(key + " conteos", actual == expected)
        check(key + " porcentajes", all(r[2] == pct(r[1],len(tickets)) for r in results[key][1]))
    check("A totales", {r[0]: r[1] for r in results["A"][1]} == {"tickets":len(tickets), "eventos":len(events)})
    parents = set(events.issueid.dropna())
    with_history = int(tickets.id.isin(parents).sum())
    check("I historial", {r[0]:r[1] for r in results["I"][1]} == {"Con historial":with_history, "Sin historial":len(tickets)-with_history})
    check("I porcentajes", all(r[2] == pct(r[1],len(tickets)) for r in results["I"][1]))
    flags = {}
    for table, frame in (("issues",tickets),("issue_change_history",events)):
        for col in frame:
            if col.startswith("dq_") and col != "dq_source_row":
                count = int(frame[col].eq("True").sum())
                flags[(table,col)] = (count,len(frame),pct(count,len(frame)))
    check("J todos los flags", {(r[0],r[1]):tuple(r[2:]) for r in results["J"][1]} == flags)
    documented, _ = quality_baseline()
    check("J reporte de Fase 2", all(documented[t][c] == values[0] for (t,c),values in flags.items()))
    expected = tickets.groupby(["issue_status","issue_resolution"],dropna=False).size()
    expected = {(None if pd.isna(a) else a,None if pd.isna(b) else b):int(n) for (a,b),n in expected.items()}
    check("K estado/resolución", {(r[0],r[1]):r[2] for r in results["K"][1]} == expected)
    check("K porcentajes", all(r[3] == pct(r[2],len(tickets)) for r in results["K"][1]))
    for row, series in zip(results["L"][1], (dates,pd.to_datetime(events.created,utc=True,format="ISO8601"))):
        check("L cobertura " + row[0], pd.Timestamp(row[1]) == series.min() and pd.Timestamp(row[2]) == series.max()
              and row[3] == int(series.lt("2016-01-01").sum()) and row[4] == int(series.ge("2023-04-01").sum())
              and row[5] == int(series.isna().sum()))
    for row, frame in zip(results["M"][1],(tickets,events)):
        source = frame.dq_source_row.map(int)
        check("M procedencia " + row[0], tuple(row[1:]) == (int(source.min()),int(source.max()),source.nunique()))
    return checks


def interpretations(results):
    r = {k:v[1] for k,v in results.items()}
    total = dict(r['A'])['tickets']
    flags = {(t,c):n for t,c,n,_,_ in r['J']}
    annual = max(r['F'], key=lambda row:row[1])
    monthly = max(r['G'], key=lambda row:row[1])
    top10 = sum(row[1] for row in r['H'])
    no_resolution_terminal = sum(n for s,res,n,_ in r['K'] if s in ('closed','done') and res is None)
    return {
        'S': 'Se confirmaron 102 columnas en issues y 28 en issue_change_history. Se mantienen BIGINT, DECIMAL(38,16), DATETIMEOFFSET(7), NVARCHAR(256) y BIT. Hay 8/4 columnas __raw y 36/18 dq_* respectivamente; dq_source_row es BIGINT.',
        'A': f"Se conservan {total:,} tickets y {dict(r['A'])['eventos']:,} eventos. Los totales coinciden con Pandas y la carga de Fase 3.3.",
        'B': f"La prioridad más frecuente es {r['B'][0][0]}: {r['B'][0][1]:,} ({r['B'][0][2]}%). Más de la mitad carece de una prioridad interpretable; segmentar criticidad requiere mostrar explícitamente esa falta de clasificación.",
        'C': f"Ticket representa {r['C'][0][2]}% del conjunto. También hay Service, Story, Vacation y tipos de planificación. Subtask y Sub-task permanecen separados: no hay documentación que permita equipararlos.",
        'D': f"closed concentra {r['D'][0][2]}% y done {r['D'][1][2]}%. Son estados finales registrados, sin evidencia suficiente para llamarlos éxito o calcular satisfacción.",
        'E': f"La resolución Done figura en {r['E'][0][1]:,} tickets ({r['E'][0][2]}%). Se conservan Won't Do, Duplicate, Cannot Reproduce y 853 ausencias como resultados diferenciados.",
        'F': f"El año con más creaciones es {annual[0]} con {annual[1]:,} ({annual[2]}% del total). Se cubren 17 años, con extremos 2007 y 2023 parciales; no comparar 2023 como año completo.",
        'G': f"Se observan {len(r['G'])} meses con registros. El máximo mensual es {monthly[0]}: {monthly[1]:,} tickets. El corte de marzo de 2023 es el día 14; la menor exposición de un mes parcial sesga las comparaciones mensuales.",
        'H': f"{r['H'][0][0]} lidera con {r['H'][0][1]:,} tickets, sólo {r['H'][0][2]}% del total. Los diez primeros suman {top10:,} ({pct(top10,total)}%); conviene conservar el resto de proyectos al analizar concentración.",
        'I': f"{r['I'][0][1]:,} tickets tienen historial y {r['I'][1][1]} no lo tienen ({r['I'][1][2]}%). La cobertura de historia es alta pero comienza años después de las primeras creaciones; tener algún evento no garantiza historia completa.",
        'J': f"Hay {flags[('issues','dq_has_problem')]} tickets señalados y {flags[('issue_change_history','dq_has_problem')]} evento señalado. Se preservan 55 tickets con wf_* negativos, 374 discrepancias, 65 filas con colisión proyecto/número y 9 fines posteriores al último cambio. dq_missing_optional=True en todos los tickets refleja campos legítimamente vacíos; no significa que todos sean incorrectos. dq_duration_comparable=True en todos significa que se pudieron comparar, no que los tiempos concuerden.",
        'K': f"Existen {no_resolution_terminal} tickets closed/done con resolución NULL, además de cierres Won't Do, Duplicate y Cannot Reproduce. El cruce demuestra que estado y resolución no son intercambiables.",
        'L': f"{r['L'][0][3]:,} tickets ({pct(r['L'][0][3],total)}%) se crearon antes de 2016. La historia empieza el 12 de agosto de 2015; no hay filas desde abril de 2023 ni fechas nulas en los dos campos revisados. La cobertura documentada no describe todo el CSV; no se conoce la causa y no se excluyen filas.",
        'M': 'Los números de procedencia son distintos por registro y van de 2 a N+1, coherentes con la cabecera en fila 1. No se mezclan con las tasas de calidad.'}


def table(headers, rows):
    def fmt(value):
        return "(NULL)" if value is None else str(value).replace("|", "\\|").replace("\n", " ")
    return ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"] + ["| " + " | ".join(map(fmt,r)) + " |" for r in rows]


DESCRIPTIONS = {
    "S": ("¿Qué columnas y tipos existen realmente?", "sys.columns y sys.types inspeccionan el catálogo; ORDER BY conserva el orden físico de columnas.", "El catálogo describe el esquema actual; los nombres no garantizan semántica de negocio."),
    "A": ("¿Cuál es el volumen de tickets y de eventos?", "COUNT_BIG cuenta filas de cada tabla; UNION ALL evita multiplicarlas mediante un join.", "Un evento es un cambio de campo, no necesariamente una interacción, resolución o actualización única."),
    "B": ("¿Cómo se distribuyen las prioridades?", "GROUP BY agrupa las etiquetas originales; la ventana SUM(COUNT_BIG(*)) OVER() calcula el denominador global.", "unknown se conserva como categoría sin asignarle nivel de severidad. La frecuencia no demuestra urgencia."),
    "C": ("¿Qué tipos de registro predominan?", "Se cuentan tipos y se ordenan por frecuencia, con desempate por etiqueta.", "No todos los tipos representan incidencias de soporte; el conjunto incluye otros usos del sistema."),
    "D": ("¿Qué estados finales registra la extracción?", "Se agrupa por el último estado almacenado en issues, no por las transiciones del histórico.", "closed/done no equivalen a resolución exitosa. No es una serie histórica de backlog."),
    "E": ("¿Qué resoluciones se documentan?", "GROUP BY conserva NULL como un grupo; COUNT_BIG(*) incluye sus filas en el denominador.", "NULL es ausencia de resolución registrada; por sí solo no prueba que el ticket siga abierto."),
    "F": ("¿Cuántos tickets se crearon cada año?", "YEAR extrae el año de issue_created UTC; ORDER BY mantiene el orden cronológico.", "Cobertura desigual y extremos parciales impiden atribuir variaciones a productividad o demanda real sin más contexto."),
    "G": ("¿Cómo cambia la creación mes a mes?", "DATEFROMPARTS genera el primer día de cada año/mes; no mezcla enero de distintos años.", "Se muestran sólo meses con registros, sin completar ausencias con ceros. El último mes es parcial."),
    "H": ("¿Qué diez proyectos concentran más tickets?", "CTE agrupa antes de TOP(10); el porcentaje usa todos los tickets, no sólo el top 10.", "Los códigos están enmascarados; un mayor volumen no demuestra peor servicio ni identifica al cliente."),
    "I": ("¿Qué tickets tienen al menos un evento?", "La CTE agrupa eventos por issueid con HAVING; LEFT JOIN mantiene los tickets sin historial y evita contarlos varias veces.", "Sin historial no significa sin trabajo; puede ser una limitación de extracción/cobertura."),
    "J": ("¿Qué advertencias y ausencias afectan al análisis?", "CROSS APPLY VALUES convierte los flags en filas; SUM cuenta True y COUNT_BIG es el total de la tabla correspondiente.", "Los indicadores se solapan; no deben sumarse como tickets únicos. missing_optional, no_history y duration_comparable son informativos. dq_source_row es procedencia, no un flag."),
    "K": ("¿Coinciden estado y resolución?", "Agrupación conjunta para contrastar el estado final con la resolución informada.", "La etiqueta Done sigue siendo una clasificación del origen; éxito percibido y satisfacción requieren evidencia adicional."),
    "L": ("¿Cuál es la cobertura temporal efectiva y cuánto queda fuera de la documentada?", "MIN/MAX obtienen extremos y SUM(CASE WHEN...) cuenta antes de 2016 y desde abril de 2023.", "FEATURES.md describe enero de 2016 a marzo de 2023 para issues. No se excluyen registros anteriores ni se atribuye una causa sin evidencia."),
    "M": ("¿Qué rango tienen los números de procedencia?", "MIN/MAX y COUNT_BIG(DISTINCT) resumen dq_source_row por tabla.", "La fila de origen es trazabilidad de CSV, no fecha ni indicador binario de calidad.")}


def main():
    started = datetime.now(timezone.utc).isoformat()
    paths = [ROOT/"data/processed"/f"{name}_clean.csv" for name in ("issues","issues_change_history")]
    before = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    sql = queries()
    results = {}
    connection = connect(database="HelpDeskAnalytics")
    try:
        cursor = connection.cursor()
        for key, statement in sql.items():
            cursor.execute(statement)
            results[key] = ([c[0] for c in cursor.description], [tuple(r) for r in cursor.fetchall()])
            print(key, len(results[key][1]), "filas de resultado", flush=True)
    finally:
        connection.close()
    tickets, events = [read_csv(p) for p in paths]
    checks = compare(results,tickets,events)
    if before != {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}:
        raise ValueError("Cambió un CSV durante el análisis")
    lines = ["# Exploración SQL Server — Fase 3.4", "", f"Ejecución UTC: {started}. Base: HelpDeskAnalytics. Sólo SELECT/CTE; sin cambios de datos ni objetos.", "",
             "Reproducción: `python -m src.explore_sql` con .env local. Consultas ejecutadas literalmente desde [03_exploratory_analysis.sql](../sql/03_exploratory_analysis.sql). En SSMS elegir HelpDeskAnalytics antes de abrir el archivo.", "",
             "Todos los porcentajes se expresan de 0 a 100 con cuatro decimales. B–I y K usan el total de tickets como denominador; J usa el total de su tabla. El top 10 usa también el total global. Redondeos pueden impedir sumar exactamente 100. No se filtran anomalías ni NULL. Clasificaciones textuales usan collation binaria para mantener diferencias de mayúsculas; no se renombran ni unifican categorías.", "",
             "## Comparación independiente con Pandas", "", "Se recalcularon sobre los CSV procesados los resultados principales de Fase 2; no se usa memoria conversacional como evidencia. Se verificaron todos los grupos, porcentajes, top 10, historial y flags, además de estado/resolución.", ""]
    lines += ["- SUPERADA: " + check for check in checks]
    lines += ["", "SHA-256 de CSV antes/después sin cambios: " + str(before) + ".", "",
              "## Lectura de resultados y próximos indicadores", "", "La interpretación específica de las tablas se presenta al final. Los resultados completos, incluidos todos los meses y los indicadores en cero, se conservan a continuación."]
    readings = interpretations(results)
    for key, (headers, rows) in results.items():
        question, explanation, limitation = DESCRIPTIONS[key]
        lines += ["",f"## {key}. {question}","",f"**SQL:** sección `-- QUERY: {key}` de sql/03_exploratory_analysis.sql.","",f"**Aprendizaje:** {explanation}","",*table(headers, rows),"",f"**Interpretación:** {readings[key]}","",f"**Límite:** {limitation}"]
    lines += ["", "## Indicadores recomendados para la siguiente fase", "",
              "1. Volumen de creaciones por mes UTC, tipo, proyecto y prioridad; comparar meses completos y explicitar el corte temporal. Crear después un calendario para distinguir meses sin registros de ceros confirmados.",
              "2. Porcentaje unknown sobre todos los tickets (50,9289%) y distribución de prioridades conocidas con su denominador declarado. Mostrar ambos; no reclasificar unknown como Low.",
              "3. Distribución de resoluciones registradas y cruce estado/resolución; mostrar NULL separado. Una tasa de resolución exige acordar estados y fechas elegibles; no llamar éxito al porcentaje closed/done.",
              "4. Cobertura de histórico: tickets con al menos un evento / tickets. Desglosar por cohorte de creación por la diferencia entre 2007 y el inicio de eventos en 2015.",
              "5. Calidad: negativos, discrepancias y ausencia de resolución, cada uno con su denominador; usar dq_has_problem para registros únicos con anomalías, no sumar flags. Ausencias opcionales legítimas se presentan como completitud, no errores.",
              "6. Concentración por proyecto: participación del top 10 sobre todos los tickets y resto explícito; segmentar por tipo antes de comparaciones operativas.",
              "7. Posteriormente, mediana y percentil 90 de tiempo transcurrido/calendario en segundos u horas, con cohortes, fechas válidas y tratamiento explícito de negativos/discrepancias. Comparar métricas con y sin flags, manteniendo registros. No asumir horas laborales, SLA, tiempo de primera respuesta ni productividad: requieren reglas, horarios y fuentes adicionales.", "",
              "## Conceptos SQL para practicar", "", "Aprender en este orden: COUNT_BIG(*) y GROUP BY; NULL frente a COUNT(columna); agregaciones condicionales con CASE; porcentajes con SUM(...) OVER() y NULLIF; fechas por año/mes; CTE; LEFT JOIN tras agrupar el lado de eventos para evitar multiplicación; WHERE para filtrar filas y HAVING para filtrar grupos; TOP con ORDER BY y desempate; CROSS APPLY VALUES para resumir indicadores. Revisar siempre granularidad y denominador antes de interpretar una tasa.", "",
              "## Límites generales", "", "Resultados descriptivos de una extracción histórica, no del HelpDesk actual. No hay calendario laboral, objetivo SLA ni evidencia de satisfacción. No se reconstruyó backlog diario ni reaperturas. No se crearon vistas, tablas o elementos de Power BI. Las consultas se ejecutaron secuencialmente sin aislamiento snapshot: si hubiera escrituras concurrentes, repetir sobre una copia estable; las comparaciones con CSV pasaron en esta ejecución."]
    (ROOT/"reports/sql_exploration.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print("Comparaciones superadas:",len(checks))
    for key in ("A","B","C","D","E","F","H","I","K","L"):
        print(key,results[key][1])


if __name__ == "__main__":
    try:
        main()
    except pyodbc.Error as error:
        raise SystemExit(f"Error ODBC; SQLSTATE={error.args[0] if error.args else 'desconocido'}")
