# Calidad de datos — HelpDesk Analytics

Generado por `src/clean_data.py`. Python 3.13.2; Pandas 2.3.3.

## Tratamiento y reproducción

Ejecutar `python src/clean_data.py`; pruebas: `python -m unittest discover -s tests -v`.

Se conservan orden, filas y columnas originales. IDs: Decimal exacto → Int64 nullable; fechas ISO8601 → UTC. Valores inválidos producen NA/NaT y un indicador; las columnas `__raw` conservan el texto previo. Fechas sin zona se interpretan UTC y se señalan: falta confirmar su zona real.

Sólo se recortan espacios externos no vacíos en campos de códigos/categorías documentados; no se cambian espacios internos, mayúsculas ni categorías. Se preservan unknown y nulos; sólo campos CSV vacíos se leen como nulos. Duraciones originales se conservan textualmente; su conversión numérica es auxiliar para validar, sin reemplazos ni recortes a cero.

## Resultados

| Dataset | Entrada | Salida | Conservación |
|---|---:|---:|---|
| issues | 66691 | 66691 | SUPERADA |
| issues_change_history | 257508 | 257508 | SUPERADA |

## issues

Columnas obligatorias: SUPERADA.

| Indicador / validación | Registros | Estado |
|---|---:|---|
| dq_duplicate_row | 0 | SUPERADA |
| dq_invalid_id | 0 | SUPERADA |
| dq_missing_id | 0 | SUPERADA |
| dq_invalid_issue_num | 0 | SUPERADA |
| dq_missing_issue_num | 0 | INFORMATIVA |
| dq_duplicate_id | 0 | SUPERADA |
| dq_invalid_started | 0 | SUPERADA |
| dq_missing_started | 0 | INFORMATIVA |
| dq_naive_started | 0 | SUPERADA |
| dq_invalid_ended | 0 | SUPERADA |
| dq_missing_ended | 0 | INFORMATIVA |
| dq_naive_ended | 0 | SUPERADA |
| dq_invalid_issue_created | 0 | SUPERADA |
| dq_missing_issue_created | 0 | INFORMATIVA |
| dq_naive_issue_created | 0 | SUPERADA |
| dq_invalid_issue_resolution_date | 0 | SUPERADA |
| dq_missing_issue_resolution_date | 853 | INFORMATIVA |
| dq_naive_issue_resolution_date | 0 | SUPERADA |
| dq_invalid_last_change_date | 0 | SUPERADA |
| dq_missing_last_change_date | 1 | INFORMATIVA |
| dq_naive_last_change_date | 0 | SUPERADA |
| dq_missing_optional | 66691 | INFORMATIVA |
| dq_invalid_duration | 0 | SUPERADA |
| dq_negative_workflow_duration | 55 | FALLIDA |
| dq_negative_elapsed | 0 | SUPERADA |
| dq_negative_duration | 55 | FALLIDA |
| dq_duration_comparable | 66691 | INFORMATIVA |
| dq_duration_mismatch | 374 | FALLIDA |
| dq_resolution_before_creation | 0 | SUPERADA |
| dq_last_change_before_creation | 0 | SUPERADA |
| dq_start_before_creation | 0 | SUPERADA |
| dq_end_after_last_change | 9 | FALLIDA |
| dq_duplicate_project_number | 65 | FALLIDA |
| dq_no_history | 41 | INFORMATIVA |
| dq_has_problem | 450 | FALLIDA |

Recortes de espacios por columna: issue_proj=0, issue_reporter=58, issue_assignee=0, issue_type=0, issue_priority=0, issue_resolution=0, issue_status=0.

| Columna original | Nulos entrada | Nulos salida |
|---|---:|---:|
| id | 0 | 0 |
| started | 0 | 0 |
| ended | 0 | 0 |
| issue_num | 0 | 0 |
| issue_proj | 0 | 0 |
| issue_reporter | 0 | 0 |
| issue_assignee | 31047 | 31047 |
| issue_contr_count | 0 | 0 |
| issue_type | 0 | 0 |
| issue_priority | 0 | 0 |
| issue_created | 0 | 0 |
| issue_resolution_date | 853 | 853 |
| issue_resolution | 853 | 853 |
| issue_status | 0 | 0 |
| issue_comments_count | 0 | 0 |
| last_change_date | 1 | 1 |
| wf_in_review | 66614 | 66614 |
| wfe_in_review | 0 | 0 |
| wf_deployment | 66556 | 66556 |
| wfe_deployment | 0 | 0 |
| wf_resolved | 38546 | 38546 |
| wfe_resolved | 0 | 0 |
| wf_open | 78 | 78 |
| wfe_open | 0 | 0 |
| wf_monitoring | 66173 | 66173 |
| wfe_monitoring | 0 | 0 |
| wf_done | 65831 | 65831 |
| wfe_done | 0 | 0 |
| wf_pending_customer_approval | 66437 | 66437 |
| wfe_pending_customer_approval | 0 | 0 |
| wf_rejected | 66579 | 66579 |
| wfe_rejected | 0 | 0 |
| wf_testing_monitoring | 66401 | 66401 |
| wfe_testing_monitoring | 0 | 0 |
| wf_in_progress | 29944 | 29944 |
| wfe_in_progress | 0 | 0 |
| wf_reopened | 64568 | 64568 |
| wfe_reopened | 0 | 0 |
| wf_to_do | 65906 | 65906 |
| wfe_to_do | 0 | 0 |
| wf_validation | 63730 | 63730 |
| wfe_validation | 0 | 0 |
| wf_resolved_under_monitoring | 64760 | 64760 |
| wfe_resolved_under_monitoring | 0 | 0 |
| wf_closed | 65096 | 65096 |
| wfe_closed | 0 | 0 |
| wf_waiting | 46987 | 46987 |
| wfe_waiting | 0 | 0 |
| wf_cancelled | 66531 | 66531 |
| wfe_cancelled | 0 | 0 |
| wf_under_review | 64870 | 64870 |
| wfe_under_review | 0 | 0 |
| wf_approved | 65061 | 65061 |
| wfe_approved | 0 | 0 |
| wf_pending_deployment | 65278 | 65278 |
| wfe_pending_deployment | 0 | 0 |
| wf_total_time | 0 | 0 |
| processing_steps | 0 | 0 |

Muestra de problemas (fila lógica CSV, id): [(12, np.int64(11938)), (115, np.int64(11527)), (208, np.int64(11786)), (220, np.int64(11831)), (380, np.int64(11621)), (430, np.int64(12038)), (447, np.int64(12023)), (601, np.int64(12076)), (663, np.int64(11895)), (922, np.int64(11563))].

## issues_change_history

Columnas obligatorias: SUPERADA.

| Indicador / validación | Registros | Estado |
|---|---:|---|
| dq_duplicate_row | 0 | SUPERADA |
| dq_invalid_id | 0 | SUPERADA |
| dq_missing_id | 0 | SUPERADA |
| dq_invalid_issueid | 0 | SUPERADA |
| dq_missing_issueid | 0 | SUPERADA |
| dq_invalid_change_group_id | 0 | SUPERADA |
| dq_missing_change_group_id | 0 | SUPERADA |
| dq_duplicate_id | 0 | SUPERADA |
| dq_invalid_created | 0 | SUPERADA |
| dq_missing_created | 0 | INFORMATIVA |
| dq_naive_created | 0 | SUPERADA |
| dq_missing_optional | 1840 | INFORMATIVA |
| dq_orphan_issue | 0 | SUPERADA |
| dq_parent_ambiguous | 0 | SUPERADA |
| dq_event_before_creation | 1 | FALLIDA |
| dq_event_after_last_change | 0 | SUPERADA |
| dq_has_problem | 1 | FALLIDA |

Recortes de espacios por columna: field=0, value=0.

| Columna original | Nulos entrada | Nulos salida |
|---|---:|---:|
| id | 0 | 0 |
| issueid | 0 | 0 |
| field | 0 | 0 |
| value | 1840 | 1840 |
| created | 0 | 0 |
| change_group_id | 0 | 0 |

Muestra de problemas (fila lógica CSV, id): [(18, np.int64(10844))].

## Trazabilidad de entradas

Originales sin cambios (SHA-256 antes/después): SUPERADA.

- `issues.csv`: `eab3b8857bc19bd917e0767fb9c30b7714d5468b25c5a1c1cd71a760e9602f02`
- `issues_change_history.csv`: `93f6d99893bac6eb755c075dc4a3c3f655cab7c6b4e2d54a3dca0b26e4b6a3c6`

## Decisiones y limitaciones

Las validaciones fallidas describen datos pendientes de revisión; no se fuerza su aprobación. `dq_has_problem` agrupa anomalías, no ausencias opcionales ni falta de histórico. Cada indicador cuenta filas y puede solaparse con otros. `dq_source_row` identifica el registro lógico original (cabecera=1).

`dq_duration_mismatch` compara wf_total_time con ended-started en segundos, tolerancia absoluta 0.000001 s, sólo con ambos valores disponibles. No comparables no significa validación superada; consultar dq_duration_comparable y los indicadores de fechas faltantes/ inválidas. Se revisan todos los wf_* para negativos. No se infieren unidades adicionales ni se calcula una duración corregida.

FEATURES.md documenta started/ended para snapshots, pero EXAMPLE.md y el CSV los contienen en issues. Las diferencias pueden obedecer a reglas de agregación desconocidas: requieren confirmación del proveedor. No se exige que resolución coincida con fin ni que un evento posterior a resolución sea inválido: puede haber reaperturas. Eventos fuera de creación/último cambio se señalan para revisión; padres duplicados impiden evaluarlos de forma inequívoca.

La clave primaria validada es id en ambos archivos; change_group_id puede repetirse legítimamente y issue_num sólo se evalúa junto al proyecto. Las colisiones proyecto/número se señalan sin reasignar claves. Los tickets sin histórico no implican un huérfano del histórico. Los negativos de wf_* no implican necesariamente ended anterior a started.

Nulos opcionales y unknown se conservan sin imputación. No se unifican categorías ni se eliminan duplicados, huérfanos o negativos. CSV no almacena tipos: al recargar usar el lector de este módulo y convertir fechas/IDs explícitamente. No se implementan SQL Server ni Power BI.
