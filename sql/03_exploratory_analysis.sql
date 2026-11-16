-- HelpDeskAnalytics: elegir esta base en SSMS; el ejecutor Python la selecciona al conectar.
-- Sólo SELECT/CTE. NULL permanece NULL; sin filtro de anomalías.

-- QUERY: S
SELECT OBJECT_NAME(c.object_id) AS tabla,c.column_id AS posicion,c.name AS columna,
 t.name AS tipo,c.max_length AS longitud_bytes,c.precision AS precision,c.scale AS escala,c.is_nullable AS nullable
FROM sys.columns c JOIN sys.types t ON c.user_type_id=t.user_type_id
WHERE c.object_id IN (OBJECT_ID(N'stg.issues'),OBJECT_ID(N'stg.issue_change_history'))
ORDER BY tabla,posicion;
-- QUERY: A
SELECT N'tickets' AS dataset,COUNT_BIG(*) AS cantidad FROM stg.issues
UNION ALL
SELECT N'eventos',COUNT_BIG(*) FROM stg.issue_change_history;

-- QUERY: B
SELECT [issue_priority] COLLATE Latin1_General_100_BIN2 AS categoria,COUNT_BIG(*) AS cantidad,
 CAST(100.0*COUNT_BIG(*)/NULLIF(SUM(COUNT_BIG(*)) OVER(),0) AS decimal(9,4)) AS porcentaje_total
FROM stg.issues
GROUP BY [issue_priority] COLLATE Latin1_General_100_BIN2
ORDER BY cantidad DESC,categoria;

-- QUERY: C
SELECT [issue_type] COLLATE Latin1_General_100_BIN2 AS categoria,COUNT_BIG(*) AS cantidad,
 CAST(100.0*COUNT_BIG(*)/NULLIF(SUM(COUNT_BIG(*)) OVER(),0) AS decimal(9,4)) AS porcentaje_total
FROM stg.issues
GROUP BY [issue_type] COLLATE Latin1_General_100_BIN2
ORDER BY cantidad DESC,categoria;

-- QUERY: D
SELECT [issue_status] COLLATE Latin1_General_100_BIN2 AS categoria,COUNT_BIG(*) AS cantidad,
 CAST(100.0*COUNT_BIG(*)/NULLIF(SUM(COUNT_BIG(*)) OVER(),0) AS decimal(9,4)) AS porcentaje_total
FROM stg.issues
GROUP BY [issue_status] COLLATE Latin1_General_100_BIN2
ORDER BY cantidad DESC,categoria;

-- QUERY: E
SELECT [issue_resolution] COLLATE Latin1_General_100_BIN2 AS categoria,COUNT_BIG(*) AS cantidad,
 CAST(100.0*COUNT_BIG(*)/NULLIF(SUM(COUNT_BIG(*)) OVER(),0) AS decimal(9,4)) AS porcentaje_total
FROM stg.issues
GROUP BY [issue_resolution] COLLATE Latin1_General_100_BIN2
ORDER BY cantidad DESC,categoria;

-- QUERY: F
SELECT YEAR(issue_created) AS periodo,COUNT_BIG(*) AS cantidad,
 CAST(100.0*COUNT_BIG(*)/NULLIF(SUM(COUNT_BIG(*)) OVER(),0) AS decimal(9,4)) AS porcentaje_total
FROM stg.issues GROUP BY YEAR(issue_created)
ORDER BY periodo;

-- QUERY: G
SELECT DATEFROMPARTS(YEAR(issue_created),MONTH(issue_created),1) AS periodo,COUNT_BIG(*) AS cantidad,
 CAST(100.0*COUNT_BIG(*)/NULLIF(SUM(COUNT_BIG(*)) OVER(),0) AS decimal(9,4)) AS porcentaje_total
FROM stg.issues GROUP BY DATEFROMPARTS(YEAR(issue_created),MONTH(issue_created),1)
ORDER BY periodo;

-- QUERY: H
;WITH proyectos AS (
 SELECT issue_proj COLLATE Latin1_General_100_BIN2 AS proyecto,COUNT_BIG(*) AS cantidad
 FROM stg.issues GROUP BY issue_proj COLLATE Latin1_General_100_BIN2
)
SELECT TOP (10) proyecto,cantidad,
 CAST(100.0*cantidad/NULLIF(SUM(cantidad) OVER(),0) AS decimal(9,4)) AS porcentaje_total
FROM proyectos ORDER BY cantidad DESC,proyecto;
-- QUERY: I
;WITH historial AS (
 SELECT issueid,COUNT_BIG(*) AS eventos FROM stg.issue_change_history
 GROUP BY issueid HAVING COUNT_BIG(*)>0
), clasificados AS (
 SELECT CASE WHEN h.issueid IS NULL THEN N'Sin historial' ELSE N'Con historial' END AS cobertura
 FROM stg.issues i LEFT JOIN historial h ON h.issueid=i.id
)
SELECT cobertura,COUNT_BIG(*) AS cantidad,
 CAST(100.0*COUNT_BIG(*)/NULLIF(SUM(COUNT_BIG(*)) OVER(),0) AS decimal(9,4)) AS porcentaje_total
FROM clasificados GROUP BY cobertura ORDER BY cantidad DESC,cobertura;
-- QUERY: J

SELECT N'issues' AS tabla,q.indicador,SUM(q.activo) AS filas_true,COUNT_BIG(*) AS total_tabla,
 CAST(100.0*SUM(q.activo)/NULLIF(COUNT_BIG(*),0) AS decimal(9,4)) AS porcentaje_tabla
FROM stg.[issues] i CROSS APPLY (VALUES
 (N'dq_duplicate_row',CONVERT(bigint,i.[dq_duplicate_row])),
 (N'dq_invalid_id',CONVERT(bigint,i.[dq_invalid_id])),
 (N'dq_missing_id',CONVERT(bigint,i.[dq_missing_id])),
 (N'dq_invalid_issue_num',CONVERT(bigint,i.[dq_invalid_issue_num])),
 (N'dq_missing_issue_num',CONVERT(bigint,i.[dq_missing_issue_num])),
 (N'dq_duplicate_id',CONVERT(bigint,i.[dq_duplicate_id])),
 (N'dq_invalid_started',CONVERT(bigint,i.[dq_invalid_started])),
 (N'dq_missing_started',CONVERT(bigint,i.[dq_missing_started])),
 (N'dq_naive_started',CONVERT(bigint,i.[dq_naive_started])),
 (N'dq_invalid_ended',CONVERT(bigint,i.[dq_invalid_ended])),
 (N'dq_missing_ended',CONVERT(bigint,i.[dq_missing_ended])),
 (N'dq_naive_ended',CONVERT(bigint,i.[dq_naive_ended])),
 (N'dq_invalid_issue_created',CONVERT(bigint,i.[dq_invalid_issue_created])),
 (N'dq_missing_issue_created',CONVERT(bigint,i.[dq_missing_issue_created])),
 (N'dq_naive_issue_created',CONVERT(bigint,i.[dq_naive_issue_created])),
 (N'dq_invalid_issue_resolution_date',CONVERT(bigint,i.[dq_invalid_issue_resolution_date])),
 (N'dq_missing_issue_resolution_date',CONVERT(bigint,i.[dq_missing_issue_resolution_date])),
 (N'dq_naive_issue_resolution_date',CONVERT(bigint,i.[dq_naive_issue_resolution_date])),
 (N'dq_invalid_last_change_date',CONVERT(bigint,i.[dq_invalid_last_change_date])),
 (N'dq_missing_last_change_date',CONVERT(bigint,i.[dq_missing_last_change_date])),
 (N'dq_naive_last_change_date',CONVERT(bigint,i.[dq_naive_last_change_date])),
 (N'dq_missing_optional',CONVERT(bigint,i.[dq_missing_optional])),
 (N'dq_invalid_duration',CONVERT(bigint,i.[dq_invalid_duration])),
 (N'dq_negative_workflow_duration',CONVERT(bigint,i.[dq_negative_workflow_duration])),
 (N'dq_negative_elapsed',CONVERT(bigint,i.[dq_negative_elapsed])),
 (N'dq_negative_duration',CONVERT(bigint,i.[dq_negative_duration])),
 (N'dq_duration_comparable',CONVERT(bigint,i.[dq_duration_comparable])),
 (N'dq_duration_mismatch',CONVERT(bigint,i.[dq_duration_mismatch])),
 (N'dq_resolution_before_creation',CONVERT(bigint,i.[dq_resolution_before_creation])),
 (N'dq_last_change_before_creation',CONVERT(bigint,i.[dq_last_change_before_creation])),
 (N'dq_start_before_creation',CONVERT(bigint,i.[dq_start_before_creation])),
 (N'dq_end_after_last_change',CONVERT(bigint,i.[dq_end_after_last_change])),
 (N'dq_duplicate_project_number',CONVERT(bigint,i.[dq_duplicate_project_number])),
 (N'dq_no_history',CONVERT(bigint,i.[dq_no_history])),
 (N'dq_has_problem',CONVERT(bigint,i.[dq_has_problem]))
) q(indicador,activo) GROUP BY q.indicador
UNION ALL
SELECT N'issue_change_history' AS tabla,q.indicador,SUM(q.activo) AS filas_true,COUNT_BIG(*) AS total_tabla,
 CAST(100.0*SUM(q.activo)/NULLIF(COUNT_BIG(*),0) AS decimal(9,4)) AS porcentaje_tabla
FROM stg.[issue_change_history] i CROSS APPLY (VALUES
 (N'dq_duplicate_row',CONVERT(bigint,i.[dq_duplicate_row])),
 (N'dq_invalid_id',CONVERT(bigint,i.[dq_invalid_id])),
 (N'dq_missing_id',CONVERT(bigint,i.[dq_missing_id])),
 (N'dq_invalid_issueid',CONVERT(bigint,i.[dq_invalid_issueid])),
 (N'dq_missing_issueid',CONVERT(bigint,i.[dq_missing_issueid])),
 (N'dq_invalid_change_group_id',CONVERT(bigint,i.[dq_invalid_change_group_id])),
 (N'dq_missing_change_group_id',CONVERT(bigint,i.[dq_missing_change_group_id])),
 (N'dq_duplicate_id',CONVERT(bigint,i.[dq_duplicate_id])),
 (N'dq_invalid_created',CONVERT(bigint,i.[dq_invalid_created])),
 (N'dq_missing_created',CONVERT(bigint,i.[dq_missing_created])),
 (N'dq_naive_created',CONVERT(bigint,i.[dq_naive_created])),
 (N'dq_missing_optional',CONVERT(bigint,i.[dq_missing_optional])),
 (N'dq_orphan_issue',CONVERT(bigint,i.[dq_orphan_issue])),
 (N'dq_parent_ambiguous',CONVERT(bigint,i.[dq_parent_ambiguous])),
 (N'dq_event_before_creation',CONVERT(bigint,i.[dq_event_before_creation])),
 (N'dq_event_after_last_change',CONVERT(bigint,i.[dq_event_after_last_change])),
 (N'dq_has_problem',CONVERT(bigint,i.[dq_has_problem]))
) q(indicador,activo) GROUP BY q.indicador
ORDER BY tabla,filas_true DESC,indicador;

-- QUERY: K
SELECT issue_status COLLATE Latin1_General_100_BIN2 AS estado,
 issue_resolution COLLATE Latin1_General_100_BIN2 AS resolucion,COUNT_BIG(*) AS cantidad,
 CAST(100.0*COUNT_BIG(*)/NULLIF(SUM(COUNT_BIG(*)) OVER(),0) AS decimal(9,4)) AS porcentaje_total
FROM stg.issues GROUP BY issue_status COLLATE Latin1_General_100_BIN2,issue_resolution COLLATE Latin1_General_100_BIN2
ORDER BY cantidad DESC,estado,resolucion;
-- QUERY: L
SELECT N'issues.issue_created' AS campo,
 CONVERT(varchar(40),MIN(issue_created),127) AS minimo_utc,CONVERT(varchar(40),MAX(issue_created),127) AS maximo_utc,
 SUM(CASE WHEN issue_created<'2016-01-01T00:00:00+00:00' THEN CONVERT(bigint,1) ELSE 0 END) AS antes_2016,
 SUM(CASE WHEN issue_created>='2023-04-01T00:00:00+00:00' THEN CONVERT(bigint,1) ELSE 0 END) AS desde_abril_2023,
 SUM(CASE WHEN issue_created IS NULL THEN CONVERT(bigint,1) ELSE 0 END) AS fechas_null
FROM stg.issues
UNION ALL
SELECT N'history.created',CONVERT(varchar(40),MIN(created),127),CONVERT(varchar(40),MAX(created),127),
 SUM(CASE WHEN created<'2016-01-01T00:00:00+00:00' THEN CONVERT(bigint,1) ELSE 0 END),
 SUM(CASE WHEN created>='2023-04-01T00:00:00+00:00' THEN CONVERT(bigint,1) ELSE 0 END),
 SUM(CASE WHEN created IS NULL THEN CONVERT(bigint,1) ELSE 0 END)
FROM stg.issue_change_history;
-- QUERY: M
SELECT N'issues' AS tabla,MIN(dq_source_row) AS fila_min,MAX(dq_source_row) AS fila_max,COUNT_BIG(DISTINCT dq_source_row) AS filas_distintas
FROM stg.issues UNION ALL
SELECT N'issue_change_history',MIN(dq_source_row),MAX(dq_source_row),COUNT_BIG(DISTINCT dq_source_row)
FROM stg.issue_change_history;
