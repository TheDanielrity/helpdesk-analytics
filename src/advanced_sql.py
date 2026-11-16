"""Genera/ejecuta SELECT avanzados y los verifica independientemente con Pandas."""
from datetime import datetime, timezone
from decimal import Decimal, localcontext
import hashlib
import math
from pathlib import Path
import re
import sys

import numpy as np
import pandas as pd
import pyodbc

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.clean_data import ROOT, read_csv
from src.sql_connection import connect
from src.explore_sql import table

SQL_PATH = ROOT / "sql/04_advanced_analysis.sql"

BASE = """base AS (
 SELECT i.*,
 CASE WHEN issue_resolution COLLATE Latin1_General_100_BIN2=N'Done' THEN N'Done'
      WHEN issue_resolution IS NULL THEN N'Sin resolución' ELSE N'Otras resoluciones' END AS grupo,
 CASE WHEN issue_resolution IS NULL THEN N'sin_resolucion'
      WHEN issue_created IS NULL OR issue_resolution_date IS NULL THEN N'sin_fechas'
      WHEN issue_resolution_date<issue_created THEN N'orden_negativo' ELSE N'elegible' END AS motivo,
 CASE WHEN issue_resolution IS NOT NULL AND issue_created IS NOT NULL AND issue_resolution_date>=issue_created
 THEN DATEDIFF_BIG(MICROSECOND,issue_created,issue_resolution_date)/1000000.0 END AS segundos
 FROM stg.issues i
)"""

HISTORY = """hist AS (
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
)"""


def summary(prefix, dimensions, source="base", condition="1=1", extra=""):
    partition = ",".join(dimensions)
    return f""";WITH {prefix}, metricas AS (
 SELECT {partition},COUNT_BIG(*) OVER(PARTITION BY {partition}) AS poblacion,
 COUNT_BIG(segundos) OVER(PARTITION BY {partition}) AS elegibles,
 PERCENTILE_CONT(0.5) WITHIN GROUP(ORDER BY segundos) OVER(PARTITION BY {partition}) AS mediana_seg,
 PERCENTILE_CONT(0.9) WITHIN GROUP(ORDER BY segundos) OVER(PARTITION BY {partition}) AS p90_seg
 {extra}
 FROM {source} WHERE {condition}
)
SELECT DISTINCT {partition},poblacion,elegibles,poblacion-elegibles AS excluidos,
 mediana_seg,p90_seg,mediana_seg/86400.0 AS mediana_dias,p90_seg/86400.0 AS p90_dias
FROM metricas ORDER BY {partition};"""


def build_queries(states):
    q = {}
    q['S'] = """SELECT COUNT_BIG(*) AS tickets,
 SUM(CONVERT(bigint,CASE WHEN DATEPART(TZOFFSET,issue_created)<>0 OR DATEPART(TZOFFSET,issue_resolution_date)<>0 THEN 1 ELSE 0 END)) AS offset_no_utc,
 SUM(CONVERT(bigint,CASE WHEN DATEPART(NANOSECOND,issue_created)%1000<>0 OR DATEPART(NANOSECOND,issue_resolution_date)%1000<>0 THEN 1 ELSE 0 END)) AS fraccion_submicrosegundo,
 CONVERT(varchar(40),MIN(issue_created),127) AS creacion_min,
 CONVERT(varchar(40),(SELECT MIN(created) FROM stg.issue_change_history),127) AS historial_min,
 CONVERT(varchar(40),(SELECT MAX(t) FROM (
 SELECT MAX(issue_created) AS t FROM stg.issues UNION ALL SELECT MAX(issue_resolution_date) FROM stg.issues
 UNION ALL SELECT MAX(last_change_date) FROM stg.issues UNION ALL SELECT MAX(created) FROM stg.issue_change_history) fechas),127) AS corte_observado
FROM stg.issues;"""
    q['A'] = summary(BASE,['grupo'])
    q['A_EXCLUSIONES'] = f";WITH {BASE} SELECT grupo,motivo,COUNT_BIG(*) AS tickets FROM base GROUP BY grupo,motivo ORDER BY grupo,motivo;"
    # Alias para mantener etiquetas legibles en la partición y en el resultado.
    q['B'] = summary(BASE+", prioridades AS (SELECT *,issue_priority COLLATE Latin1_General_100_BIN2 AS prioridad FROM base)",['prioridad'],source='prioridades',condition="grupo=N'Done'")
    q['B_TIPO'] = summary(BASE+", tipos AS (SELECT *,issue_priority COLLATE Latin1_General_100_BIN2 AS prioridad,issue_type COLLATE Latin1_General_100_BIN2 AS tipo FROM base)",['prioridad','tipo'],source='tipos',condition="grupo=N'Done'")
    cohort = BASE+""", limites AS (
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
)"""
    q['C'] = f""";WITH {cohort}, m AS (
 SELECT nivel,periodo,periodo_parcial,dias_desde_fin_periodo,
 COUNT_BIG(*) OVER(PARTITION BY nivel,periodo) AS cohorte,
 COUNT_BIG(segundos_done) OVER(PARTITION BY nivel,periodo) AS done_elegibles,
 SUM(CONVERT(bigint,CASE WHEN issue_resolution_date IS NULL THEN 1 ELSE 0 END)) OVER(PARTITION BY nivel,periodo) AS sin_fecha_resolucion,
 PERCENTILE_CONT(0.5) WITHIN GROUP(ORDER BY segundos_done) OVER(PARTITION BY nivel,periodo) AS mediana_seg,
 PERCENTILE_CONT(0.9) WITHIN GROUP(ORDER BY segundos_done) OVER(PARTITION BY nivel,periodo) AS p90_seg
 FROM cohortes)
 SELECT DISTINCT nivel,periodo,periodo_parcial,dias_desde_fin_periodo,cohorte,done_elegibles,
 cohorte-done_elegibles AS no_elegibles_done,sin_fecha_resolucion,
 mediana_seg,p90_seg,mediana_seg/86400.0 AS mediana_dias FROM m ORDER BY nivel,periodo;"""
    q['D'] = f""";WITH {HISTORY}
SELECT cobertura,COUNT_BIG(*) AS tickets,
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
FROM joined GROUP BY cobertura ORDER BY cobertura;"""
    q['D_DIFERENCIAS'] = f""";WITH {HISTORY}
SELECT TOP(20) id,cobertura,wfe_reopened,reopened AS eventos_reopened,eventos AS eventos_total
FROM joined WHERE eventos IS NOT NULL AND wfe_reopened<>reopened ORDER BY ABS(wfe_reopened-reopened) DESC,id;"""
    q['E'] = f""";WITH {HISTORY}, m AS (
SELECT cobertura,COUNT_BIG(*) OVER(PARTITION BY cobertura) AS tickets,
 COUNT_BIG(eventos) OVER(PARTITION BY cobertura) AS con_historial,
 SUM(COALESCE(assignee,0)) OVER(PARTITION BY cobertura) AS eventos_assignee,
 SUM(COALESCE(assignee_null,0)) OVER(PARTITION BY cobertura) AS valores_null,
 SUM(CONVERT(bigint,CASE WHEN assignee>1 THEN 1 ELSE 0 END)) OVER(PARTITION BY cobertura) AS tickets_multiples,
 PERCENTILE_CONT(0.5) WITHIN GROUP(ORDER BY assignee) OVER(PARTITION BY cobertura) AS mediana_eventos,
 PERCENTILE_CONT(0.9) WITHIN GROUP(ORDER BY assignee) OVER(PARTITION BY cobertura) AS p90_eventos
FROM joined)
SELECT DISTINCT cobertura,tickets,con_historial,tickets-con_historial AS sin_historial,eventos_assignee,valores_null,
 tickets_multiples,mediana_eventos,p90_eventos,CAST(100.0*tickets_multiples/NULLIF(con_historial,0) AS decimal(9,4)) AS pct_multiples
FROM m ORDER BY cobertura;"""
    # Publicar también el total: una tasa/mediana global no se obtiene promediando cohortes.
    q['D'] = q['D'].replace('SELECT cobertura,COUNT_BIG', 'SELECT ambito AS cobertura,COUNT_BIG').replace(
        'FROM joined GROUP BY cobertura ORDER BY cobertura;',
        "FROM joined CROSS APPLY (VALUES(cobertura),(N'Todos')) p(ambito) GROUP BY ambito ORDER BY cobertura;")
    q['E'] = q['E'].replace('SELECT cobertura,COUNT_BIG', 'SELECT ambito AS cobertura,COUNT_BIG').replace(
        'PARTITION BY cobertura', 'PARTITION BY ambito').replace('FROM joined)',
        "FROM joined CROSS APPLY (VALUES(cobertura),(N'Todos')) p(ambito))")
    vals=",\n".join(f"(N'{s}',i.[wf_{s}],i.[wfe_{s}])" for s in states)
    q['F'] = f""";WITH estados AS (
SELECT i.id,e.*,
 CASE WHEN segundos>=0 THEN segundos END AS no_negativo,
 CASE WHEN segundos>=0 AND visitas>0 THEN CONVERT(float,segundos)/NULLIF(visitas,0) END AS promedio_por_visita
FROM stg.issues i CROSS APPLY (VALUES {vals}) e(estado,segundos,visitas)
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
FROM m ORDER BY suma_positiva_seg DESC,estado;"""
    scenarios = """(N'Base Done',1),
 (N'Sin dq_has_problem (sensibilidad)',CASE WHEN dq_has_problem=0 THEN 1 ELSE 0 END),
 (N'Sin negativos/mismatch workflow',CASE WHEN dq_negative_duration=0 AND dq_duration_mismatch=0 THEN 1 ELSE 0 END),
 (N'Creación desde 2016',CASE WHEN issue_created>='2016-01-01T00:00:00+00:00' THEN 1 ELSE 0 END),
 (N'Fechas sin flags específicos',CASE WHEN dq_invalid_issue_created=0 AND dq_invalid_issue_resolution_date=0 AND dq_naive_issue_created=0 AND dq_naive_issue_resolution_date=0 AND dq_resolution_before_creation=0 THEN 1 ELSE 0 END)"""
    q['Q'] = summary(BASE+f", escenarios AS (SELECT b.*,s.escenario,CASE WHEN s.incluir=1 THEN segundos END AS valor FROM base b CROSS APPLY (VALUES {scenarios}) s(escenario,incluir)), filtrados AS (SELECT escenario,valor AS segundos FROM escenarios WHERE grupo=N'Done')",['escenario'],source='filtrados')
    q['Q_FLAGS'] = f""";WITH {BASE}
SELECT dq_has_problem,dq_negative_duration,dq_duration_mismatch,COUNT_BIG(*) AS tickets,
 SUM(CONVERT(bigint,CASE WHEN segundos IS NOT NULL THEN 1 ELSE 0 END)) AS elegibles_calendario,
 SUM(CONVERT(bigint,CASE WHEN segundos IS NOT NULL AND grupo=N'Done' THEN 1 ELSE 0 END)) AS elegibles_done
FROM base GROUP BY dq_has_problem,dq_negative_duration,dq_duration_mismatch
ORDER BY dq_has_problem,dq_negative_duration,dq_duration_mismatch;"""
    q['A_MUESTRA'] = f""";WITH {BASE}
SELECT TOP(10) id,CONVERT(varchar(40),issue_created,127) AS creacion_utc,
 CONVERT(varchar(40),issue_resolution_date,127) AS resolucion_utc,grupo,issue_priority,issue_type,
 segundos,segundos/86400.0 AS dias,CONVERT(varchar(50),wf_total_time) AS wf_total_seg,
 dq_has_problem,dq_duration_mismatch FROM base WHERE segundos IS NOT NULL ORDER BY segundos DESC,id;"""
    q['P'] = f""";WITH {BASE}, muestra AS (SELECT TOP(4) segundos FROM base WHERE segundos IS NOT NULL GROUP BY segundos ORDER BY segundos)
 SELECT ROW_NUMBER() OVER(ORDER BY segundos) AS posicion,segundos,
 PERCENTILE_CONT(0.5) WITHIN GROUP(ORDER BY segundos) OVER() AS mediana,
 PERCENTILE_CONT(0.9) WITHIN GROUP(ORDER BY segundos) OVER() AS p90 FROM muestra ORDER BY segundos;"""
    return q


def expected_results(t,e,states):
    """Cálculos desde CSV sin reutilizar resultados SQL."""
    t=t.copy(); e=e.copy()
    for c in ('issue_created','issue_resolution_date','last_change_date'):
        t[c]=pd.to_datetime(t[c],utc=True,format='ISO8601')
    e['created']=pd.to_datetime(e.created,utc=True,format='ISO8601')
    t['grupo']=np.where(t.issue_resolution.eq('Done').fillna(False),'Done',np.where(t.issue_resolution.isna(),'Sin resolución','Otras resoluciones'))
    t['motivo']=np.where(t.issue_resolution.isna(),'sin_resolucion',np.where(t.issue_created.isna()|t.issue_resolution_date.isna(),'sin_fechas',np.where(t.issue_resolution_date.lt(t.issue_created),'orden_negativo','elegible')))
    t['segundos']=(t.issue_resolution_date-t.issue_created).dt.total_seconds().where(t.motivo.eq('elegible'))
    def quant(s,p):
        s=pd.to_numeric(s.dropna(),errors='raise').astype(float)
        return float(s.quantile(p,interpolation='linear')) if len(s) else None
    def stats(f):
        med,p90=quant(f.segundos,.5),quant(f.segundos,.9)
        n=int(f.segundos.notna().sum())
        return [len(f),n,len(f)-n,med,p90,None if med is None else med/86400,None if p90 is None else p90/86400]
    def grouped(f,cols):
        return [(key if isinstance(key,tuple) else (key,))+tuple(stats(g)) for key,g in f.groupby(cols,dropna=False)]
    out={}
    out['A']=grouped(t,['grupo'])
    out['A_EXCLUSIONES']=[(a,b,len(g)) for (a,b),g in t.groupby(['grupo','motivo'],dropna=False)]
    done=t.loc[t.grupo.eq('Done')]
    out['B']=grouped(done,['issue_priority'])
    out['B_TIPO']=grouped(done,['issue_priority','issue_type'])
    cutoff=max(t.issue_created.max(),t.issue_resolution_date.max(),t.last_change_date.max(),e.created.max())
    start=t.issue_created.min()
    out['C']=[]
    for level,periods in [('Anual',t.issue_created.dt.strftime('%Y-01-01')),('Mensual',t.issue_created.dt.strftime('%Y-%m-01'))]:
        for period,g in t.groupby(periods,dropna=False):
            p=pd.Timestamp(period,tz='UTC')
            end=p+ (pd.offsets.YearEnd(0) if level=='Anual' else pd.offsets.MonthEnd(0))
            s=g.segundos.where(g.grupo.eq('Done')); med=quant(s,.5); p90=quant(s,.9); n=int(s.notna().sum())
            out['C'].append((level,p.date(),int(p.date()<start.date() or end.date()>cutoff.date()),(cutoff.date()-end.date()).days,len(g),n,len(g)-n,int(g.issue_resolution_date.isna().sum()),med,p90,None if med is None else med/86400))
    e['reopened']=(e.field.eq('status') & e.value.eq('reopened')).fillna(False).astype(int)
    e['assignee']=e.field.eq('assignee').fillna(False).astype(int)
    e['assignee_null']=(e.field.eq('assignee') & e.value.isna()).fillna(False).astype(int)
    h=e.groupby('issueid').agg(eventos=('id','size'),reopened=('reopened','sum'),assignee=('assignee','sum'),assignee_null=('assignee_null','sum'))
    j=t.join(h,on='id',validate='one_to_one')
    j['cobertura']=np.where(j.issue_created.lt(e.created.min()),'Creación anterior al historial','Creación desde inicio historial')
    out['D']=[];out['E']=[]
    for coverage,g in list(j.groupby('cobertura'))+[('Todos',j)]:
        w=pd.to_numeric(g.wfe_reopened); hist=g.eventos.notna(); comp=hist&w.notna(); nh=int(hist.sum())
        pw=int(w.gt(0).sum()); pe=int(g.reopened.gt(0).sum())
        from src.explore_sql import pct
        out['D'].append((coverage,len(g),nh,int(w.isna().sum()),pw,int(w.sum()),pe,int(g.reopened.sum()),int(comp.sum()),int((comp & w.ne(g.reopened)).sum()),pct(pw,len(g)),pct(pe,nh) if nh else None))
        multiple=int(g.assignee.gt(1).sum())
        out['E'].append((coverage,len(g),nh,len(g)-nh,int(g.assignee.sum()),int(g.assignee_null.sum()),multiple,quant(g.assignee,.5),quant(g.assignee,.9),pct(multiple,nh) if nh else None))
    diff=j.loc[j.eventos.notna() & pd.to_numeric(j.wfe_reopened).ne(j.reopened)].copy()
    diff['delta']=(pd.to_numeric(diff.wfe_reopened)-diff.reopened).abs();diff['id_num']=diff.id.map(int)
    diff=diff.sort_values(['delta','id_num'],ascending=[False,True]).head(20)
    out['D_DIFERENCIAS']=[(int(r.id),r.cobertura,int(r.wfe_reopened),int(r.reopened),int(r.eventos)) for r in diff.itertuples()]
    out['F']=[]
    with localcontext() as ctx:
        ctx.prec=50
        for state in states:
            raw=t['wf_'+state].dropna().map(Decimal); vals=raw.astype(float); nn=vals[vals>=0]
            visits=pd.to_numeric(t.loc[raw.index,'wfe_'+state]); pv=(vals/visits.where(visits>0)).where(vals>=0).dropna()
            pos=raw[raw>0]
            out['F'].append((state,len(t),len(raw),len(t)-len(raw),int((raw>0).sum()),int((raw==0).sum()),int((raw<0).sum()),sum(raw,Decimal(0)) if len(raw) else None,sum(pos,Decimal(0)) if len(pos) else None,len(pv),int((visits.isna()|visits.le(0)).sum()),quant(nn,.5),quant(nn,.9),quant(vals,.5),quant(vals,.9),quant(pv,.5)))
    mask={ 'Base Done':pd.Series(True,index=done.index),
          'Sin dq_has_problem (sensibilidad)':done.dq_has_problem.eq('False'),
          'Sin negativos/mismatch workflow':done.dq_negative_duration.eq('False') & done.dq_duration_mismatch.eq('False'),
          'Creación desde 2016':done.issue_created.ge('2016-01-01'),
          'Fechas sin flags específicos':done[['dq_invalid_issue_created','dq_invalid_issue_resolution_date','dq_naive_issue_created','dq_naive_issue_resolution_date','dq_resolution_before_creation']].eq('False').all(axis=1)}
    out['Q']=[]
    for label,m in mask.items():
        f=done.copy();f['segundos']=f.segundos.where(m);out['Q'].append((label,*stats(f)))
    out['Q_FLAGS']=[]
    cols=['dq_has_problem','dq_negative_duration','dq_duration_mismatch']
    for key,g in t.groupby(cols):
        out['Q_FLAGS'].append(tuple(v=='True' for v in key)+(len(g),int(g.segundos.notna().sum()),int((g.segundos.notna()&g.grupo.eq('Done')).sum())))
    small=t.loc[t.segundos.notna()].sort_values('segundos').drop_duplicates('segundos').head(4)
    out['P']=[(n+1,r.segundos,quant(small.segundos,.5),quant(small.segundos,.9)) for n,r in enumerate(small.itertuples())]
    long=t.loc[t.segundos.notna()].assign(id_num=lambda f:f.id.map(int)).sort_values(['segundos','id_num'],ascending=[False,True]).head(10)
    out['A_MUESTRA']=[(int(r.id),r.issue_created,r.issue_resolution_date,r.grupo,r.issue_priority,r.issue_type,r.segundos,r.segundos/86400,
                        Decimal(r.wf_total_time) if pd.notna(r.wf_total_time) else None,r.dq_has_problem=='True',r.dq_duration_mismatch=='True') for r in long.itertuples()]
    return out,cutoff


def check_results(results,expected):
    checks=[]
    for name,wanted in expected.items():
        actual=results[name][1]
        # Comparación como multiconjuntos ordenados por representación de claves; las claves
        # son los primeros 1/2/3 campos según granularidad, no los percentiles aproximados.
        nk=2 if name in ('A_EXCLUSIONES','B_TIPO','C') else 3 if name=='Q_FLAGS' else 1
        def indexed(rows):
            return {tuple(None if pd.isna(v) else v for v in row[:nk]):row for row in rows}
        a,b=indexed(actual),indexed(wanted)
        if set(a)!=set(b) or len(actual)!=len(wanted):
            raise ValueError(f'{name}: grupos/conteos de resultados distintos')
        for k,row in a.items():
            for pos,(v,w) in enumerate(zip(row,b[k])):
                if w is None or pd.isna(w):
                    match=v is None
                elif isinstance(w,pd.Timestamp):
                    match=v is not None and pd.Timestamp(v)==w
                elif name=='A_MUESTRA' and pos==8:
                    match=v is not None and Decimal(v)==w
                elif isinstance(w,(float,np.floating)):
                    # SQL PERCENTILE_CONT devuelve float(53), no DECIMAL exacto.
                    match=v is not None and math.isclose(float(v),float(w),rel_tol=1e-12,abs_tol=0.0001)
                else:
                    match=v==w
                if not match:
                    raise ValueError(f'{name}: diferencia en grupo={k}, columna={pos}: SQL={v}; Pandas={w}')
        checks.append(f'{name}: {len(actual)} grupos; conteos/denominadores exactos, sumas DECIMAL exactas, percentiles coincidentes')
    if results['S'][1][0][1:3]!=(0,0):
        raise ValueError('Fechas no UTC o precisión submicrosegundo; revisar definición temporal')
    return checks


DEFINITIONS={
 'S':('Auditoría y corte temporal','Todos los tickets. Se comprueban UTC y ausencia de fracciones menores a microsegundo; corte inferido = máximo de creación, resolución, último cambio y eventos.','El corte es una referencia observada, no una fecha de extracción certificada.'),
 'A':('Tiempo calendario hasta resolución','Cada grupo de resolución: Done exacto, otras etiquetas no nulas, y ausencia. Elegible: resolución informada, fechas presentes y fin≥inicio. Segundos=DATEDIFF_BIG(MICROSECOND)/1e6; días=segundos/86400. No se usa wf_total_time.','Una fecha almacenada no permite distinguir primera resolución de resolución final tras reaperturas. Otras resoluciones no se consideran éxito.'),
 'A_EXCLUSIONES':('Exclusiones mutuamente excluyentes','Prioridad del motivo: sin etiqueta de resolución, sin fechas, orden negativo, elegible. Los conteos suman 66.691.','No se excluye dq_has_problem por defecto. Los motivos por fecha y workflow son conceptos distintos.'),
 'B':('Tiempos por prioridad','Sólo resolución Done; población y excluidos dentro de cada prioridad, unknown separado. Mediana/P90 sólo en duraciones calendario elegibles.','Mezclar tipos y proyectos puede confundir comparaciones de prioridad; no inferir causalidad.'),
 'B_TIPO':('Prioridad segmentada por tipo','Misma definición que B, particionada adicionalmente por issue_type; se conservan todas las categorías originales.','Grupos pequeños producen percentiles inestables. No todos los tipos son incidencias ni Subtask equivale documentalmente a Sub-task.'),
 'C':('Cohortes de creación mensuales y anuales','Denominador=total de tickets creados en período; percentiles sólo Done elegibles. Se informan los no elegibles Done y las fechas de resolución ausentes por separado. Período parcial si comienza antes del primer registro o termina después del corte observado.','Período calendario completo no implica seguimiento completo. Cohortes recientes están potencialmente censuradas; sin fecha puede significar no resolución observada o dato ausente. Los cuantiles no son estimaciones de supervivencia.'),
 'D':('Reaperturas y cobertura','wfe_reopened>0 / tickets por cohorte de cobertura; eventos exactos field=status,value=reopened. Tasa de eventos / tickets con al menos un evento. Comparación sólo entre tickets con historial y agregado no NULL.','Cuenta entradas/visitas o eventos almacenados; no verifica que hubiera un cierre previo. Un cero observado no demuestra ausencia histórica de reaperturas.'),
 'D_DIFERENCIAS':('Muestra de discrepancias de reapertura','Top 20 diferencias absolutas entre conteo agregado y eventos; una fila por ticket tras preagrupar historial.','Sólo muestra de revisión, no se corrige ninguno de los dos orígenes. Ordenamiento de eventos simultáneos no establece causalidad.'),
 'E':('Eventos assignee por ticket','Historial preagrupado por issueid. Mediana y P90 entre tickets con cualquier historial, incluidos quienes tienen cero eventos assignee. Tickets sin historial excluidos de los cuantiles. Múltiples significa >1 evento.','Primeras asignaciones, valores repetidos, desasignaciones NULL y varios cambios de un grupo pueden contar como eventos; no se conocen responsables anteriores suficientes para llamarlos reasignaciones efectivas.'),
 'F':('Duración acumulada por estado','Todos los tickets por estado wf_* (excepto wf_total_time). Separar NULL, positivo, cero y negativo. Sumas firmadas y positivas; percentiles tanto firmados como no negativos. Promedio por visita=wf_estado/wfe_estado sólo con duración≥0 y visitas>0; se muestra la mediana entre tickets de ese cociente.','Los NULL no se imputan a cero. El cociente no es la media global de visitas ni reconstruye intervalos. Duración larga puede reflejar espera, calendario, diseño del flujo o agregación; no demuestra ineficiencia.'),
 'Q':('Sensibilidad del tiempo calendario Done','Población original=Done en cada escenario. Base conserva toda duración calendario elegible; escenarios contrastan flags globales, negativos/mismatch de workflow, fechas específicas o creaciones desde 2016. Excluidos=población−elegibles.','Filtros de workflow y de año se muestran como sensibilidad, no como correcciones justificadas ni población preferida automáticamente.'),
 'Q_FLAGS':('Anomalías conservadas','Conteos por combinación de dq_has_problem, dq_negative_duration y dq_duration_mismatch; se muestran elegibles calendario y Done.','Flags se solapan; los negativos de workflow no implican un intervalo creación→resolución negativo.'),
 'A_MUESTRA':('Inspección de duraciones calendario extensas','Diez intervalos calendario elegibles más largos, mostrando creación y resolución UTC, wf_total_time por separado y flags.','Muestra de revisión: no se infiere causa de los intervalos extensos ni se eliminan por su longitud. La ausencia de flags no garantiza semántica correcta.'),
 'P':('Verificación de PERCENTILE_CONT','Cuatro duraciones reales distintas más cortas; comparar interpolación lineal con Pandas. NULL ignorados por el percentil; SQL devuelve float(53).','El percentil interpolado puede no coincidir con un ticket observado. Tolerancia para cálculos aproximados: 0,0001 en unidades de salida y relativa 1e-12; conteos y sumas decimales se exigen exactos.')}


def write_report(results,checks,cutoff,hashes):
    lines=['# Análisis avanzado SQL — Fase 3.5','',f'Ejecución UTC: {datetime.now(timezone.utc).isoformat()}. Corte observado: {cutoff.isoformat()}. Sólo SELECT/CTE.', '',
    'Consultas exactas en [04_advanced_analysis.sql](../sql/04_advanced_analysis.sql); referencias por `-- QUERY: ...`. Reproducción: `python -m src.advanced_sql`. Script de sólo lectura en SQL; genera únicamente artefactos locales SQL/Markdown.', '',
    '## Definiciones y fuentes','',
    'FEATURES.md define issue_resolution_date como fecha de resolución, wf_* como segundos acumulados y wfe_* como número de visitas; los agregados provienen del histórico. EXAMPLE.md ilustra agregaciones por estado y por responsable. started/ended se describen para snapshots aunque también están en issues. Aquí no definen tiempo hasta resolución. No se unifican etiquetas ni se interpreta Done como satisfacción o cumplimiento contractual.', '',
    'Toda duración calendario incluye noches, fines de semana y pausas. No se calculan horas laborales ni SLA. Se separa Done de Won\'t Do/Duplicate/Cannot Reproduce (agregadas como otras resoluciones para comparación). No se eliminan tickets señalados globalmente. Los estados de workflow no se equiparan a resultados de negocio.', '',
    'Historial observado desde 2015, tickets desde 2007: se segmenta creación anterior/posterior al inicio de eventos, sin afirmar completitud del segundo grupo. Fecha de resolución presente no prueba historia completa. NULL legítimos permanecen y se publican denominadores.', '',
    '## Validación independiente','']
    lines += ['- SUPERADA: '+s for s in checks]
    lines+=['','Se comparan todos los grupos de A–F, sensibilidad Q, muestras y denominadores con cálculos independientes desde los CSV. PERCENTILE_CONT usa interpolación lineal y omite NULL; se contrasta con Series.quantile de Pandas. DATEDIFF_BIG en microsegundos evita el error de contar sólo fronteras de segundos; la auditoría comprobó que ninguna fecha usada pierde precisión. Días siempre equivalen a 86.400 segundos.','',
    'Huellas SHA-256 antes/después intactas: '+str(hashes), '',
    'Referencias técnicas: [PERCENTILE_CONT](https://learn.microsoft.com/en-us/sql/t-sql/functions/percentile-cont-transact-sql), [DATEDIFF_BIG](https://learn.microsoft.com/en-us/sql/t-sql/functions/datediff-big-transact-sql).','']
    for name,(headers,rows) in results.items():
        title,definition,limit=DEFINITIONS[name]
        lines+=['',f'## {name}. {title}','',f'**Consulta:** sección `{name}` del archivo SQL.','',f'**Definición y población:** {definition}','',*table(headers,rows),'',f'**Limitación:** {limit}']
    # Interpretaciones y recomendaciones derivadas del resultado actual, no de constantes históricas.
    a={r[0]:r for r in results['A'][1]}; done=a['Done']; other=a['Otras resoluciones']
    f=results['F'][1]; largest=f[0]; slow=max(f,key=lambda r:r[11] if r[11] is not None else -1)
    d=[r for r in results['D'][1] if r[0]!='Todos']; e=[r for r in results['E'][1] if r[0]!='Todos']
    scenarios={r[0]:r for r in results['Q'][1]}; recent=scenarios['Creación desde 2016']; clean=scenarios['Sin dq_has_problem (sensibilidad)']
    everyone=next(r for r in results['E'][1] if r[0]=='Todos')
    lines+=['','## Interpretación de los resultados','',
    f"- Done: {done[2]} elegibles de {done[1]}; mediana {done[6]:.4f} días y P90 {done[7]:.4f} días. Otras resoluciones: {other[2]} elegibles; mediana {other[6]:.4f} y P90 {other[7]:.4f} días. Son distribuciones de resoluciones observadas, no comparaciones ajustadas por mezcla de casos.",
    f"- Reaperturas: {sum(r[4] for r in d)} tickets con wfe_reopened positivo; {sum(r[5] for r in d)} visitas agregadas. Historial: {sum(r[6] for r in d)} tickets y {sum(r[7] for r in d)} eventos reopened; {sum(r[9] for r in d)} tickets discrepantes entre {sum(r[8] for r in d)} comparables. La discrepancia no se elimina y no puede atribuirse sólo a la cobertura sin investigar cada caso.",
    f"- Responsables: {sum(r[4] for r in e)} eventos assignee, {sum(r[6] for r in e)} tickets con más de un evento entre {sum(r[2] for r in e)} tickets con historial; {sum(r[5] for r in e)} eventos con nuevo valor NULL. No equivale automáticamente a traspasos reales.",
    f"- Mayor suma positiva acumulada: {largest[0]} ({largest[8]} s); mayor mediana no negativa entre observados: {slow[0]} ({slow[11]:.3f} s). Los rankings responden preguntas distintas y dependen de cobertura, volumen y visitas. Son candidatos a investigar, no cuellos de botella demostrados.",
    f"- Responsables, población global con historial: mediana {everyone[7]:g} y P90 {everyone[8]:g} eventos; múltiples en {everyone[9]}%. Las medianas de cohortes no se promedian para obtener la mediana global.",
    '- B y B_TIPO permiten detectar diferencias por prioridad y composición; unknown sigue separado. No atribuir diferencias a prioridad sin controlar tipo/proyecto y tamaño de muestra.',
    '- C publica meses/años parciales y días desde el fin de cada período. En períodos recientes, los tickets que aún no registran resolución no contribuyen al percentil: la mediana observada puede favorecer casos rápidos. Nunca etiquetar las cohortes recientes como completas.',
    f"- Q: creación desde 2016 conserva {recent[2]} Done y aparta {recent[3]}; mediana {recent[6]:.4f} y P90 {recent[7]:.4f} días. Excluir dq_has_problem conserva {clean[2]} y aparta {clean[3]}; mediana {clean[6]:.4f} y P90 {clean[7]:.4f} días. La cohorte temporal tiene un efecto mucho mayor que estos flags; ninguno de los filtros reemplaza la base automáticamente.",
    '- Los diez casos calendario más extensos de A_MUESTRA fueron creados en 2007 y tienen resolución en agosto de 2018, con unknown y sin dq_has_problem. Es evidencia para investigar semántica/cobertura; no prueba migración ni autoriza a corregir fechas. Los flags actuales no detectan todas las dudas de interpretación.', '',
    '## Recomendaciones para Power BI (sin implementación)','',
    '1. Tarjetas de mediana/P90 calendario Done en días junto a elegibles, excluidos y fechas ausentes. Otras resoluciones en panel separado. Mostrar definición y corte observado.',
    '2. Matriz prioridad × tipo con n, mediana y P90; unknown explícito y advertencia visual para grupos pequeños (umbral por acordar).',
    '3. Línea por cohorte mensual con mediana, P90, número elegible y porcentaje de Done observado; sombrear períodos parciales y exponer seguimiento hasta el corte. No confundir con una curva de supervivencia.',
    '4. Reaperturas en dos indicadores: visitas agregadas y eventos observados, con denominadores, cobertura y discrepancias. Desglose por creación anterior/posterior al inicio del historial.',
    '5. Histograma de eventos assignee por ticket con historial; mediana y porcentaje con múltiples eventos, llamados eventos de cambio y no reasignaciones efectivas.',
    '6. Barras por estado de suma positiva y mediana/P90 acumulada; tabla paralela de negativos y NULL. Mostrar aparte la mediana del promedio por visita, con su n elegible.',
    '7. Panel de sensibilidad y calidad: población base frente a cada filtro Q. Filtros futuros deben mostrar cuántos tickets ocultan. Antes de concluir ineficiencia, investigar reglas de estado, pausas, responsabilidad, mezcla de casos y cobertura.', '',
    '## Aprendizaje SQL y límites de ejecución','',
    'Las CTE separan población, métricas y presentación; PERCENTILE_CONT OVER(PARTITION BY...) calcula cuantiles por grupo. SELECT DISTINCT reduce la repetición de las ventanas, no deduplica tickets de origen. El historial se agrupa por issueid antes del LEFT JOIN, preservando una fila por ticket. CASE define elegibilidad, NULLIF evita dividir por cero y COUNT(segundos) cuenta sólo elegibles. CROSS APPLY VALUES transforma columnas de estados en filas para comparar distribuciones.', '',
    'Las consultas son secuenciales sin snapshot transaccional; las comparaciones SQL/CSV superadas permiten detectar diferencias en esta ejecución, sin prometer consistencia ante futuras escrituras concurrentes. No se modificaron tablas ni se crearon vistas. No hay objetivos contractuales ni calendario laboral.']
    (ROOT/'reports/sql_advanced_analysis.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')


def main():
    paths=list((ROOT/'data/raw').glob('*.csv'))+list((ROOT/'data/processed').glob('*.csv'))
    before={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    t=read_csv(ROOT/'data/processed/issues_clean.csv');e=read_csv(ROOT/'data/processed/issues_change_history_clean.csv')
    states=[c[3:] for c in t if c.startswith('wf_') and c!='wf_total_time']
    q=build_queries(states)
    for name,statement in q.items():
        if re.search(r'\b(?:INSERT|UPDATE|DELETE|DROP|TRUNCATE|ALTER|CREATE|EXEC|INTO|MERGE)\b',statement,re.I):
            raise ValueError('Se esperaba sólo SELECT/CTE')
    SQL_PATH.write_text('-- Análisis avanzado: conectar a HelpDeskAnalytics. Sólo lectura.\n'+'\n\n'.join('-- QUERY: '+k+'\n'+v for k,v in q.items())+'\n',encoding='utf-8')
    expected,cutoff=expected_results(t,e,states)
    results={}
    c=connect(database='HelpDeskAnalytics')
    try:
        cur=c.cursor()
        for name,statement in q.items():
            cur.execute(statement);results[name]=([d[0] for d in cur.description],[tuple(r) for r in cur.fetchall()])
            print(name,len(results[name][1]),'grupos',flush=True)
    finally:c.close()
    checks=check_results(results,expected)
    after={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    if before!=after:raise ValueError('Cambió un CSV durante el análisis')
    write_report(results,checks,cutoff,before)
    print('Verificaciones SQL/Pandas superadas:',len(checks))
    for k in ['A','D','E','Q']:
        print(k,results[k])
    print('F principales',results['F'][1][:5])


if __name__=='__main__':
    try:main()
    except pyodbc.Error as error:raise SystemExit(f'Error ODBC; SQLSTATE={error.args[0] if error.args else "desconocido"}')
