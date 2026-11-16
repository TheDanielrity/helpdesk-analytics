# Exploración SQL Server — Fase 3.4

Ejecución UTC: 2026-11-14T05:12:09.544172+00:00. Base: HelpDeskAnalytics. Sólo SELECT/CTE; sin cambios de datos ni objetos.

Reproducción: `python -m src.explore_sql` con .env local. Consultas ejecutadas literalmente desde [03_exploratory_analysis.sql](../sql/03_exploratory_analysis.sql). En SSMS elegir HelpDeskAnalytics antes de abrir el archivo.

Todos los porcentajes se expresan de 0 a 100 con cuatro decimales. B–I y K usan el total de tickets como denominador; J usa el total de su tabla. El top 10 usa también el total global. Redondeos pueden impedir sumar exactamente 100. No se filtran anomalías ni NULL. Clasificaciones textuales usan collation binaria para mantener diferencias de mayúsculas; no se renombran ni unifican categorías.

## Comparación independiente con Pandas

Se recalcularon sobre los CSV procesados los resultados principales de Fase 2; no se usa memoria conversacional como evidencia. Se verificaron todos los grupos, porcentajes, top 10, historial y flags, además de estado/resolución.

- SUPERADA: B conteos
- SUPERADA: B porcentajes
- SUPERADA: C conteos
- SUPERADA: C porcentajes
- SUPERADA: D conteos
- SUPERADA: D porcentajes
- SUPERADA: E conteos
- SUPERADA: E porcentajes
- SUPERADA: H selección top 10
- SUPERADA: H conteos
- SUPERADA: H porcentajes
- SUPERADA: F conteos
- SUPERADA: F porcentajes
- SUPERADA: G conteos
- SUPERADA: G porcentajes
- SUPERADA: A totales
- SUPERADA: I historial
- SUPERADA: I porcentajes
- SUPERADA: J todos los flags
- SUPERADA: J reporte de Fase 2
- SUPERADA: K estado/resolución
- SUPERADA: K porcentajes
- SUPERADA: L cobertura issues.issue_created
- SUPERADA: L cobertura history.created
- SUPERADA: M procedencia issues
- SUPERADA: M procedencia issue_change_history

SHA-256 de CSV antes/después sin cambios: {'issues_clean.csv': '05a3dde8e3f276a1a8bf137890e5a662221dc0cfa0c262ba3ae82b4c7757c538', 'issues_change_history_clean.csv': 'c8186426422f7aaa74070fdaf6ab1da23f00677754615d998ff93d9693707292'}.

## Lectura de resultados y próximos indicadores

La interpretación específica de las tablas se presenta al final. Los resultados completos, incluidos todos los meses y los indicadores en cero, se conservan a continuación.

## S. ¿Qué columnas y tipos existen realmente?

**SQL:** sección `-- QUERY: S` de sql/03_exploratory_analysis.sql.

**Aprendizaje:** sys.columns y sys.types inspeccionan el catálogo; ORDER BY conserva el orden físico de columnas.

| tabla | posicion | columna | tipo | longitud_bytes | precision | escala | nullable |
|---|---|---|---|---|---|---|---|
| issue_change_history | 1 | id | bigint | 8 | 19 | 0 | False |
| issue_change_history | 2 | issueid | bigint | 8 | 19 | 0 | False |
| issue_change_history | 3 | field | nvarchar | 512 | 0 | 0 | True |
| issue_change_history | 4 | value | nvarchar | 512 | 0 | 0 | True |
| issue_change_history | 5 | created | datetimeoffset | 10 | 34 | 7 | True |
| issue_change_history | 6 | change_group_id | bigint | 8 | 19 | 0 | False |
| issue_change_history | 7 | dq_source_row | bigint | 8 | 19 | 0 | False |
| issue_change_history | 8 | dq_duplicate_row | bit | 1 | 1 | 0 | False |
| issue_change_history | 9 | id__raw | nvarchar | 512 | 0 | 0 | True |
| issue_change_history | 10 | dq_invalid_id | bit | 1 | 1 | 0 | False |
| issue_change_history | 11 | dq_missing_id | bit | 1 | 1 | 0 | False |
| issue_change_history | 12 | issueid__raw | nvarchar | 512 | 0 | 0 | True |
| issue_change_history | 13 | dq_invalid_issueid | bit | 1 | 1 | 0 | False |
| issue_change_history | 14 | dq_missing_issueid | bit | 1 | 1 | 0 | False |
| issue_change_history | 15 | change_group_id__raw | nvarchar | 512 | 0 | 0 | True |
| issue_change_history | 16 | dq_invalid_change_group_id | bit | 1 | 1 | 0 | False |
| issue_change_history | 17 | dq_missing_change_group_id | bit | 1 | 1 | 0 | False |
| issue_change_history | 18 | dq_duplicate_id | bit | 1 | 1 | 0 | False |
| issue_change_history | 19 | created__raw | nvarchar | 512 | 0 | 0 | True |
| issue_change_history | 20 | dq_invalid_created | bit | 1 | 1 | 0 | False |
| issue_change_history | 21 | dq_missing_created | bit | 1 | 1 | 0 | False |
| issue_change_history | 22 | dq_naive_created | bit | 1 | 1 | 0 | False |
| issue_change_history | 23 | dq_missing_optional | bit | 1 | 1 | 0 | False |
| issue_change_history | 24 | dq_orphan_issue | bit | 1 | 1 | 0 | False |
| issue_change_history | 25 | dq_parent_ambiguous | bit | 1 | 1 | 0 | False |
| issue_change_history | 26 | dq_event_before_creation | bit | 1 | 1 | 0 | False |
| issue_change_history | 27 | dq_event_after_last_change | bit | 1 | 1 | 0 | False |
| issue_change_history | 28 | dq_has_problem | bit | 1 | 1 | 0 | False |
| issues | 1 | id | bigint | 8 | 19 | 0 | False |
| issues | 2 | started | datetimeoffset | 10 | 34 | 7 | True |
| issues | 3 | ended | datetimeoffset | 10 | 34 | 7 | True |
| issues | 4 | issue_num | bigint | 8 | 19 | 0 | True |
| issues | 5 | issue_proj | nvarchar | 512 | 0 | 0 | True |
| issues | 6 | issue_reporter | nvarchar | 512 | 0 | 0 | True |
| issues | 7 | issue_assignee | nvarchar | 512 | 0 | 0 | True |
| issues | 8 | issue_contr_count | bigint | 8 | 19 | 0 | True |
| issues | 9 | issue_type | nvarchar | 512 | 0 | 0 | True |
| issues | 10 | issue_priority | nvarchar | 512 | 0 | 0 | True |
| issues | 11 | issue_created | datetimeoffset | 10 | 34 | 7 | True |
| issues | 12 | issue_resolution_date | datetimeoffset | 10 | 34 | 7 | True |
| issues | 13 | issue_resolution | nvarchar | 512 | 0 | 0 | True |
| issues | 14 | issue_status | nvarchar | 512 | 0 | 0 | True |
| issues | 15 | issue_comments_count | bigint | 8 | 19 | 0 | True |
| issues | 16 | last_change_date | datetimeoffset | 10 | 34 | 7 | True |
| issues | 17 | wf_in_review | decimal | 17 | 38 | 16 | True |
| issues | 18 | wfe_in_review | bigint | 8 | 19 | 0 | True |
| issues | 19 | wf_deployment | decimal | 17 | 38 | 16 | True |
| issues | 20 | wfe_deployment | bigint | 8 | 19 | 0 | True |
| issues | 21 | wf_resolved | decimal | 17 | 38 | 16 | True |
| issues | 22 | wfe_resolved | bigint | 8 | 19 | 0 | True |
| issues | 23 | wf_open | decimal | 17 | 38 | 16 | True |
| issues | 24 | wfe_open | bigint | 8 | 19 | 0 | True |
| issues | 25 | wf_monitoring | decimal | 17 | 38 | 16 | True |
| issues | 26 | wfe_monitoring | bigint | 8 | 19 | 0 | True |
| issues | 27 | wf_done | decimal | 17 | 38 | 16 | True |
| issues | 28 | wfe_done | bigint | 8 | 19 | 0 | True |
| issues | 29 | wf_pending_customer_approval | decimal | 17 | 38 | 16 | True |
| issues | 30 | wfe_pending_customer_approval | bigint | 8 | 19 | 0 | True |
| issues | 31 | wf_rejected | decimal | 17 | 38 | 16 | True |
| issues | 32 | wfe_rejected | bigint | 8 | 19 | 0 | True |
| issues | 33 | wf_testing_monitoring | decimal | 17 | 38 | 16 | True |
| issues | 34 | wfe_testing_monitoring | bigint | 8 | 19 | 0 | True |
| issues | 35 | wf_in_progress | decimal | 17 | 38 | 16 | True |
| issues | 36 | wfe_in_progress | bigint | 8 | 19 | 0 | True |
| issues | 37 | wf_reopened | decimal | 17 | 38 | 16 | True |
| issues | 38 | wfe_reopened | bigint | 8 | 19 | 0 | True |
| issues | 39 | wf_to_do | decimal | 17 | 38 | 16 | True |
| issues | 40 | wfe_to_do | bigint | 8 | 19 | 0 | True |
| issues | 41 | wf_validation | decimal | 17 | 38 | 16 | True |
| issues | 42 | wfe_validation | bigint | 8 | 19 | 0 | True |
| issues | 43 | wf_resolved_under_monitoring | decimal | 17 | 38 | 16 | True |
| issues | 44 | wfe_resolved_under_monitoring | bigint | 8 | 19 | 0 | True |
| issues | 45 | wf_closed | decimal | 17 | 38 | 16 | True |
| issues | 46 | wfe_closed | bigint | 8 | 19 | 0 | True |
| issues | 47 | wf_waiting | decimal | 17 | 38 | 16 | True |
| issues | 48 | wfe_waiting | bigint | 8 | 19 | 0 | True |
| issues | 49 | wf_cancelled | decimal | 17 | 38 | 16 | True |
| issues | 50 | wfe_cancelled | bigint | 8 | 19 | 0 | True |
| issues | 51 | wf_under_review | decimal | 17 | 38 | 16 | True |
| issues | 52 | wfe_under_review | bigint | 8 | 19 | 0 | True |
| issues | 53 | wf_approved | decimal | 17 | 38 | 16 | True |
| issues | 54 | wfe_approved | bigint | 8 | 19 | 0 | True |
| issues | 55 | wf_pending_deployment | decimal | 17 | 38 | 16 | True |
| issues | 56 | wfe_pending_deployment | bigint | 8 | 19 | 0 | True |
| issues | 57 | wf_total_time | decimal | 17 | 38 | 16 | True |
| issues | 58 | processing_steps | bigint | 8 | 19 | 0 | True |
| issues | 59 | dq_source_row | bigint | 8 | 19 | 0 | False |
| issues | 60 | dq_duplicate_row | bit | 1 | 1 | 0 | False |
| issues | 61 | id__raw | nvarchar | 512 | 0 | 0 | True |
| issues | 62 | dq_invalid_id | bit | 1 | 1 | 0 | False |
| issues | 63 | dq_missing_id | bit | 1 | 1 | 0 | False |
| issues | 64 | issue_num__raw | nvarchar | 512 | 0 | 0 | True |
| issues | 65 | dq_invalid_issue_num | bit | 1 | 1 | 0 | False |
| issues | 66 | dq_missing_issue_num | bit | 1 | 1 | 0 | False |
| issues | 67 | dq_duplicate_id | bit | 1 | 1 | 0 | False |
| issues | 68 | started__raw | nvarchar | 512 | 0 | 0 | True |
| issues | 69 | dq_invalid_started | bit | 1 | 1 | 0 | False |
| issues | 70 | dq_missing_started | bit | 1 | 1 | 0 | False |
| issues | 71 | dq_naive_started | bit | 1 | 1 | 0 | False |
| issues | 72 | ended__raw | nvarchar | 512 | 0 | 0 | True |
| issues | 73 | dq_invalid_ended | bit | 1 | 1 | 0 | False |
| issues | 74 | dq_missing_ended | bit | 1 | 1 | 0 | False |
| issues | 75 | dq_naive_ended | bit | 1 | 1 | 0 | False |
| issues | 76 | issue_created__raw | nvarchar | 512 | 0 | 0 | True |
| issues | 77 | dq_invalid_issue_created | bit | 1 | 1 | 0 | False |
| issues | 78 | dq_missing_issue_created | bit | 1 | 1 | 0 | False |
| issues | 79 | dq_naive_issue_created | bit | 1 | 1 | 0 | False |
| issues | 80 | issue_resolution_date__raw | nvarchar | 512 | 0 | 0 | True |
| issues | 81 | dq_invalid_issue_resolution_date | bit | 1 | 1 | 0 | False |
| issues | 82 | dq_missing_issue_resolution_date | bit | 1 | 1 | 0 | False |
| issues | 83 | dq_naive_issue_resolution_date | bit | 1 | 1 | 0 | False |
| issues | 84 | last_change_date__raw | nvarchar | 512 | 0 | 0 | True |
| issues | 85 | dq_invalid_last_change_date | bit | 1 | 1 | 0 | False |
| issues | 86 | dq_missing_last_change_date | bit | 1 | 1 | 0 | False |
| issues | 87 | dq_naive_last_change_date | bit | 1 | 1 | 0 | False |
| issues | 88 | issue_reporter__raw | nvarchar | 512 | 0 | 0 | True |
| issues | 89 | dq_missing_optional | bit | 1 | 1 | 0 | False |
| issues | 90 | dq_invalid_duration | bit | 1 | 1 | 0 | False |
| issues | 91 | dq_negative_workflow_duration | bit | 1 | 1 | 0 | False |
| issues | 92 | dq_negative_elapsed | bit | 1 | 1 | 0 | False |
| issues | 93 | dq_negative_duration | bit | 1 | 1 | 0 | False |
| issues | 94 | dq_duration_comparable | bit | 1 | 1 | 0 | False |
| issues | 95 | dq_duration_mismatch | bit | 1 | 1 | 0 | False |
| issues | 96 | dq_resolution_before_creation | bit | 1 | 1 | 0 | False |
| issues | 97 | dq_last_change_before_creation | bit | 1 | 1 | 0 | False |
| issues | 98 | dq_start_before_creation | bit | 1 | 1 | 0 | False |
| issues | 99 | dq_end_after_last_change | bit | 1 | 1 | 0 | False |
| issues | 100 | dq_duplicate_project_number | bit | 1 | 1 | 0 | False |
| issues | 101 | dq_no_history | bit | 1 | 1 | 0 | False |
| issues | 102 | dq_has_problem | bit | 1 | 1 | 0 | False |

**Interpretación:** Se confirmaron 102 columnas en issues y 28 en issue_change_history. Se mantienen BIGINT, DECIMAL(38,16), DATETIMEOFFSET(7), NVARCHAR(256) y BIT. Hay 8/4 columnas __raw y 36/18 dq_* respectivamente; dq_source_row es BIGINT.

**Límite:** El catálogo describe el esquema actual; los nombres no garantizan semántica de negocio.

## A. ¿Cuál es el volumen de tickets y de eventos?

**SQL:** sección `-- QUERY: A` de sql/03_exploratory_analysis.sql.

**Aprendizaje:** COUNT_BIG cuenta filas de cada tabla; UNION ALL evita multiplicarlas mediante un join.

| dataset | cantidad |
|---|---|
| tickets | 66691 |
| eventos | 257508 |

**Interpretación:** Se conservan 66,691 tickets y 257,508 eventos. Los totales coinciden con Pandas y la carga de Fase 3.3.

**Límite:** Un evento es un cambio de campo, no necesariamente una interacción, resolución o actualización única.

## B. ¿Cómo se distribuyen las prioridades?

**SQL:** sección `-- QUERY: B` de sql/03_exploratory_analysis.sql.

**Aprendizaje:** GROUP BY agrupa las etiquetas originales; la ventana SUM(COUNT_BIG(*)) OVER() calcula el denominador global.

| categoria | cantidad | porcentaje_total |
|---|---|---|
| unknown | 33965 | 50.9289 |
| Medium | 24788 | 37.1684 |
| High | 4554 | 6.8285 |
| Highest | 2084 | 3.1249 |
| Blocker | 656 | 0.9836 |
| Low | 560 | 0.8397 |
| Lowest | 84 | 0.1260 |

**Interpretación:** La prioridad más frecuente es unknown: 33,965 (50.9289%). Más de la mitad carece de una prioridad interpretable; segmentar criticidad requiere mostrar explícitamente esa falta de clasificación.

**Límite:** unknown se conserva como categoría sin asignarle nivel de severidad. La frecuencia no demuestra urgencia.

## C. ¿Qué tipos de registro predominan?

**SQL:** sección `-- QUERY: C` de sql/03_exploratory_analysis.sql.

**Aprendizaje:** Se cuentan tipos y se ordenan por frecuencia, con desempate por etiqueta.

| categoria | cantidad | porcentaje_total |
|---|---|---|
| Ticket | 45275 | 67.8877 |
| Service | 5300 | 7.9471 |
| Subtask | 4746 | 7.1164 |
| Story | 4538 | 6.8045 |
| HD Service | 1686 | 2.5281 |
| Task | 1540 | 2.3092 |
| Vacation | 856 | 1.2835 |
| Project | 842 | 1.2625 |
| Sub-task | 544 | 0.8157 |
| Epic | 403 | 0.6043 |
| Deployment | 350 | 0.5248 |
| Retrospective | 241 | 0.3614 |
| Sprint Summary | 208 | 0.3119 |
| Assistance | 109 | 0.1634 |
| Bug | 53 | 0.0795 |

**Interpretación:** Ticket representa 67.8877% del conjunto. También hay Service, Story, Vacation y tipos de planificación. Subtask y Sub-task permanecen separados: no hay documentación que permita equipararlos.

**Límite:** No todos los tipos representan incidencias de soporte; el conjunto incluye otros usos del sistema.

## D. ¿Qué estados finales registra la extracción?

**SQL:** sección `-- QUERY: D` de sql/03_exploratory_analysis.sql.

**Aprendizaje:** Se agrupa por el último estado almacenado en issues, no por las transiciones del histórico.

| categoria | cantidad | porcentaje_total |
|---|---|---|
| closed | 56344 | 84.4852 |
| done | 9714 | 14.5657 |
| waiting | 218 | 0.3269 |
| open | 97 | 0.1454 |
| in_progress | 94 | 0.1409 |
| validation | 86 | 0.1290 |
| resolved | 59 | 0.0885 |
| pending_deployment | 47 | 0.0705 |
| resolved_under_monitoring | 18 | 0.0270 |
| under_review | 5 | 0.0075 |
| to_do | 3 | 0.0045 |
| approved | 2 | 0.0030 |
| in_review | 2 | 0.0030 |
| cancelled | 1 | 0.0015 |
| reopened | 1 | 0.0015 |

**Interpretación:** closed concentra 84.4852% y done 14.5657%. Son estados finales registrados, sin evidencia suficiente para llamarlos éxito o calcular satisfacción.

**Límite:** closed/done no equivalen a resolución exitosa. No es una serie histórica de backlog.

## E. ¿Qué resoluciones se documentan?

**SQL:** sección `-- QUERY: E` de sql/03_exploratory_analysis.sql.

**Aprendizaje:** GROUP BY conserva NULL como un grupo; COUNT_BIG(*) incluye sus filas en el denominador.

| categoria | cantidad | porcentaje_total |
|---|---|---|
| Done | 62034 | 93.0170 |
| Won't Do | 2991 | 4.4849 |
| (NULL) | 853 | 1.2790 |
| Duplicate | 661 | 0.9911 |
| Cannot Reproduce | 152 | 0.2279 |

**Interpretación:** La resolución Done figura en 62,034 tickets (93.0170%). Se conservan Won't Do, Duplicate, Cannot Reproduce y 853 ausencias como resultados diferenciados.

**Límite:** NULL es ausencia de resolución registrada; por sí solo no prueba que el ticket siga abierto.

## F. ¿Cuántos tickets se crearon cada año?

**SQL:** sección `-- QUERY: F` de sql/03_exploratory_analysis.sql.

**Aprendizaje:** YEAR extrae el año de issue_created UTC; ORDER BY mantiene el orden cronológico.

| periodo | cantidad | porcentaje_total |
|---|---|---|
| 2007 | 457 | 0.6852 |
| 2008 | 1103 | 1.6539 |
| 2009 | 2157 | 3.2343 |
| 2010 | 3133 | 4.6978 |
| 2011 | 2966 | 4.4474 |
| 2012 | 3071 | 4.6048 |
| 2013 | 2442 | 3.6617 |
| 2014 | 2845 | 4.2659 |
| 2015 | 5543 | 8.3115 |
| 2016 | 7053 | 10.5756 |
| 2017 | 5524 | 8.2830 |
| 2018 | 5712 | 8.5649 |
| 2019 | 5084 | 7.6232 |
| 2020 | 5470 | 8.2020 |
| 2021 | 5834 | 8.7478 |
| 2022 | 6542 | 9.8094 |
| 2023 | 1755 | 2.6315 |

**Interpretación:** El año con más creaciones es 2016 con 7,053 (10.5756% del total). Se cubren 17 años, con extremos 2007 y 2023 parciales; no comparar 2023 como año completo.

**Límite:** Cobertura desigual y extremos parciales impiden atribuir variaciones a productividad o demanda real sin más contexto.

## G. ¿Cómo cambia la creación mes a mes?

**SQL:** sección `-- QUERY: G` de sql/03_exploratory_analysis.sql.

**Aprendizaje:** DATEFROMPARTS genera el primer día de cada año/mes; no mezcla enero de distintos años.

| periodo | cantidad | porcentaje_total |
|---|---|---|
| 2007-04-01 | 39 | 0.0585 |
| 2007-05-01 | 54 | 0.0810 |
| 2007-06-01 | 33 | 0.0495 |
| 2007-07-01 | 70 | 0.1050 |
| 2007-08-01 | 55 | 0.0825 |
| 2007-09-01 | 42 | 0.0630 |
| 2007-10-01 | 45 | 0.0675 |
| 2007-11-01 | 61 | 0.0915 |
| 2007-12-01 | 58 | 0.0870 |
| 2008-01-01 | 52 | 0.0780 |
| 2008-02-01 | 58 | 0.0870 |
| 2008-03-01 | 129 | 0.1934 |
| 2008-04-01 | 140 | 0.2099 |
| 2008-05-01 | 77 | 0.1155 |
| 2008-06-01 | 103 | 0.1544 |
| 2008-07-01 | 126 | 0.1889 |
| 2008-08-01 | 86 | 0.1290 |
| 2008-09-01 | 68 | 0.1020 |
| 2008-10-01 | 97 | 0.1454 |
| 2008-11-01 | 98 | 0.1469 |
| 2008-12-01 | 69 | 0.1035 |
| 2009-01-01 | 99 | 0.1484 |
| 2009-02-01 | 108 | 0.1619 |
| 2009-03-01 | 132 | 0.1979 |
| 2009-04-01 | 112 | 0.1679 |
| 2009-05-01 | 141 | 0.2114 |
| 2009-06-01 | 254 | 0.3809 |
| 2009-07-01 | 174 | 0.2609 |
| 2009-08-01 | 243 | 0.3644 |
| 2009-09-01 | 192 | 0.2879 |
| 2009-10-01 | 174 | 0.2609 |
| 2009-11-01 | 213 | 0.3194 |
| 2009-12-01 | 315 | 0.4723 |
| 2010-01-01 | 253 | 0.3794 |
| 2010-02-01 | 251 | 0.3764 |
| 2010-03-01 | 289 | 0.4333 |
| 2010-04-01 | 225 | 0.3374 |
| 2010-05-01 | 276 | 0.4138 |
| 2010-06-01 | 291 | 0.4363 |
| 2010-07-01 | 252 | 0.3779 |
| 2010-08-01 | 237 | 0.3554 |
| 2010-09-01 | 211 | 0.3164 |
| 2010-10-01 | 372 | 0.5578 |
| 2010-11-01 | 238 | 0.3569 |
| 2010-12-01 | 238 | 0.3569 |
| 2011-01-01 | 308 | 0.4618 |
| 2011-02-01 | 159 | 0.2384 |
| 2011-03-01 | 229 | 0.3434 |
| 2011-04-01 | 423 | 0.6343 |
| 2011-05-01 | 353 | 0.5293 |
| 2011-06-01 | 232 | 0.3479 |
| 2011-07-01 | 233 | 0.3494 |
| 2011-08-01 | 164 | 0.2459 |
| 2011-09-01 | 208 | 0.3119 |
| 2011-10-01 | 231 | 0.3464 |
| 2011-11-01 | 199 | 0.2984 |
| 2011-12-01 | 227 | 0.3404 |
| 2012-01-01 | 217 | 0.3254 |
| 2012-02-01 | 265 | 0.3974 |
| 2012-03-01 | 312 | 0.4678 |
| 2012-04-01 | 290 | 0.4348 |
| 2012-05-01 | 348 | 0.5218 |
| 2012-06-01 | 226 | 0.3389 |
| 2012-07-01 | 308 | 0.4618 |
| 2012-08-01 | 182 | 0.2729 |
| 2012-09-01 | 260 | 0.3899 |
| 2012-10-01 | 239 | 0.3584 |
| 2012-11-01 | 219 | 0.3284 |
| 2012-12-01 | 205 | 0.3074 |
| 2013-01-01 | 174 | 0.2609 |
| 2013-02-01 | 207 | 0.3104 |
| 2013-03-01 | 196 | 0.2939 |
| 2013-04-01 | 225 | 0.3374 |
| 2013-05-01 | 200 | 0.2999 |
| 2013-06-01 | 194 | 0.2909 |
| 2013-07-01 | 175 | 0.2624 |
| 2013-08-01 | 155 | 0.2324 |
| 2013-09-01 | 269 | 0.4034 |
| 2013-10-01 | 179 | 0.2684 |
| 2013-11-01 | 188 | 0.2819 |
| 2013-12-01 | 280 | 0.4198 |
| 2014-01-01 | 219 | 0.3284 |
| 2014-02-01 | 228 | 0.3419 |
| 2014-03-01 | 296 | 0.4438 |
| 2014-04-01 | 258 | 0.3869 |
| 2014-05-01 | 243 | 0.3644 |
| 2014-06-01 | 235 | 0.3524 |
| 2014-07-01 | 170 | 0.2549 |
| 2014-08-01 | 250 | 0.3749 |
| 2014-09-01 | 253 | 0.3794 |
| 2014-10-01 | 218 | 0.3269 |
| 2014-11-01 | 246 | 0.3689 |
| 2014-12-01 | 229 | 0.3434 |
| 2015-01-01 | 187 | 0.2804 |
| 2015-02-01 | 235 | 0.3524 |
| 2015-03-01 | 234 | 0.3509 |
| 2015-04-01 | 245 | 0.3674 |
| 2015-05-01 | 282 | 0.4228 |
| 2015-06-01 | 358 | 0.5368 |
| 2015-07-01 | 367 | 0.5503 |
| 2015-08-01 | 770 | 1.1546 |
| 2015-09-01 | 664 | 0.9956 |
| 2015-10-01 | 686 | 1.0286 |
| 2015-11-01 | 775 | 1.1621 |
| 2015-12-01 | 740 | 1.1096 |
| 2016-01-01 | 866 | 1.2985 |
| 2016-02-01 | 723 | 1.0841 |
| 2016-03-01 | 813 | 1.2191 |
| 2016-04-01 | 571 | 0.8562 |
| 2016-05-01 | 510 | 0.7647 |
| 2016-06-01 | 407 | 0.6103 |
| 2016-07-01 | 351 | 0.5263 |
| 2016-08-01 | 389 | 0.5833 |
| 2016-09-01 | 358 | 0.5368 |
| 2016-10-01 | 992 | 1.4875 |
| 2016-11-01 | 547 | 0.8202 |
| 2016-12-01 | 526 | 0.7887 |
| 2017-01-01 | 527 | 0.7902 |
| 2017-02-01 | 468 | 0.7017 |
| 2017-03-01 | 519 | 0.7782 |
| 2017-04-01 | 509 | 0.7632 |
| 2017-05-01 | 506 | 0.7587 |
| 2017-06-01 | 324 | 0.4858 |
| 2017-07-01 | 445 | 0.6673 |
| 2017-08-01 | 384 | 0.5758 |
| 2017-09-01 | 309 | 0.4633 |
| 2017-10-01 | 467 | 0.7002 |
| 2017-11-01 | 550 | 0.8247 |
| 2017-12-01 | 516 | 0.7737 |
| 2018-01-01 | 560 | 0.8397 |
| 2018-02-01 | 502 | 0.7527 |
| 2018-03-01 | 559 | 0.8382 |
| 2018-04-01 | 500 | 0.7497 |
| 2018-05-01 | 433 | 0.6493 |
| 2018-06-01 | 366 | 0.5488 |
| 2018-07-01 | 512 | 0.7677 |
| 2018-08-01 | 374 | 0.5608 |
| 2018-09-01 | 377 | 0.5653 |
| 2018-10-01 | 510 | 0.7647 |
| 2018-11-01 | 537 | 0.8052 |
| 2018-12-01 | 482 | 0.7227 |
| 2019-01-01 | 584 | 0.8757 |
| 2019-02-01 | 507 | 0.7602 |
| 2019-03-01 | 497 | 0.7452 |
| 2019-04-01 | 417 | 0.6253 |
| 2019-05-01 | 358 | 0.5368 |
| 2019-06-01 | 340 | 0.5098 |
| 2019-07-01 | 468 | 0.7017 |
| 2019-08-01 | 309 | 0.4633 |
| 2019-09-01 | 455 | 0.6823 |
| 2019-10-01 | 405 | 0.6073 |
| 2019-11-01 | 391 | 0.5863 |
| 2019-12-01 | 353 | 0.5293 |
| 2020-01-01 | 360 | 0.5398 |
| 2020-02-01 | 318 | 0.4768 |
| 2020-03-01 | 457 | 0.6852 |
| 2020-04-01 | 403 | 0.6043 |
| 2020-05-01 | 322 | 0.4828 |
| 2020-06-01 | 471 | 0.7062 |
| 2020-07-01 | 500 | 0.7497 |
| 2020-08-01 | 432 | 0.6478 |
| 2020-09-01 | 586 | 0.8787 |
| 2020-10-01 | 545 | 0.8172 |
| 2020-11-01 | 522 | 0.7827 |
| 2020-12-01 | 554 | 0.8307 |
| 2021-01-01 | 561 | 0.8412 |
| 2021-02-01 | 583 | 0.8742 |
| 2021-03-01 | 506 | 0.7587 |
| 2021-04-01 | 385 | 0.5773 |
| 2021-05-01 | 419 | 0.6283 |
| 2021-06-01 | 499 | 0.7482 |
| 2021-07-01 | 370 | 0.5548 |
| 2021-08-01 | 483 | 0.7242 |
| 2021-09-01 | 524 | 0.7857 |
| 2021-10-01 | 411 | 0.6163 |
| 2021-11-01 | 464 | 0.6957 |
| 2021-12-01 | 629 | 0.9432 |
| 2022-01-01 | 545 | 0.8172 |
| 2022-02-01 | 540 | 0.8097 |
| 2022-03-01 | 510 | 0.7647 |
| 2022-04-01 | 470 | 0.7047 |
| 2022-05-01 | 434 | 0.6508 |
| 2022-06-01 | 556 | 0.8337 |
| 2022-07-01 | 461 | 0.6912 |
| 2022-08-01 | 579 | 0.8682 |
| 2022-09-01 | 573 | 0.8592 |
| 2022-10-01 | 612 | 0.9177 |
| 2022-11-01 | 633 | 0.9492 |
| 2022-12-01 | 629 | 0.9432 |
| 2023-01-01 | 749 | 1.1231 |
| 2023-02-01 | 663 | 0.9941 |
| 2023-03-01 | 343 | 0.5143 |

**Interpretación:** Se observan 192 meses con registros. El máximo mensual es 2016-10-01: 992 tickets. El corte de marzo de 2023 es el día 14; la menor exposición de un mes parcial sesga las comparaciones mensuales.

**Límite:** Se muestran sólo meses con registros, sin completar ausencias con ceros. El último mes es parcial.

## H. ¿Qué diez proyectos concentran más tickets?

**SQL:** sección `-- QUERY: H` de sql/03_exploratory_analysis.sql.

**Aprendizaje:** CTE agrupa antes de TOP(10); el porcentaje usa todos los tickets, no sólo el top 10.

| proyecto | cantidad | porcentaje_total |
|---|---|---|
| t.n2 | 2213 | 3.3183 |
| C06hg2xcu | 1994 | 2.9899 |
| C13ggb_0 | 1522 | 2.2822 |
| dx8a | 1474 | 2.2102 |
| C06ggzcz0 | 1289 | 1.9328 |
| C06ggn039 | 1251 | 1.8758 |
| C01ggx0z2 | 979 | 1.4680 |
| C01ggz-3 | 942 | 1.4125 |
| db6 | 932 | 1.3975 |
| C13gg20 | 864 | 1.2955 |

**Interpretación:** t.n2 lidera con 2,213 tickets, sólo 3.3183% del total. Los diez primeros suman 13,460 (20.1826%); conviene conservar el resto de proyectos al analizar concentración.

**Límite:** Los códigos están enmascarados; un mayor volumen no demuestra peor servicio ni identifica al cliente.

## I. ¿Qué tickets tienen al menos un evento?

**SQL:** sección `-- QUERY: I` de sql/03_exploratory_analysis.sql.

**Aprendizaje:** La CTE agrupa eventos por issueid con HAVING; LEFT JOIN mantiene los tickets sin historial y evita contarlos varias veces.

| cobertura | cantidad | porcentaje_total |
|---|---|---|
| Con historial | 66650 | 99.9385 |
| Sin historial | 41 | 0.0615 |

**Interpretación:** 66,650 tickets tienen historial y 41 no lo tienen (0.0615%). La cobertura de historia es alta pero comienza años después de las primeras creaciones; tener algún evento no garantiza historia completa.

**Límite:** Sin historial no significa sin trabajo; puede ser una limitación de extracción/cobertura.

## J. ¿Qué advertencias y ausencias afectan al análisis?

**SQL:** sección `-- QUERY: J` de sql/03_exploratory_analysis.sql.

**Aprendizaje:** CROSS APPLY VALUES convierte los flags en filas; SUM cuenta True y COUNT_BIG es el total de la tabla correspondiente.

| tabla | indicador | filas_true | total_tabla | porcentaje_tabla |
|---|---|---|---|---|
| issue_change_history | dq_missing_optional | 1840 | 257508 | 0.7145 |
| issue_change_history | dq_event_before_creation | 1 | 257508 | 0.0004 |
| issue_change_history | dq_has_problem | 1 | 257508 | 0.0004 |
| issue_change_history | dq_duplicate_id | 0 | 257508 | 0.0000 |
| issue_change_history | dq_duplicate_row | 0 | 257508 | 0.0000 |
| issue_change_history | dq_event_after_last_change | 0 | 257508 | 0.0000 |
| issue_change_history | dq_invalid_change_group_id | 0 | 257508 | 0.0000 |
| issue_change_history | dq_invalid_created | 0 | 257508 | 0.0000 |
| issue_change_history | dq_invalid_id | 0 | 257508 | 0.0000 |
| issue_change_history | dq_invalid_issueid | 0 | 257508 | 0.0000 |
| issue_change_history | dq_missing_change_group_id | 0 | 257508 | 0.0000 |
| issue_change_history | dq_missing_created | 0 | 257508 | 0.0000 |
| issue_change_history | dq_missing_id | 0 | 257508 | 0.0000 |
| issue_change_history | dq_missing_issueid | 0 | 257508 | 0.0000 |
| issue_change_history | dq_naive_created | 0 | 257508 | 0.0000 |
| issue_change_history | dq_orphan_issue | 0 | 257508 | 0.0000 |
| issue_change_history | dq_parent_ambiguous | 0 | 257508 | 0.0000 |
| issues | dq_duration_comparable | 66691 | 66691 | 100.0000 |
| issues | dq_missing_optional | 66691 | 66691 | 100.0000 |
| issues | dq_missing_issue_resolution_date | 853 | 66691 | 1.2790 |
| issues | dq_has_problem | 450 | 66691 | 0.6748 |
| issues | dq_duration_mismatch | 374 | 66691 | 0.5608 |
| issues | dq_duplicate_project_number | 65 | 66691 | 0.0975 |
| issues | dq_negative_duration | 55 | 66691 | 0.0825 |
| issues | dq_negative_workflow_duration | 55 | 66691 | 0.0825 |
| issues | dq_no_history | 41 | 66691 | 0.0615 |
| issues | dq_end_after_last_change | 9 | 66691 | 0.0135 |
| issues | dq_missing_last_change_date | 1 | 66691 | 0.0015 |
| issues | dq_duplicate_id | 0 | 66691 | 0.0000 |
| issues | dq_duplicate_row | 0 | 66691 | 0.0000 |
| issues | dq_invalid_duration | 0 | 66691 | 0.0000 |
| issues | dq_invalid_ended | 0 | 66691 | 0.0000 |
| issues | dq_invalid_id | 0 | 66691 | 0.0000 |
| issues | dq_invalid_issue_created | 0 | 66691 | 0.0000 |
| issues | dq_invalid_issue_num | 0 | 66691 | 0.0000 |
| issues | dq_invalid_issue_resolution_date | 0 | 66691 | 0.0000 |
| issues | dq_invalid_last_change_date | 0 | 66691 | 0.0000 |
| issues | dq_invalid_started | 0 | 66691 | 0.0000 |
| issues | dq_last_change_before_creation | 0 | 66691 | 0.0000 |
| issues | dq_missing_ended | 0 | 66691 | 0.0000 |
| issues | dq_missing_id | 0 | 66691 | 0.0000 |
| issues | dq_missing_issue_created | 0 | 66691 | 0.0000 |
| issues | dq_missing_issue_num | 0 | 66691 | 0.0000 |
| issues | dq_missing_started | 0 | 66691 | 0.0000 |
| issues | dq_naive_ended | 0 | 66691 | 0.0000 |
| issues | dq_naive_issue_created | 0 | 66691 | 0.0000 |
| issues | dq_naive_issue_resolution_date | 0 | 66691 | 0.0000 |
| issues | dq_naive_last_change_date | 0 | 66691 | 0.0000 |
| issues | dq_naive_started | 0 | 66691 | 0.0000 |
| issues | dq_negative_elapsed | 0 | 66691 | 0.0000 |
| issues | dq_resolution_before_creation | 0 | 66691 | 0.0000 |
| issues | dq_start_before_creation | 0 | 66691 | 0.0000 |

**Interpretación:** Hay 450 tickets señalados y 1 evento señalado. Se preservan 55 tickets con wf_* negativos, 374 discrepancias, 65 filas con colisión proyecto/número y 9 fines posteriores al último cambio. dq_missing_optional=True en todos los tickets refleja campos legítimamente vacíos; no significa que todos sean incorrectos. dq_duration_comparable=True en todos significa que se pudieron comparar, no que los tiempos concuerden.

**Límite:** Los indicadores se solapan; no deben sumarse como tickets únicos. missing_optional, no_history y duration_comparable son informativos. dq_source_row es procedencia, no un flag.

## K. ¿Coinciden estado y resolución?

**SQL:** sección `-- QUERY: K` de sql/03_exploratory_analysis.sql.

**Aprendizaje:** Agrupación conjunta para contrastar el estado final con la resolución informada.

| estado | resolucion | cantidad | porcentaje_total |
|---|---|---|---|
| closed | Done | 53358 | 80.0078 |
| done | Done | 8676 | 13.0093 |
| closed | Won't Do | 1982 | 2.9719 |
| done | Won't Do | 1009 | 1.5129 |
| closed | Duplicate | 660 | 0.9896 |
| waiting | (NULL) | 218 | 0.3269 |
| closed | (NULL) | 192 | 0.2879 |
| closed | Cannot Reproduce | 152 | 0.2279 |
| open | (NULL) | 97 | 0.1454 |
| in_progress | (NULL) | 94 | 0.1409 |
| validation | (NULL) | 86 | 0.1290 |
| resolved | (NULL) | 59 | 0.0885 |
| pending_deployment | (NULL) | 47 | 0.0705 |
| done | (NULL) | 28 | 0.0420 |
| resolved_under_monitoring | (NULL) | 18 | 0.0270 |
| under_review | (NULL) | 5 | 0.0075 |
| to_do | (NULL) | 3 | 0.0045 |
| approved | (NULL) | 2 | 0.0030 |
| in_review | (NULL) | 2 | 0.0030 |
| cancelled | (NULL) | 1 | 0.0015 |
| done | Duplicate | 1 | 0.0015 |
| reopened | (NULL) | 1 | 0.0015 |

**Interpretación:** Existen 220 tickets closed/done con resolución NULL, además de cierres Won't Do, Duplicate y Cannot Reproduce. El cruce demuestra que estado y resolución no son intercambiables.

**Límite:** La etiqueta Done sigue siendo una clasificación del origen; éxito percibido y satisfacción requieren evidencia adicional.

## L. ¿Cuál es la cobertura temporal efectiva y cuánto queda fuera de la documentada?

**SQL:** sección `-- QUERY: L` de sql/03_exploratory_analysis.sql.

**Aprendizaje:** MIN/MAX obtienen extremos y SUM(CASE WHEN...) cuenta antes de 2016 y desde abril de 2023.

| campo | minimo_utc | maximo_utc | antes_2016 | desde_abril_2023 | fechas_null |
|---|---|---|---|---|---|
| issues.issue_created | 2007-04-15T08:12:11Z | 2023-03-14T14:00:32Z | 23717 | 0 | 0 |
| history.created | 2015-08-12T11:14:28Z | 2023-03-14T14:19:32Z | 4015 | 0 | 0 |

**Interpretación:** 23,717 tickets (35.5625%) se crearon antes de 2016. La historia empieza el 12 de agosto de 2015; no hay filas desde abril de 2023 ni fechas nulas en los dos campos revisados. La cobertura documentada no describe todo el CSV; no se conoce la causa y no se excluyen filas.

**Límite:** FEATURES.md describe enero de 2016 a marzo de 2023 para issues. No se excluyen registros anteriores ni se atribuye una causa sin evidencia.

## M. ¿Qué rango tienen los números de procedencia?

**SQL:** sección `-- QUERY: M` de sql/03_exploratory_analysis.sql.

**Aprendizaje:** MIN/MAX y COUNT_BIG(DISTINCT) resumen dq_source_row por tabla.

| tabla | fila_min | fila_max | filas_distintas |
|---|---|---|---|
| issues | 2 | 66692 | 66691 |
| issue_change_history | 2 | 257509 | 257508 |

**Interpretación:** Los números de procedencia son distintos por registro y van de 2 a N+1, coherentes con la cabecera en fila 1. No se mezclan con las tasas de calidad.

**Límite:** La fila de origen es trazabilidad de CSV, no fecha ni indicador binario de calidad.

## Indicadores recomendados para la siguiente fase

1. Volumen de creaciones por mes UTC, tipo, proyecto y prioridad; comparar meses completos y explicitar el corte temporal. Crear después un calendario para distinguir meses sin registros de ceros confirmados.
2. Porcentaje unknown sobre todos los tickets (50,9289%) y distribución de prioridades conocidas con su denominador declarado. Mostrar ambos; no reclasificar unknown como Low.
3. Distribución de resoluciones registradas y cruce estado/resolución; mostrar NULL separado. Una tasa de resolución exige acordar estados y fechas elegibles; no llamar éxito al porcentaje closed/done.
4. Cobertura de histórico: tickets con al menos un evento / tickets. Desglosar por cohorte de creación por la diferencia entre 2007 y el inicio de eventos en 2015.
5. Calidad: negativos, discrepancias y ausencia de resolución, cada uno con su denominador; usar dq_has_problem para registros únicos con anomalías, no sumar flags. Ausencias opcionales legítimas se presentan como completitud, no errores.
6. Concentración por proyecto: participación del top 10 sobre todos los tickets y resto explícito; segmentar por tipo antes de comparaciones operativas.
7. Posteriormente, mediana y percentil 90 de tiempo transcurrido/calendario en segundos u horas, con cohortes, fechas válidas y tratamiento explícito de negativos/discrepancias. Comparar métricas con y sin flags, manteniendo registros. No asumir horas laborales, SLA, tiempo de primera respuesta ni productividad: requieren reglas, horarios y fuentes adicionales.

## Conceptos SQL para practicar

Aprender en este orden: COUNT_BIG(*) y GROUP BY; NULL frente a COUNT(columna); agregaciones condicionales con CASE; porcentajes con SUM(...) OVER() y NULLIF; fechas por año/mes; CTE; LEFT JOIN tras agrupar el lado de eventos para evitar multiplicación; WHERE para filtrar filas y HAVING para filtrar grupos; TOP con ORDER BY y desempate; CROSS APPLY VALUES para resumir indicadores. Revisar siempre granularidad y denominador antes de interpretar una tasa.

## Límites generales

Resultados descriptivos de una extracción histórica, no del HelpDesk actual. No hay calendario laboral, objetivo SLA ni evidencia de satisfacción. No se reconstruyó backlog diario ni reaperturas. No se crearon vistas, tablas o elementos de Power BI. Las consultas se ejecutaron secuencialmente sin aislamiento snapshot: si hubiera escrituras concurrentes, repetir sobre una copia estable; las comparaciones con CSV pasaron en esta ejecución.
