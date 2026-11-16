# Importación SQL Server — Fase 3.3

Fecha UTC: 2026-11-14T04:11:18.935036+00:00

Estado: **COMMIT CONFIRMADO**. Duración total: 82.125 s.

Datos originales/procesados leídos sin modificaciones. No se imprimen credenciales.

SQL Server: 17.0.1000.7. Base existente antes: False.

DDL: 01_create_database.sql ejecutado (base ausente); 02_create_tables.sql ejecutado (tablas ausentes).

## Conversión y transacciones

Pandas string con sólo campos vacíos como ausencias → None/SQL NULL. BIGINT exacto y BIT True/False→1/0. NVARCHAR conserva texto, unknown y __raw sin strip. DECIMAL se valida con Decimal (contexto de 50 dígitos), sin float ni redondeo, y se transporta como Unicode de 16 decimales con CONVERT(DECIMAL(38,16), ?). Fechas UTC canónicas de 7 decimales se transportan como Unicode con CONVERT(DATETIMEOFFSET(7), ?); lectura explícita como ISO evita pérdida del offset en ODBC.

Inserciones parametrizadas, setinputsizes explícitos y lotes acotados. Primero tickets, luego eventos. Prueba representativa con filas reales y ROLLBACK; después carga completa con BEGIN TRANSACTION y bloqueos TABLOCKX/HOLDLOCK sobre ambas tablas vacías. Ante error previo al COMMIT: ROLLBACK completo. Se compara cada celda, NULL, flag y negativo y el reporte de Fase 2 antes de confirmar. Se comprueban PK, FK confiable e índice en el catálogo.

## Ejecución

```json
{
  "started": "2026-11-14T04:11:18.935036+00:00",
  "status": "COMMIT CONFIRMADO",
  "batch_size": 1000,
  "fast_executemany": true,
  "pyodbc": "5.5.0",
  "preparation": {
    "version": "17.0.1000.7",
    "before": {
      "issues": null,
      "issue_change_history": null
    },
    "database_existed": false,
    "ddl": [
      "01_create_database.sql ejecutado (base ausente)",
      "02_create_tables.sql ejecutado (tablas ausentes)"
    ]
  },
  "odbc_driver": "msodbcsql18.dll",
  "odbc_version": "18.07.0001",
  "pilot": {
    "rows": {
      "issues": 88,
      "issue_change_history": 5
    },
    "result": "EXACTO; ROLLBACK",
    "seconds": 0.137
  },
  "insert_seconds": 30.587,
  "validation_seconds": 37.618,
  "load_seconds": 68.206,
  "persisted_counts": {
    "issues": 66691,
    "issue_change_history": 257508
  },
  "seconds": 82.12456620000012
}
```

## Conteos e integridad

| Tabla | Antes | Después | IDs duplicados | Celdas exactas |
|---|---:|---:|---:|---:|
| stg.issues | 0 | 66691 | 0 | 6802482 |
| stg.issue_change_history | 0 | 257508 | 0 | 7210224 |

Huérfanos: 0. Conteos NULL/indicadores coinciden con CSV y reports/data_quality.md. Todas las celdas fueron verificadas, incluyendo las muestras de precisión, UTC, negativos y auditoría.

## issues: NULL, calidad y negativos

| Columna | NULL conservados | True conservados | Negativos conservados |
|---|---:|---:|---:|
| id | 0 | — | — |
| started | 0 | — | — |
| ended | 0 | — | — |
| issue_num | 0 | — | — |
| issue_proj | 0 | — | — |
| issue_reporter | 0 | — | — |
| issue_assignee | 31047 | — | — |
| issue_contr_count | 0 | — | — |
| issue_type | 0 | — | — |
| issue_priority | 0 | — | — |
| issue_created | 0 | — | — |
| issue_resolution_date | 853 | — | — |
| issue_resolution | 853 | — | — |
| issue_status | 0 | — | — |
| issue_comments_count | 0 | — | — |
| last_change_date | 1 | — | — |
| wf_in_review | 66614 | — | 0 |
| wfe_in_review | 0 | — | — |
| wf_deployment | 66556 | — | 0 |
| wfe_deployment | 0 | — | — |
| wf_resolved | 38546 | — | 0 |
| wfe_resolved | 0 | — | — |
| wf_open | 78 | — | 0 |
| wfe_open | 0 | — | — |
| wf_monitoring | 66173 | — | 0 |
| wfe_monitoring | 0 | — | — |
| wf_done | 65831 | — | 47 |
| wfe_done | 0 | — | — |
| wf_pending_customer_approval | 66437 | — | 0 |
| wfe_pending_customer_approval | 0 | — | — |
| wf_rejected | 66579 | — | 0 |
| wfe_rejected | 0 | — | — |
| wf_testing_monitoring | 66401 | — | 0 |
| wfe_testing_monitoring | 0 | — | — |
| wf_in_progress | 29944 | — | 2 |
| wfe_in_progress | 0 | — | — |
| wf_reopened | 64568 | — | 0 |
| wfe_reopened | 0 | — | — |
| wf_to_do | 65906 | — | 5 |
| wfe_to_do | 0 | — | — |
| wf_validation | 63730 | — | 0 |
| wfe_validation | 0 | — | — |
| wf_resolved_under_monitoring | 64760 | — | 0 |
| wfe_resolved_under_monitoring | 0 | — | — |
| wf_closed | 65096 | — | 0 |
| wfe_closed | 0 | — | — |
| wf_waiting | 46987 | — | 0 |
| wfe_waiting | 0 | — | — |
| wf_cancelled | 66531 | — | 0 |
| wfe_cancelled | 0 | — | — |
| wf_under_review | 64870 | — | 1 |
| wfe_under_review | 0 | — | — |
| wf_approved | 65061 | — | 0 |
| wfe_approved | 0 | — | — |
| wf_pending_deployment | 65278 | — | 0 |
| wfe_pending_deployment | 0 | — | — |
| wf_total_time | 0 | — | 0 |
| processing_steps | 0 | — | — |
| dq_source_row | 0 | — | — |
| dq_duplicate_row | 0 | 0 | — |
| id__raw | 0 | — | — |
| dq_invalid_id | 0 | 0 | — |
| dq_missing_id | 0 | 0 | — |
| issue_num__raw | 0 | — | — |
| dq_invalid_issue_num | 0 | 0 | — |
| dq_missing_issue_num | 0 | 0 | — |
| dq_duplicate_id | 0 | 0 | — |
| started__raw | 0 | — | — |
| dq_invalid_started | 0 | 0 | — |
| dq_missing_started | 0 | 0 | — |
| dq_naive_started | 0 | 0 | — |
| ended__raw | 0 | — | — |
| dq_invalid_ended | 0 | 0 | — |
| dq_missing_ended | 0 | 0 | — |
| dq_naive_ended | 0 | 0 | — |
| issue_created__raw | 0 | — | — |
| dq_invalid_issue_created | 0 | 0 | — |
| dq_missing_issue_created | 0 | 0 | — |
| dq_naive_issue_created | 0 | 0 | — |
| issue_resolution_date__raw | 853 | — | — |
| dq_invalid_issue_resolution_date | 0 | 0 | — |
| dq_missing_issue_resolution_date | 0 | 853 | — |
| dq_naive_issue_resolution_date | 0 | 0 | — |
| last_change_date__raw | 1 | — | — |
| dq_invalid_last_change_date | 0 | 0 | — |
| dq_missing_last_change_date | 0 | 1 | — |
| dq_naive_last_change_date | 0 | 0 | — |
| issue_reporter__raw | 0 | — | — |
| dq_missing_optional | 0 | 66691 | — |
| dq_invalid_duration | 0 | 0 | — |
| dq_negative_workflow_duration | 0 | 55 | — |
| dq_negative_elapsed | 0 | 0 | — |
| dq_negative_duration | 0 | 55 | — |
| dq_duration_comparable | 0 | 66691 | — |
| dq_duration_mismatch | 0 | 374 | — |
| dq_resolution_before_creation | 0 | 0 | — |
| dq_last_change_before_creation | 0 | 0 | — |
| dq_start_before_creation | 0 | 0 | — |
| dq_end_after_last_change | 0 | 9 | — |
| dq_duplicate_project_number | 0 | 65 | — |
| dq_no_history | 0 | 41 | — |
| dq_has_problem | 0 | 450 | — |

## issue_change_history: NULL, calidad y negativos

| Columna | NULL conservados | True conservados | Negativos conservados |
|---|---:|---:|---:|
| id | 0 | — | — |
| issueid | 0 | — | — |
| field | 0 | — | — |
| value | 1840 | — | — |
| created | 0 | — | — |
| change_group_id | 0 | — | — |
| dq_source_row | 0 | — | — |
| dq_duplicate_row | 0 | 0 | — |
| id__raw | 0 | — | — |
| dq_invalid_id | 0 | 0 | — |
| dq_missing_id | 0 | 0 | — |
| issueid__raw | 0 | — | — |
| dq_invalid_issueid | 0 | 0 | — |
| dq_missing_issueid | 0 | 0 | — |
| change_group_id__raw | 0 | — | — |
| dq_invalid_change_group_id | 0 | 0 | — |
| dq_missing_change_group_id | 0 | 0 | — |
| dq_duplicate_id | 0 | 0 | — |
| created__raw | 0 | — | — |
| dq_invalid_created | 0 | 0 | — |
| dq_missing_created | 0 | 0 | — |
| dq_naive_created | 0 | 0 | — |
| dq_missing_optional | 0 | 1840 | — |
| dq_orphan_issue | 0 | 0 | — |
| dq_parent_ambiguous | 0 | 0 | — |
| dq_event_before_creation | 0 | 1 | — |
| dq_event_after_last_change | 0 | 0 | — |
| dq_has_problem | 0 | 1 | — |

## Huellas de archivos

```json
{
  "data\\processed\\issues_change_history_clean.csv": "c8186426422f7aaa74070fdaf6ab1da23f00677754615d998ff93d9693707292",
  "data\\processed\\issues_clean.csv": "05a3dde8e3f276a1a8bf137890e5a662221dc0cfa0c262ba3ae82b4c7757c538",
  "data\\raw\\issues.csv": "eab3b8857bc19bd917e0767fb9c30b7714d5468b25c5a1c1cd71a760e9602f02",
  "data\\raw\\issues_change_history.csv": "93f6d99893bac6eb755c075dc4a3c3f655cab7c6b4e2d54a3dca0b26e4b6a3c6"
}
```

Las anomalías de Fase 2 permanecen; una importación correcta conserva esas advertencias. El éxito confirma fidelidad de almacenamiento, no resuelve sus causas de negocio.

Referencias: [pyodbc Cursor](https://github.com/mkleehammer/pyodbc/wiki/Cursor), [GO](https://learn.microsoft.com/en-us/sql/t-sql/language-elements/sql-server-utilities-statements-go).

## Comprobaciones complementarias posteriores al COMMIT

25 pruebas autom?ticas superadas (13 nuevas). Se comprob? tambi?n el rechazo real de una preparaci?n/carga sobre las tablas pobladas; conteos posteriores intactos: 66.691 y 257.508. No se ejecut? ninguna nueva inserci?n.

| ID ticket | Columna | CSV | SQL | Coincidencia |
|---:|---|---|---|---|
| 36146 | wf_resolved | 6.6690000000000005 | 6.6690000000000005 | Exacta |
| 44472 | wf_under_review | -181782.279 | -181782.2790000000000000 | Exacta |
| 29765 | started | 2018-08-27 09:53:57.546000+00:00 | 2018-08-27T09:53:57.5460000Z | Exacta |
