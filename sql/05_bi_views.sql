-- Ejecutar en HelpDeskAnalytics; conserva objetos existentes compatibles.
USE [HelpDeskAnalytics];
GO
IF DB_NAME()<>N'HelpDeskAnalytics' THROW 50001,'Base incorrecta.',1;
SET XACT_ABORT ON;
DECLARE @v0 nvarchar(max)=N'CREATE VIEW [bi].[vw_tickets] AS
WITH eventos AS (
 SELECT issueid,COUNT_BIG(*) AS cantidad_eventos,
 SUM(CONVERT(bigint,CASE WHEN field COLLATE Latin1_General_100_BIN2=N''status'' AND value COLLATE Latin1_General_100_BIN2=N''reopened'' THEN 1 ELSE 0 END)) AS eventos_reopened,
 SUM(CONVERT(bigint,CASE WHEN field COLLATE Latin1_General_100_BIN2=N''assignee'' THEN 1 ELSE 0 END)) AS eventos_assignee
 FROM stg.issue_change_history GROUP BY issueid
), limites AS (SELECT MIN(created) AS inicio FROM stg.issue_change_history)
SELECT i.id AS ticket_id,i.issue_proj AS proyecto,i.issue_type AS tipo,i.issue_priority AS prioridad,
 i.issue_status AS estado,i.issue_resolution AS resolucion,
 CAST(SWITCHOFFSET(i.issue_created,''+00:00'') AS datetime2(7)) AS creacion_utc,
 CAST(SWITCHOFFSET(i.issue_resolution_date,''+00:00'') AS datetime2(7)) AS resolucion_utc,
 CAST(SWITCHOFFSET(i.issue_created,''+00:00'') AS date) AS fecha_creacion_utc,
 YEAR(SWITCHOFFSET(i.issue_created,''+00:00'')) AS anio_creacion,
 MONTH(SWITCHOFFSET(i.issue_created,''+00:00'')) AS mes_creacion,
 DATEFROMPARTS(YEAR(SWITCHOFFSET(i.issue_created,''+00:00'')),MONTH(SWITCHOFFSET(i.issue_created,''+00:00'')),1) AS periodo_creacion,
 d.segundos AS intervalo_calendario_segundos,
 CASE WHEN e.elegible=1 THEN d.segundos END AS tiempo_calendario_segundos,
 CAST(CASE WHEN e.elegible=1 THEN d.segundos/86400.0 END AS decimal(28,12)) AS tiempo_calendario_dias,
 CAST(e.elegible AS bit) AS elegible_calendario,
 CAST(CASE WHEN e.elegible=1 AND i.issue_resolution COLLATE Latin1_General_100_BIN2=N''Done'' THEN 1 ELSE 0 END AS bit) AS elegible_done,
 CAST(CASE WHEN e.elegible=1 AND i.issue_resolution COLLATE Latin1_General_100_BIN2<>N''Done'' THEN 1 ELSE 0 END AS bit) AS elegible_otra_resolucion,
 CAST(CASE WHEN i.issue_resolution IS NULL THEN N''sin_resolucion''
 WHEN i.issue_created IS NULL OR i.issue_resolution_date IS NULL THEN N''sin_fechas''
 WHEN i.issue_resolution_date<i.issue_created THEN N''orden_negativo'' ELSE N''elegible'' END AS nvarchar(32)) AS motivo_elegibilidad,
 COALESCE(h.cantidad_eventos,CONVERT(bigint,0)) AS cantidad_eventos,
 COALESCE(h.eventos_reopened,CONVERT(bigint,0)) AS eventos_reopened,
 COALESCE(h.eventos_assignee,CONVERT(bigint,0)) AS eventos_assignee,
 CAST(CASE WHEN h.issueid IS NOT NULL THEN 1 ELSE 0 END AS bit) AS tiene_historial,
 CAST(SWITCHOFFSET(l.inicio,''+00:00'') AS datetime2(7)) AS inicio_historial_observado_utc,
 CAST(CASE WHEN i.issue_created IS NULL OR l.inicio IS NULL THEN NULL
 WHEN i.issue_created<l.inicio THEN 1 ELSE 0 END AS bit) AS creacion_anterior_inicio_historial,
 CAST(CASE WHEN h.issueid IS NULL THEN N''Sin eventos observados''
 WHEN i.issue_created IS NULL OR l.inicio IS NULL THEN N''Cobertura temporal desconocida''
 WHEN i.issue_created<l.inicio THEN N''Creación anterior al historial''
 ELSE N''Creación desde inicio historial'' END AS nvarchar(50)) AS cobertura_historica,
 i.wfe_reopened AS visitas_reopened_agregadas,
 CAST(CASE WHEN h.issueid IS NOT NULL AND i.wfe_reopened IS NOT NULL THEN 1 ELSE 0 END AS bit) AS reaperturas_comparables,
 CASE WHEN h.issueid IS NOT NULL AND i.wfe_reopened IS NOT NULL THEN i.wfe_reopened-h.eventos_reopened END AS diferencia_reopened,
 i.wf_total_time AS wf_total_time_segundos,
 i.[dq_source_row],
 i.[dq_duplicate_row],
 i.[dq_invalid_id],
 i.[dq_missing_id],
 i.[dq_invalid_issue_num],
 i.[dq_missing_issue_num],
 i.[dq_duplicate_id],
 i.[dq_invalid_started],
 i.[dq_missing_started],
 i.[dq_naive_started],
 i.[dq_invalid_ended],
 i.[dq_missing_ended],
 i.[dq_naive_ended],
 i.[dq_invalid_issue_created],
 i.[dq_missing_issue_created],
 i.[dq_naive_issue_created],
 i.[dq_invalid_issue_resolution_date],
 i.[dq_missing_issue_resolution_date],
 i.[dq_naive_issue_resolution_date],
 i.[dq_invalid_last_change_date],
 i.[dq_missing_last_change_date],
 i.[dq_naive_last_change_date],
 i.[dq_missing_optional],
 i.[dq_invalid_duration],
 i.[dq_negative_workflow_duration],
 i.[dq_negative_elapsed],
 i.[dq_negative_duration],
 i.[dq_duration_comparable],
 i.[dq_duration_mismatch],
 i.[dq_resolution_before_creation],
 i.[dq_last_change_before_creation],
 i.[dq_start_before_creation],
 i.[dq_end_after_last_change],
 i.[dq_duplicate_project_number],
 i.[dq_no_history],
 i.[dq_has_problem]
FROM stg.issues i LEFT JOIN eventos h ON h.issueid=i.id CROSS JOIN limites l
CROSS APPLY (SELECT CAST(
 CAST(DATEDIFF_BIG(SECOND,i.issue_created,i.issue_resolution_date) AS decimal(28,7))+
 CAST((DATEPART(NANOSECOND,i.issue_resolution_date)-DATEPART(NANOSECOND,i.issue_created))/1000000000.0 AS decimal(10,7))
 AS decimal(28,7)) AS segundos) d
CROSS APPLY (SELECT CASE WHEN i.issue_resolution IS NOT NULL AND i.issue_created IS NOT NULL
 AND i.issue_resolution_date>=i.issue_created THEN 1 ELSE 0 END AS elegible) e;';
IF OBJECT_ID(N'bi.vw_tickets') IS NOT NULL AND (OBJECT_ID(N'bi.vw_tickets',N'V') IS NULL OR ISNULL(OBJECT_DEFINITION(OBJECT_ID(N'bi.vw_tickets')),N'') COLLATE Latin1_General_100_BIN2<>@v0 COLLATE Latin1_General_100_BIN2)
    THROW 50002,'Objeto bi.vw_tickets existente incompatible; no se modifica.',1;
DECLARE @v1 nvarchar(max)=N'CREATE VIEW [bi].[vw_ticket_events] AS
SELECT h.id AS event_id,h.issueid AS ticket_id,h.field AS campo,h.value AS valor,
 CAST(SWITCHOFFSET(h.created,''+00:00'') AS datetime2(7)) AS evento_utc,
 CAST(SWITCHOFFSET(h.created,''+00:00'') AS date) AS fecha_evento_utc,
 h.change_group_id AS grupo_cambio_id,
 h.[dq_source_row],
 h.[dq_duplicate_row],
 h.[id__raw],
 h.[dq_invalid_id],
 h.[dq_missing_id],
 h.[issueid__raw],
 h.[dq_invalid_issueid],
 h.[dq_missing_issueid],
 h.[change_group_id__raw],
 h.[dq_invalid_change_group_id],
 h.[dq_missing_change_group_id],
 h.[dq_duplicate_id],
 h.[created__raw],
 h.[dq_invalid_created],
 h.[dq_missing_created],
 h.[dq_naive_created],
 h.[dq_missing_optional],
 h.[dq_orphan_issue],
 h.[dq_parent_ambiguous],
 h.[dq_event_before_creation],
 h.[dq_event_after_last_change],
 h.[dq_has_problem]
FROM stg.issue_change_history h;';
IF OBJECT_ID(N'bi.vw_ticket_events') IS NOT NULL AND (OBJECT_ID(N'bi.vw_ticket_events',N'V') IS NULL OR ISNULL(OBJECT_DEFINITION(OBJECT_ID(N'bi.vw_ticket_events')),N'') COLLATE Latin1_General_100_BIN2<>@v1 COLLATE Latin1_General_100_BIN2)
    THROW 50002,'Objeto bi.vw_ticket_events existente incompatible; no se modifica.',1;
DECLARE @v2 nvarchar(max)=N'CREATE VIEW [bi].[vw_ticket_state_durations] AS
SELECT i.id AS ticket_id,e.estado,e.duracion_segundos,e.numero_visitas,
 CONVERT(nvarchar(50),e.duracion_segundos) AS duracion_segundos_exacta,
 CAST(CASE WHEN e.duracion_segundos<0 THEN 1 ELSE 0 END AS bit) AS indicador_duracion_negativa,
 CAST(CASE WHEN e.duracion_segundos IS NULL THEN 1 ELSE 0 END AS bit) AS duracion_faltante,
 CAST(CASE WHEN e.duracion_segundos=0 THEN 1 ELSE 0 END AS bit) AS duracion_cero,
 CAST(CASE WHEN e.numero_visitas=0 AND e.duracion_segundos IS NULL THEN 1 ELSE 0 END AS bit) AS estado_no_recorrido,
 CAST(CASE WHEN e.numero_visitas>0 THEN 1 ELSE 0 END AS bit) AS estado_recorrido,
 CAST(CASE WHEN e.duracion_segundos>=0 THEN 1 ELSE 0 END AS bit) AS elegible_duracion_no_negativa,
 CAST(CASE WHEN e.duracion_segundos>=0 AND e.numero_visitas>0 THEN 1 ELSE 0 END AS bit) AS elegible_promedio_visita,
 CASE WHEN e.duracion_segundos>=0 AND e.numero_visitas>0 THEN CONVERT(float,e.duracion_segundos)/NULLIF(e.numero_visitas,0) END AS promedio_por_visita_segundos
FROM stg.issues i CROSS APPLY (VALUES
 (N''approved'',i.[wf_approved],i.[wfe_approved]),
 (N''cancelled'',i.[wf_cancelled],i.[wfe_cancelled]),
 (N''closed'',i.[wf_closed],i.[wfe_closed]),
 (N''deployment'',i.[wf_deployment],i.[wfe_deployment]),
 (N''done'',i.[wf_done],i.[wfe_done]),
 (N''in_progress'',i.[wf_in_progress],i.[wfe_in_progress]),
 (N''in_review'',i.[wf_in_review],i.[wfe_in_review]),
 (N''monitoring'',i.[wf_monitoring],i.[wfe_monitoring]),
 (N''open'',i.[wf_open],i.[wfe_open]),
 (N''pending_customer_approval'',i.[wf_pending_customer_approval],i.[wfe_pending_customer_approval]),
 (N''pending_deployment'',i.[wf_pending_deployment],i.[wfe_pending_deployment]),
 (N''rejected'',i.[wf_rejected],i.[wfe_rejected]),
 (N''reopened'',i.[wf_reopened],i.[wfe_reopened]),
 (N''resolved'',i.[wf_resolved],i.[wfe_resolved]),
 (N''resolved_under_monitoring'',i.[wf_resolved_under_monitoring],i.[wfe_resolved_under_monitoring]),
 (N''testing_monitoring'',i.[wf_testing_monitoring],i.[wfe_testing_monitoring]),
 (N''to_do'',i.[wf_to_do],i.[wfe_to_do]),
 (N''under_review'',i.[wf_under_review],i.[wfe_under_review]),
 (N''validation'',i.[wf_validation],i.[wfe_validation]),
 (N''waiting'',i.[wf_waiting],i.[wfe_waiting])
) e(estado,duracion_segundos,numero_visitas);';
IF OBJECT_ID(N'bi.vw_ticket_state_durations') IS NOT NULL AND (OBJECT_ID(N'bi.vw_ticket_state_durations',N'V') IS NULL OR ISNULL(OBJECT_DEFINITION(OBJECT_ID(N'bi.vw_ticket_state_durations')),N'') COLLATE Latin1_General_100_BIN2<>@v2 COLLATE Latin1_General_100_BIN2)
    THROW 50002,'Objeto bi.vw_ticket_state_durations existente incompatible; no se modifica.',1;
BEGIN TRANSACTION;
IF SCHEMA_ID(N'bi') IS NULL EXEC(N'CREATE SCHEMA [bi] AUTHORIZATION [dbo]');
IF OBJECT_ID(N'bi.vw_tickets',N'V') IS NULL EXEC sys.sp_executesql @v0;
IF OBJECT_ID(N'bi.vw_ticket_events',N'V') IS NULL EXEC sys.sp_executesql @v1;
IF OBJECT_ID(N'bi.vw_ticket_state_durations',N'V') IS NULL EXEC sys.sp_executesql @v2;
COMMIT TRANSACTION;
GO
