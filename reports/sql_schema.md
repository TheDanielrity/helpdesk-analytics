# Diseño SQL Server — Fase 3.1

Perfil exhaustivo de los CSV procesados. No se han importado filas ni ejecutado los scripts DDL.

CSV no tiene tipos físicos; los tipos siguientes son tipos lógicos verificados sobre todos los valores no vacíos, sin inferencia float. Longitud en unidades UTF-16. La nulabilidad es el contrato de carga; se permiten nulos de campos opcionales aunque hoy no existan.

## stg.issues

Fuente: `issues_clean.csv`; 66691 registros; 102 columnas; SHA-256 `05a3dde8e3f276a1a8bf137890e5a662221dc0cfa0c262ba3ae82b4c7757c538`.

| Columna real | Tipo SQL validado | Nullable | Nulos | Longitud máxima | Escala observada |
|---|---|---|---:|---:|---:|
| id | BIGINT | no | 0 | 8 | 0 |
| started | DATETIMEOFFSET(7) | sí | 0 | 32 | — |
| ended | DATETIMEOFFSET(7) | sí | 0 | 32 | — |
| issue_num | BIGINT | sí | 0 | 4 | 0 |
| issue_proj | NVARCHAR(256) | sí | 0 | 21 | — |
| issue_reporter | NVARCHAR(256) | sí | 0 | 14 | — |
| issue_assignee | NVARCHAR(256) | sí | 31047 | 17 | — |
| issue_contr_count | BIGINT | sí | 0 | 4 | 1 |
| issue_type | NVARCHAR(256) | sí | 0 | 14 | — |
| issue_priority | NVARCHAR(256) | sí | 0 | 7 | — |
| issue_created | DATETIMEOFFSET(7) | sí | 0 | 32 | — |
| issue_resolution_date | DATETIMEOFFSET(7) | sí | 853 | 32 | — |
| issue_resolution | NVARCHAR(256) | sí | 853 | 16 | — |
| issue_status | NVARCHAR(256) | sí | 0 | 25 | — |
| issue_comments_count | BIGINT | sí | 0 | 3 | 0 |
| last_change_date | DATETIMEOFFSET(7) | sí | 1 | 32 | — |
| wf_in_review | DECIMAL(38,16) | sí | 66614 | 9 | 1 |
| wfe_in_review | BIGINT | sí | 0 | 1 | 0 |
| wf_deployment | DECIMAL(38,16) | sí | 66556 | 12 | 3 |
| wfe_deployment | BIGINT | sí | 0 | 1 | 0 |
| wf_resolved | DECIMAL(38,16) | sí | 38546 | 18 | 16 |
| wfe_resolved | BIGINT | sí | 0 | 1 | 0 |
| wf_open | DECIMAL(38,16) | sí | 78 | 18 | 15 |
| wfe_open | BIGINT | sí | 0 | 1 | 0 |
| wf_monitoring | DECIMAL(38,16) | sí | 66173 | 17 | 15 |
| wfe_monitoring | BIGINT | sí | 0 | 1 | 0 |
| wf_done | DECIMAL(38,16) | sí | 65831 | 18 | 10 |
| wfe_done | BIGINT | sí | 0 | 1 | 0 |
| wf_pending_customer_approval | DECIMAL(38,16) | sí | 66437 | 18 | 16 |
| wfe_pending_customer_approval | BIGINT | sí | 0 | 1 | 0 |
| wf_rejected | DECIMAL(38,16) | sí | 66579 | 18 | 16 |
| wfe_rejected | BIGINT | sí | 0 | 1 | 0 |
| wf_testing_monitoring | DECIMAL(38,16) | sí | 66401 | 10 | 1 |
| wfe_testing_monitoring | BIGINT | sí | 0 | 1 | 0 |
| wf_in_progress | DECIMAL(38,16) | sí | 29944 | 18 | 16 |
| wfe_in_progress | BIGINT | sí | 0 | 2 | 0 |
| wf_reopened | DECIMAL(38,16) | sí | 64568 | 18 | 16 |
| wfe_reopened | BIGINT | sí | 0 | 2 | 0 |
| wf_to_do | DECIMAL(38,16) | sí | 65906 | 18 | 16 |
| wfe_to_do | BIGINT | sí | 0 | 1 | 0 |
| wf_validation | DECIMAL(38,16) | sí | 63730 | 18 | 16 |
| wfe_validation | BIGINT | sí | 0 | 2 | 0 |
| wf_resolved_under_monitoring | DECIMAL(38,16) | sí | 64760 | 18 | 16 |
| wfe_resolved_under_monitoring | BIGINT | sí | 0 | 1 | 0 |
| wf_closed | DECIMAL(38,16) | sí | 65096 | 18 | 16 |
| wfe_closed | BIGINT | sí | 0 | 2 | 0 |
| wf_waiting | DECIMAL(38,16) | sí | 46987 | 18 | 14 |
| wfe_waiting | BIGINT | sí | 0 | 2 | 0 |
| wf_cancelled | DECIMAL(38,16) | sí | 66531 | 18 | 16 |
| wfe_cancelled | BIGINT | sí | 0 | 1 | 0 |
| wf_under_review | DECIMAL(38,16) | sí | 64870 | 18 | 16 |
| wfe_under_review | BIGINT | sí | 0 | 1 | 0 |
| wf_approved | DECIMAL(38,16) | sí | 65061 | 18 | 16 |
| wfe_approved | BIGINT | sí | 0 | 1 | 0 |
| wf_pending_deployment | DECIMAL(38,16) | sí | 65278 | 18 | 16 |
| wfe_pending_deployment | BIGINT | sí | 0 | 2 | 0 |
| wf_total_time | DECIMAL(38,16) | sí | 0 | 18 | 15 |
| processing_steps | BIGINT | sí | 0 | 2 | 0 |
| dq_source_row | BIGINT | no | 0 | 5 | 0 |
| dq_duplicate_row | BIT | no | 0 | 5 | — |
| id__raw | NVARCHAR(256) | sí | 0 | 10 | — |
| dq_invalid_id | BIT | no | 0 | 5 | — |
| dq_missing_id | BIT | no | 0 | 5 | — |
| issue_num__raw | NVARCHAR(256) | sí | 0 | 6 | — |
| dq_invalid_issue_num | BIT | no | 0 | 5 | — |
| dq_missing_issue_num | BIT | no | 0 | 5 | — |
| dq_duplicate_id | BIT | no | 0 | 5 | — |
| started__raw | NVARCHAR(256) | sí | 0 | 32 | — |
| dq_invalid_started | BIT | no | 0 | 5 | — |
| dq_missing_started | BIT | no | 0 | 5 | — |
| dq_naive_started | BIT | no | 0 | 5 | — |
| ended__raw | NVARCHAR(256) | sí | 0 | 32 | — |
| dq_invalid_ended | BIT | no | 0 | 5 | — |
| dq_missing_ended | BIT | no | 0 | 5 | — |
| dq_naive_ended | BIT | no | 0 | 5 | — |
| issue_created__raw | NVARCHAR(256) | sí | 0 | 32 | — |
| dq_invalid_issue_created | BIT | no | 0 | 5 | — |
| dq_missing_issue_created | BIT | no | 0 | 5 | — |
| dq_naive_issue_created | BIT | no | 0 | 5 | — |
| issue_resolution_date__raw | NVARCHAR(256) | sí | 853 | 32 | — |
| dq_invalid_issue_resolution_date | BIT | no | 0 | 5 | — |
| dq_missing_issue_resolution_date | BIT | no | 0 | 5 | — |
| dq_naive_issue_resolution_date | BIT | no | 0 | 5 | — |
| last_change_date__raw | NVARCHAR(256) | sí | 1 | 32 | — |
| dq_invalid_last_change_date | BIT | no | 0 | 5 | — |
| dq_missing_last_change_date | BIT | no | 0 | 5 | — |
| dq_naive_last_change_date | BIT | no | 0 | 5 | — |
| issue_reporter__raw | NVARCHAR(256) | sí | 0 | 14 | — |
| dq_missing_optional | BIT | no | 0 | 4 | — |
| dq_invalid_duration | BIT | no | 0 | 5 | — |
| dq_negative_workflow_duration | BIT | no | 0 | 5 | — |
| dq_negative_elapsed | BIT | no | 0 | 5 | — |
| dq_negative_duration | BIT | no | 0 | 5 | — |
| dq_duration_comparable | BIT | no | 0 | 4 | — |
| dq_duration_mismatch | BIT | no | 0 | 5 | — |
| dq_resolution_before_creation | BIT | no | 0 | 5 | — |
| dq_last_change_before_creation | BIT | no | 0 | 5 | — |
| dq_start_before_creation | BIT | no | 0 | 5 | — |
| dq_end_after_last_change | BIT | no | 0 | 5 | — |
| dq_duplicate_project_number | BIT | no | 0 | 5 | — |
| dq_no_history | BIT | no | 0 | 5 | — |
| dq_has_problem | BIT | no | 0 | 5 | — |
## stg.issue_change_history

Fuente: `issues_change_history_clean.csv`; 257508 registros; 28 columnas; SHA-256 `c8186426422f7aaa74070fdaf6ab1da23f00677754615d998ff93d9693707292`.

| Columna real | Tipo SQL validado | Nullable | Nulos | Longitud máxima | Escala observada |
|---|---|---|---:|---:|---:|
| id | BIGINT | no | 0 | 7 | 0 |
| issueid | BIGINT | no | 0 | 8 | 0 |
| field | NVARCHAR(256) | sí | 0 | 8 | — |
| value | NVARCHAR(256) | sí | 1840 | 25 | — |
| created | DATETIMEOFFSET(7) | sí | 0 | 32 | — |
| change_group_id | BIGINT | no | 0 | 7 | 0 |
| dq_source_row | BIGINT | no | 0 | 6 | 0 |
| dq_duplicate_row | BIT | no | 0 | 5 | — |
| id__raw | NVARCHAR(256) | sí | 0 | 9 | — |
| dq_invalid_id | BIT | no | 0 | 5 | — |
| dq_missing_id | BIT | no | 0 | 5 | — |
| issueid__raw | NVARCHAR(256) | sí | 0 | 10 | — |
| dq_invalid_issueid | BIT | no | 0 | 5 | — |
| dq_missing_issueid | BIT | no | 0 | 5 | — |
| change_group_id__raw | NVARCHAR(256) | sí | 0 | 9 | — |
| dq_invalid_change_group_id | BIT | no | 0 | 5 | — |
| dq_missing_change_group_id | BIT | no | 0 | 5 | — |
| dq_duplicate_id | BIT | no | 0 | 5 | — |
| created__raw | NVARCHAR(256) | sí | 0 | 32 | — |
| dq_invalid_created | BIT | no | 0 | 5 | — |
| dq_missing_created | BIT | no | 0 | 5 | — |
| dq_naive_created | BIT | no | 0 | 5 | — |
| dq_missing_optional | BIT | no | 0 | 5 | — |
| dq_orphan_issue | BIT | no | 0 | 5 | — |
| dq_parent_ambiguous | BIT | no | 0 | 5 | — |
| dq_event_before_creation | BIT | no | 0 | 5 | — |
| dq_event_after_last_change | BIT | no | 0 | 5 | — |
| dq_has_problem | BIT | no | 0 | 5 | — |

## Contrato y decisiones

Claves id no nulas y únicas en ambas fuentes; todos los issueid existen en issues.id. Relación 1:N, FK sin cascadas. Cargar primero tickets. No hay UNIQUE sobre proyecto/issue_num (65 filas con colisiones), ni sobre change_group_id (agrupa cambios).

BIGINT: identificadores validados, contadores integrales y fila de procedencia. DECIMAL(38,16): todos los wf_* en segundos, incluidos negativos y artefactos decimales existentes; hasta 16 decimales observados, 22 posiciones enteras disponibles. Nunca FLOAT ni redondeos para estos datos.

DATETIMEOFFSET(7): conserva zona UTC y admite 100 ns; todos los valores actuales caben sin pérdida. NVARCHAR(256): códigos, categorías y __raw, longitud UTF-16 verificada; margen explícito para futuras entradas. BIT: todos los indicadores booleanos; dq_source_row es BIGINT. No se añaden valores por defecto.

PK clustered por id en cada tabla y un solo índice adicional (issueid, created) para joins y línea temporal. Los filtros de fecha/prioridad/proyecto se evaluarán con planes reales antes de añadir índices. Ningún índice sobre flags aislados o texto de auditoría.

No se imponen CHECK temporales ni de duración positiva: impedirían conservar anomalías válidamente señaladas. Las columnas opcionales son NULL y unknown permanece texto. El staging tipado representa la entrega validada actual: futuras claves inválidas, huérfanas o duplicadas requieren cuarentena separada, sin borrar registros ni desactivar restricciones para forzar una carga.

Los __raw presentes se conservan íntegramente; no se inventan columnas __raw ausentes del CSV. DECIMAL conserva valor numérico, no formato textual (.0, notación científica); el CSV inmutable y su hash conservan esa representación. Al importar se convertirán vacíos a None, booleanos explícitamente a 0/1 y números con Decimal, nunca con float. Las fechas se enviarán en ISO8601 con offset explícito para evitar pérdida de zona por ODBC.

Ejecución repetida: CREATE DATABASE y CREATE TABLE sólo si faltan; no migra ni verifica tablas preexistentes. Antes de reutilizar una base existente comparar sys.columns, sys.types, sys.key_constraints, sys.foreign_keys y sys.indexes con este contrato. Un error de índices/tabla revierte la transacción por XACT_ABORT. No ejecutar dentro de otra transacción.

Referencias: [datetimeoffset](https://learn.microsoft.com/en-us/sql/t-sql/data-types/datetimeoffset-transact-sql), [decimal](https://learn.microsoft.com/en-us/sql/t-sql/data-types/decimal-and-numeric-transact-sql).
