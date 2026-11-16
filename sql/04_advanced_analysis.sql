-- Análisis avanzado: conectar a HelpDeskAnalytics. Sólo lectura.
-- QUERY: S
SELECT COUNT_BIG(*) AS tickets,
 SUM(CONVERT(bigint,CASE WHEN DATEPART(TZOFFSET,issue_created)<>0 OR DATEPART(TZOFFSET,issue_resolution_date)<>0 THEN 1 ELSE 0 END)) AS offset_no_utc,
 SUM(CONVERT(bigint,CASE WHEN DATEPART(NANOSECOND,issue_created)%1000<>0 OR DATEPART(NANOSECOND,issue_resolution_date)%1000<>0 THEN 1 ELSE 0 END)) AS fraccion_submicrosegundo,
 CONVERT(varchar(40),MIN(issue_created),127) AS creacion_min,
 CONVERT(varchar(40),(SELECT MIN(created) FROM stg.issue_change_history),127) AS historial_min,
 CONVERT(varchar(40),(SELECT MAX(t) FROM (
 SELECT MAX(issue_created) AS t FROM stg.issues UNION ALL SELECT MAX(issue_resolution_date) FROM stg.issues
 UNION ALL SELECT MAX(last_change_date) FROM stg.issues UNION ALL SELECT MAX(created) FROM stg.issue_change_history) fechas),127) AS corte_observado
FROM stg.issues;

-- QUERY: A
;WITH base AS (
 SELECT i.*,
 CASE WHEN issue_resolution COLLATE Latin1_General_100_BIN2=N'Done' THEN N'Done'
      WHEN issue_resolution IS NULL THEN N'Sin resolución' ELSE N'Otras resoluciones' END AS grupo,
 CASE WHEN issue_resolution IS NULL THEN N'sin_resolucion'
      WHEN issue_created IS NULL OR issue_resolution_date IS NULL THEN N'sin_fechas'
      WHEN issue_resolution_date<issue_created THEN N'orden_negativo' ELSE N'elegible' END AS motivo,
 CASE WHEN issue_resolution IS NOT NULL AND issue_created IS NOT NULL AND issue_resolution_date>=issue_created
 THEN DATEDIFF_BIG(MICROSECOND,issue_created,issue_resolution_date)/1000000.0 END AS segundos
 FROM stg.issues i
), metricas AS (
 SELECT grupo,COUNT_BIG(*) OVER(PARTITION BY grupo) AS poblacion,
 COUNT_BIG(segundos) OVER(PARTITION BY grupo) AS elegibles,
 PERCENTILE_CONT(0.5) WITHIN GROUP(ORDER BY segundos) OVER(PARTITION BY grupo) AS mediana_seg,
 PERCENTILE_CONT(0.9) WITHIN GROUP(ORDER BY segundos) OVER(PARTITION BY grupo) AS p90_seg

 FROM base WHERE 1=1
)
SELECT DISTINCT grupo,poblacion,elegibles,poblacion-elegibles AS excluidos,
 mediana_seg,p90_seg,mediana_seg/86400.0 AS mediana_dias,p90_seg/86400.0 AS p90_dias
FROM metricas ORDER BY grupo;

-- QUERY: A_EXCLUSIONES
;WITH base AS (
 SELECT i.*,
 CASE WHEN issue_resolution COLLATE Latin1_General_100_BIN2=N'Done' THEN N'Done'
      WHEN issue_resolution IS NULL THEN N'Sin resolución' ELSE N'Otras resoluciones' END AS grupo,
 CASE WHEN issue_resolution IS NULL THEN N'sin_resolucion'
      WHEN issue_created IS NULL OR issue_resolution_date IS NULL THEN N'sin_fechas'
      WHEN issue_resolution_date<issue_created THEN N'orden_negativo' ELSE N'elegible' END AS motivo,
 CASE WHEN issue_resolution IS NOT NULL AND issue_created IS NOT NULL AND issue_resolution_date>=issue_created
 THEN DATEDIFF_BIG(MICROSECOND,issue_created,issue_resolution_date)/1000000.0 END AS segundos
 FROM stg.issues i
) SELECT grupo,motivo,COUNT_BIG(*) AS tickets FROM base GROUP BY grupo,motivo ORDER BY grupo,motivo;

-- QUERY: B
;WITH base AS (
 SELECT i.*,
 CASE WHEN issue_resolution COLLATE Latin1_General_100_BIN2=N'Done' THEN N'Done'
      WHEN issue_resolution IS NULL THEN N'Sin resolución' ELSE N'Otras resoluciones' END AS grupo,
 CASE WHEN issue_resolution IS NULL THEN N'sin_resolucion'
      WHEN issue_created IS NULL OR issue_resolution_date IS NULL THEN N'sin_fechas'
      WHEN issue_resolution_date<issue_created THEN N'orden_negativo' ELSE N'elegible' END AS motivo,
 CASE WHEN issue_resolution IS NOT NULL AND issue_created IS NOT NULL AND issue_resolution_date>=issue_created
 THEN DATEDIFF_BIG(MICROSECOND,issue_created,issue_resolution_date)/1000000.0 END AS segundos
 FROM stg.issues i
), prioridades AS (SELECT *,issue_priority COLLATE Latin1_General_100_BIN2 AS prioridad FROM base), metricas AS (
 SELECT prioridad,COUNT_BIG(*) OVER(PARTITION BY prioridad) AS poblacion,
 COUNT_BIG(segundos) OVER(PARTITION BY prioridad) AS elegibles,
 PERCENTILE_CONT(0.5) WITHIN GROUP(ORDER BY segundos) OVER(PARTITION BY prioridad) AS mediana_seg,
 PERCENTILE_CONT(0.9) WITHIN GROUP(ORDER BY segundos) OVER(PARTITION BY prioridad) AS p90_seg

 FROM prioridades WHERE grupo=N'Done'
)
SELECT DISTINCT prioridad,poblacion,elegibles,poblacion-elegibles AS excluidos,
 mediana_seg,p90_seg,mediana_seg/86400.0 AS mediana_dias,p90_seg/86400.0 AS p90_dias
FROM metricas ORDER BY prioridad;

-- QUERY: B_TIPO
;WITH base AS (
 SELECT i.*,
 CASE WHEN issue_resolution COLLATE Latin1_General_100_BIN2=N'Done' THEN N'Done'
      WHEN issue_resolution IS NULL THEN N'Sin resolución' ELSE N'Otras resoluciones' END AS grupo,
 CASE WHEN issue_resolution IS NULL THEN N'sin_resolucion'
      WHEN issue_created IS NULL OR issue_resolution_date IS NULL THEN N'sin_fechas'
      WHEN issue_resolution_date<issue_created THEN N'orden_negativo' ELSE N'elegible' END AS motivo,
 CASE WHEN issue_resolution IS NOT NULL AND issue_created IS NOT NULL AND issue_resolution_date>=issue_created
 THEN DATEDIFF_BIG(MICROSECOND,issue_created,issue_resolution_date)/1000000.0 END AS segundos
 FROM stg.issues i
), tipos AS (SELECT *,issue_priority COLLATE Latin1_General_100_BIN2 AS prioridad,issue_type COLLATE Latin1_General_100_BIN2 AS tipo FROM base), metricas AS (
 SELECT prioridad,tipo,COUNT_BIG(*) OVER(PARTITION BY prioridad,tipo) AS poblacion,
 COUNT_BIG(segundos) OVER(PARTITION BY prioridad,tipo) AS elegibles,
 PERCENTILE_CONT(0.5) WITHIN GROUP(ORDER BY segundos) OVER(PARTITION BY prioridad,tipo) AS mediana_seg,
 PERCENTILE_CONT(0.9) WITHIN GROUP(ORDER BY segundos) OVER(PARTITION BY prioridad,tipo) AS p90_seg

 FROM tipos WHERE grupo=N'Done'
)
SELECT DISTINCT prioridad,tipo,poblacion,elegibles,poblacion-elegibles AS excluidos,
 mediana_seg,p90_seg,mediana_seg/86400.0 AS mediana_dias,p90_seg/86400.0 AS p90_dias
FROM metricas ORDER BY prioridad,tipo;

-- QUERY: C
;WITH base AS (
 SELECT i.*,
 CASE WHEN issue_resolution COLLATE Latin1_General_100_BIN2=N'Done' THEN N'Done'
      WHEN issue_resolution IS NULL THEN N'Sin resolución' ELSE N'Otras resoluciones' END AS grupo,
 CASE WHEN issue_resolution IS NULL THEN N'sin_resolucion'
      WHEN issue_created IS NULL OR issue_resolution_date IS NULL THEN N'sin_fechas'
      WHEN issue_resolution_date<issue_created THEN N'orden_negativo' ELSE N'elegible' END AS motivo,
 CASE WHEN issue_resolution IS NOT NULL AND issue_created IS NOT NULL AND issue_resolution_date>=issue_created
 THEN DATEDIFF_BIG(MICROSECOND,issue_created,issue_resolution_date)/1000000.0 END AS segundos
 FROM stg.issues i
), limites AS (
 SELECT MIN(issue_created) AS inicio,(SELECT MAX(t) FROM (
 SELECT MAX(issue_created) AS t FROM stg.issues UNION ALL SELECT MAX(issue_resolution_date) FROM stg.issues
 UNION ALL SELECT MAX(last_change_date) FROM stg.issues UNION ALL SELECT MAX(created) FROM stg.issue_change_history) f) AS corte FROM stg.issues
), cohortes AS (
 SELECT b.*,p.nivel,p.periodo,CASE WHEN grupo=N'Done' THEN segundos END AS segundos_done,
 CASE WHEN p.periodo<CAST(l.inicio AS date) OR p.fin>CAST(l.corte AS date) THEN 1 ELSE 0 END AS periodo_parcial,
 DATEDIFF_BIG(DAY,p.fin,CAST(l.corte AS date)) AS dias_desde_fin_periodo
 FROM base b CROSS JOIN limites l CROSS APPLY (VALUES
 (N'Anual',DATEFROMPARTS(YEAR(issue_created),1,1),DATEFROMPARTS(YEAR(issue_created),12,31)),
 (N'Mensual',DATEFROMPARTS(YEAR(issue_created),MONTH(issue_created),1),EOMONTH(issue_created))) p(nivel,periodo,fin)
), m AS (
 SELECT nivel,periodo,periodo_parcial,dias_desde_fin_periodo,
 COUNT_BIG(*) OVER(PARTITION BY nivel,periodo) AS cohorte,
 COUNT_BIG(segundos_done) OVER(PARTITION BY nivel,periodo) AS done_elegibles,
 SUM(CONVERT(bigint,CASE WHEN issue_resolution_date IS NULL THEN 1 ELSE 0 END)) OVER(PARTITION BY nivel,periodo) AS sin_fecha_resolucion,
 PERCENTILE_CONT(0.5) WITHIN GROUP(ORDER BY segundos_done) OVER(PARTITION BY nivel,periodo) AS mediana_seg,
 PERCENTILE_CONT(0.9) WITHIN GROUP(ORDER BY segundos_done) OVER(PARTITION BY nivel,periodo) AS p90_seg
 FROM cohortes)
 SELECT DISTINCT nivel,periodo,periodo_parcial,dias_desde_fin_periodo,cohorte,done_elegibles,
 cohorte-done_elegibles AS no_elegibles_done,sin_fecha_resolucion,
 mediana_seg,p90_seg,mediana_seg/86400.0 AS mediana_dias FROM m ORDER BY nivel,periodo;

-- QUERY: D
;WITH hist AS (
 SELECT issueid,COUNT_BIG(*) AS eventos,
 SUM(CONVERT(bigint,CASE WHEN field COLLATE Latin1_General_100_BIN2=N'status'
 AND value COLLATE Latin1_General_100_BIN2=N'reopened' THEN 1 ELSE 0 END)) AS reopened,
 SUM(CONVERT(bigint,CASE WHEN field COLLATE Latin1_General_100_BIN2=N'assignee' THEN 1 ELSE 0 END)) AS assignee,
 SUM(CONVERT(bigint,CASE WHEN field COLLATE Latin1_General_100_BIN2=N'assignee' AND value IS NULL THEN 1 ELSE 0 END)) AS assignee_null
 FROM stg.issue_change_history GROUP BY issueid
), joined AS (
 SELECT i.id,i.wfe_reopened,h.*,
 CASE WHEN i.issue_created<(SELECT MIN(created) FROM stg.issue_change_history)
 THEN N'Creación anterior al historial' ELSE N'Creación desde inicio historial' END AS cobertura
 FROM stg.issues i LEFT JOIN hist h ON h.issueid=i.id
)
SELECT ambito AS cobertura,COUNT_BIG(*) AS tickets,
 SUM(CONVERT(bigint,CASE WHEN eventos IS NOT NULL THEN 1 ELSE 0 END)) AS con_historial,
 SUM(CONVERT(bigint,CASE WHEN wfe_reopened IS NULL THEN 1 ELSE 0 END)) AS agregado_null,
 SUM(CONVERT(bigint,CASE WHEN wfe_reopened>0 THEN 1 ELSE 0 END)) AS tickets_wfe_reopened,
 SUM(wfe_reopened) AS visitas_agregadas,
 SUM(CONVERT(bigint,CASE WHEN reopened>0 THEN 1 ELSE 0 END)) AS tickets_evento_reopened,
 SUM(COALESCE(reopened,0)) AS eventos_reopened,
 SUM(CONVERT(bigint,CASE WHEN eventos IS NOT NULL AND wfe_reopened IS NOT NULL THEN 1 ELSE 0 END)) AS comparables,
 SUM(CONVERT(bigint,CASE WHEN eventos IS NOT NULL AND wfe_reopened<>reopened THEN 1 ELSE 0 END)) AS discrepantes,
 CAST(100.0*SUM(CONVERT(bigint,CASE WHEN wfe_reopened>0 THEN 1 ELSE 0 END))/NULLIF(COUNT_BIG(*),0) AS decimal(9,4)) AS pct_wfe,
 CAST(100.0*SUM(CONVERT(bigint,CASE WHEN reopened>0 THEN 1 ELSE 0 END))/NULLIF(SUM(CONVERT(bigint,CASE WHEN eventos IS NOT NULL THEN 1 ELSE 0 END)),0) AS decimal(9,4)) AS pct_evento_con_historial
FROM joined CROSS APPLY (VALUES(cobertura),(N'Todos')) p(ambito) GROUP BY ambito ORDER BY cobertura;

-- QUERY: D_DIFERENCIAS
;WITH hist AS (
 SELECT issueid,COUNT_BIG(*) AS eventos,
 SUM(CONVERT(bigint,CASE WHEN field COLLATE Latin1_General_100_BIN2=N'status'
 AND value COLLATE Latin1_General_100_BIN2=N'reopened' THEN 1 ELSE 0 END)) AS reopened,
 SUM(CONVERT(bigint,CASE WHEN field COLLATE Latin1_General_100_BIN2=N'assignee' THEN 1 ELSE 0 END)) AS assignee,
 SUM(CONVERT(bigint,CASE WHEN field COLLATE Latin1_General_100_BIN2=N'assignee' AND value IS NULL THEN 1 ELSE 0 END)) AS assignee_null
 FROM stg.issue_change_history GROUP BY issueid
), joined AS (
 SELECT i.id,i.wfe_reopened,h.*,
 CASE WHEN i.issue_created<(SELECT MIN(created) FROM stg.issue_change_history)
 THEN N'Creación anterior al historial' ELSE N'Creación desde inicio historial' END AS cobertura
 FROM stg.issues i LEFT JOIN hist h ON h.issueid=i.id
)
SELECT TOP(20) id,cobertura,wfe_reopened,reopened AS eventos_reopened,eventos AS eventos_total
FROM joined WHERE eventos IS NOT NULL AND wfe_reopened<>reopened ORDER BY ABS(wfe_reopened-reopened) DESC,id;

-- QUERY: E
;WITH hist AS (
 SELECT issueid,COUNT_BIG(*) AS eventos,
 SUM(CONVERT(bigint,CASE WHEN field COLLATE Latin1_General_100_BIN2=N'status'
 AND value COLLATE Latin1_General_100_BIN2=N'reopened' THEN 1 ELSE 0 END)) AS reopened,
 SUM(CONVERT(bigint,CASE WHEN field COLLATE Latin1_General_100_BIN2=N'assignee' THEN 1 ELSE 0 END)) AS assignee,
 SUM(CONVERT(bigint,CASE WHEN field COLLATE Latin1_General_100_BIN2=N'assignee' AND value IS NULL THEN 1 ELSE 0 END)) AS assignee_null
 FROM stg.issue_change_history GROUP BY issueid
), joined AS (
 SELECT i.id,i.wfe_reopened,h.*,
 CASE WHEN i.issue_created<(SELECT MIN(created) FROM stg.issue_change_history)
 THEN N'Creación anterior al historial' ELSE N'Creación desde inicio historial' END AS cobertura
 FROM stg.issues i LEFT JOIN hist h ON h.issueid=i.id
), m AS (
SELECT ambito AS cobertura,COUNT_BIG(*) OVER(PARTITION BY ambito) AS tickets,
 COUNT_BIG(eventos) OVER(PARTITION BY ambito) AS con_historial,
 SUM(COALESCE(assignee,0)) OVER(PARTITION BY ambito) AS eventos_assignee,
 SUM(COALESCE(assignee_null,0)) OVER(PARTITION BY ambito) AS valores_null,
 SUM(CONVERT(bigint,CASE WHEN assignee>1 THEN 1 ELSE 0 END)) OVER(PARTITION BY ambito) AS tickets_multiples,
 PERCENTILE_CONT(0.5) WITHIN GROUP(ORDER BY assignee) OVER(PARTITION BY ambito) AS mediana_eventos,
 PERCENTILE_CONT(0.9) WITHIN GROUP(ORDER BY assignee) OVER(PARTITION BY ambito) AS p90_eventos
FROM joined CROSS APPLY (VALUES(cobertura),(N'Todos')) p(ambito))
SELECT DISTINCT cobertura,tickets,con_historial,tickets-con_historial AS sin_historial,eventos_assignee,valores_null,
 tickets_multiples,mediana_eventos,p90_eventos,CAST(100.0*tickets_multiples/NULLIF(con_historial,0) AS decimal(9,4)) AS pct_multiples
FROM m ORDER BY cobertura;

-- QUERY: F
;WITH estados AS (
SELECT i.id,e.*,
 CASE WHEN segundos>=0 THEN segundos END AS no_negativo,
 CASE WHEN segundos>=0 AND visitas>0 THEN CONVERT(float,segundos)/NULLIF(visitas,0) END AS promedio_por_visita
FROM stg.issues i CROSS APPLY (VALUES (N'in_review',i.[wf_in_review],i.[wfe_in_review]),
(N'deployment',i.[wf_deployment],i.[wfe_deployment]),
(N'resolved',i.[wf_resolved],i.[wfe_resolved]),
(N'open',i.[wf_open],i.[wfe_open]),
(N'monitoring',i.[wf_monitoring],i.[wfe_monitoring]),
(N'done',i.[wf_done],i.[wfe_done]),
(N'pending_customer_approval',i.[wf_pending_customer_approval],i.[wfe_pending_customer_approval]),
(N'rejected',i.[wf_rejected],i.[wfe_rejected]),
(N'testing_monitoring',i.[wf_testing_monitoring],i.[wfe_testing_monitoring]),
(N'in_progress',i.[wf_in_progress],i.[wfe_in_progress]),
(N'reopened',i.[wf_reopened],i.[wfe_reopened]),
(N'to_do',i.[wf_to_do],i.[wfe_to_do]),
(N'validation',i.[wf_validation],i.[wfe_validation]),
(N'resolved_under_monitoring',i.[wf_resolved_under_monitoring],i.[wfe_resolved_under_monitoring]),
(N'closed',i.[wf_closed],i.[wfe_closed]),
(N'waiting',i.[wf_waiting],i.[wfe_waiting]),
(N'cancelled',i.[wf_cancelled],i.[wfe_cancelled]),
(N'under_review',i.[wf_under_review],i.[wfe_under_review]),
(N'approved',i.[wf_approved],i.[wfe_approved]),
(N'pending_deployment',i.[wf_pending_deployment],i.[wfe_pending_deployment])) e(estado,segundos,visitas)
), m AS (
SELECT estado,COUNT_BIG(*) OVER(PARTITION BY estado) AS tickets,
 COUNT_BIG(segundos) OVER(PARTITION BY estado) AS observados,
 SUM(CONVERT(bigint,CASE WHEN segundos>0 THEN 1 ELSE 0 END)) OVER(PARTITION BY estado) AS positivos,
 SUM(CONVERT(bigint,CASE WHEN segundos=0 THEN 1 ELSE 0 END)) OVER(PARTITION BY estado) AS ceros,
 SUM(CONVERT(bigint,CASE WHEN segundos<0 THEN 1 ELSE 0 END)) OVER(PARTITION BY estado) AS negativos,
 SUM(segundos) OVER(PARTITION BY estado) AS suma_firmada_seg,
 SUM(CASE WHEN segundos>0 THEN segundos END) OVER(PARTITION BY estado) AS suma_positiva_seg,
 COUNT_BIG(promedio_por_visita) OVER(PARTITION BY estado) AS elegibles_por_visita,
 SUM(CONVERT(bigint,CASE WHEN segundos IS NOT NULL AND (visitas IS NULL OR visitas<=0) THEN 1 ELSE 0 END)) OVER(PARTITION BY estado) AS duracion_sin_visitas_validas,
 PERCENTILE_CONT(0.5) WITHIN GROUP(ORDER BY no_negativo) OVER(PARTITION BY estado) AS mediana_no_neg_seg,
 PERCENTILE_CONT(0.9) WITHIN GROUP(ORDER BY no_negativo) OVER(PARTITION BY estado) AS p90_no_neg_seg,
 PERCENTILE_CONT(0.5) WITHIN GROUP(ORDER BY segundos) OVER(PARTITION BY estado) AS mediana_firmada_seg,
 PERCENTILE_CONT(0.9) WITHIN GROUP(ORDER BY segundos) OVER(PARTITION BY estado) AS p90_firmada_seg,
 PERCENTILE_CONT(0.5) WITHIN GROUP(ORDER BY promedio_por_visita) OVER(PARTITION BY estado) AS mediana_promedio_visita_seg
FROM estados)
SELECT DISTINCT estado,tickets,observados,tickets-observados AS nulos,positivos,ceros,negativos,
 suma_firmada_seg,suma_positiva_seg,elegibles_por_visita,duracion_sin_visitas_validas,
 mediana_no_neg_seg,p90_no_neg_seg,mediana_firmada_seg,p90_firmada_seg,mediana_promedio_visita_seg
FROM m ORDER BY suma_positiva_seg DESC,estado;

-- QUERY: Q
;WITH base AS (
 SELECT i.*,
 CASE WHEN issue_resolution COLLATE Latin1_General_100_BIN2=N'Done' THEN N'Done'
      WHEN issue_resolution IS NULL THEN N'Sin resolución' ELSE N'Otras resoluciones' END AS grupo,
 CASE WHEN issue_resolution IS NULL THEN N'sin_resolucion'
      WHEN issue_created IS NULL OR issue_resolution_date IS NULL THEN N'sin_fechas'
      WHEN issue_resolution_date<issue_created THEN N'orden_negativo' ELSE N'elegible' END AS motivo,
 CASE WHEN issue_resolution IS NOT NULL AND issue_created IS NOT NULL AND issue_resolution_date>=issue_created
 THEN DATEDIFF_BIG(MICROSECOND,issue_created,issue_resolution_date)/1000000.0 END AS segundos
 FROM stg.issues i
), escenarios AS (SELECT b.*,s.escenario,CASE WHEN s.incluir=1 THEN segundos END AS valor FROM base b CROSS APPLY (VALUES (N'Base Done',1),
 (N'Sin dq_has_problem (sensibilidad)',CASE WHEN dq_has_problem=0 THEN 1 ELSE 0 END),
 (N'Sin negativos/mismatch workflow',CASE WHEN dq_negative_duration=0 AND dq_duration_mismatch=0 THEN 1 ELSE 0 END),
 (N'Creación desde 2016',CASE WHEN issue_created>='2016-01-01T00:00:00+00:00' THEN 1 ELSE 0 END),
 (N'Fechas sin flags específicos',CASE WHEN dq_invalid_issue_created=0 AND dq_invalid_issue_resolution_date=0 AND dq_naive_issue_created=0 AND dq_naive_issue_resolution_date=0 AND dq_resolution_before_creation=0 THEN 1 ELSE 0 END)) s(escenario,incluir)), filtrados AS (SELECT escenario,valor AS segundos FROM escenarios WHERE grupo=N'Done'), metricas AS (
 SELECT escenario,COUNT_BIG(*) OVER(PARTITION BY escenario) AS poblacion,
 COUNT_BIG(segundos) OVER(PARTITION BY escenario) AS elegibles,
 PERCENTILE_CONT(0.5) WITHIN GROUP(ORDER BY segundos) OVER(PARTITION BY escenario) AS mediana_seg,
 PERCENTILE_CONT(0.9) WITHIN GROUP(ORDER BY segundos) OVER(PARTITION BY escenario) AS p90_seg

 FROM filtrados WHERE 1=1
)
SELECT DISTINCT escenario,poblacion,elegibles,poblacion-elegibles AS excluidos,
 mediana_seg,p90_seg,mediana_seg/86400.0 AS mediana_dias,p90_seg/86400.0 AS p90_dias
FROM metricas ORDER BY escenario;

-- QUERY: Q_FLAGS
;WITH base AS (
 SELECT i.*,
 CASE WHEN issue_resolution COLLATE Latin1_General_100_BIN2=N'Done' THEN N'Done'
      WHEN issue_resolution IS NULL THEN N'Sin resolución' ELSE N'Otras resoluciones' END AS grupo,
 CASE WHEN issue_resolution IS NULL THEN N'sin_resolucion'
      WHEN issue_created IS NULL OR issue_resolution_date IS NULL THEN N'sin_fechas'
      WHEN issue_resolution_date<issue_created THEN N'orden_negativo' ELSE N'elegible' END AS motivo,
 CASE WHEN issue_resolution IS NOT NULL AND issue_created IS NOT NULL AND issue_resolution_date>=issue_created
 THEN DATEDIFF_BIG(MICROSECOND,issue_created,issue_resolution_date)/1000000.0 END AS segundos
 FROM stg.issues i
)
SELECT dq_has_problem,dq_negative_duration,dq_duration_mismatch,COUNT_BIG(*) AS tickets,
 SUM(CONVERT(bigint,CASE WHEN segundos IS NOT NULL THEN 1 ELSE 0 END)) AS elegibles_calendario,
 SUM(CONVERT(bigint,CASE WHEN segundos IS NOT NULL AND grupo=N'Done' THEN 1 ELSE 0 END)) AS elegibles_done
FROM base GROUP BY dq_has_problem,dq_negative_duration,dq_duration_mismatch
ORDER BY dq_has_problem,dq_negative_duration,dq_duration_mismatch;

-- QUERY: A_MUESTRA
;WITH base AS (
 SELECT i.*,
 CASE WHEN issue_resolution COLLATE Latin1_General_100_BIN2=N'Done' THEN N'Done'
      WHEN issue_resolution IS NULL THEN N'Sin resolución' ELSE N'Otras resoluciones' END AS grupo,
 CASE WHEN issue_resolution IS NULL THEN N'sin_resolucion'
      WHEN issue_created IS NULL OR issue_resolution_date IS NULL THEN N'sin_fechas'
      WHEN issue_resolution_date<issue_created THEN N'orden_negativo' ELSE N'elegible' END AS motivo,
 CASE WHEN issue_resolution IS NOT NULL AND issue_created IS NOT NULL AND issue_resolution_date>=issue_created
 THEN DATEDIFF_BIG(MICROSECOND,issue_created,issue_resolution_date)/1000000.0 END AS segundos
 FROM stg.issues i
)
SELECT TOP(10) id,CONVERT(varchar(40),issue_created,127) AS creacion_utc,
 CONVERT(varchar(40),issue_resolution_date,127) AS resolucion_utc,grupo,issue_priority,issue_type,
 segundos,segundos/86400.0 AS dias,CONVERT(varchar(50),wf_total_time) AS wf_total_seg,
 dq_has_problem,dq_duration_mismatch FROM base WHERE segundos IS NOT NULL ORDER BY segundos DESC,id;

-- QUERY: P
;WITH base AS (
 SELECT i.*,
 CASE WHEN issue_resolution COLLATE Latin1_General_100_BIN2=N'Done' THEN N'Done'
      WHEN issue_resolution IS NULL THEN N'Sin resolución' ELSE N'Otras resoluciones' END AS grupo,
 CASE WHEN issue_resolution IS NULL THEN N'sin_resolucion'
      WHEN issue_created IS NULL OR issue_resolution_date IS NULL THEN N'sin_fechas'
      WHEN issue_resolution_date<issue_created THEN N'orden_negativo' ELSE N'elegible' END AS motivo,
 CASE WHEN issue_resolution IS NOT NULL AND issue_created IS NOT NULL AND issue_resolution_date>=issue_created
 THEN DATEDIFF_BIG(MICROSECOND,issue_created,issue_resolution_date)/1000000.0 END AS segundos
 FROM stg.issues i
), muestra AS (SELECT TOP(4) segundos FROM base WHERE segundos IS NOT NULL GROUP BY segundos ORDER BY segundos)
 SELECT ROW_NUMBER() OVER(ORDER BY segundos) AS posicion,segundos,
 PERCENTILE_CONT(0.5) WITHIN GROUP(ORDER BY segundos) OVER() AS mediana,
 PERCENTILE_CONT(0.9) WITHIN GROUP(ORDER BY segundos) OVER() AS p90 FROM muestra ORDER BY segundos;
