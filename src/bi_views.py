"""Diseño, despliegue conservador y validación de vistas BI. python -m src.bi_views --apply"""
import argparse
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
from pathlib import Path
import re
import sys

import pyodbc

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.clean_data import ROOT
from src.load_to_sql import contracts, inspect_tables, require, LoadError, split_batches
from src.sql_connection import connect
from src.explore_sql import table


def state_pairs(columns):
    durations={c[3:] for c in columns if c.startswith('wf_') and c!='wf_total_time'}
    visits={c[4:] for c in columns if c.startswith('wfe_')}
    require(durations==visits and bool(durations), 'Parejas wf_/wfe_ incompletas')
    return [(f'wf_{s}',f'wfe_{s}',s) for s in sorted(durations)]


def view_definitions(schema):
    ticket_flags=',\n '.join('i.['+c.name+']' for c in schema['issues'] if c.name.startswith('dq_'))
    event_audit=',\n '.join('h.['+c.name+']' for c in schema['issue_change_history'] if c.name.startswith('dq_') or c.name.endswith('__raw'))
    q={}
    q['vw_tickets']=f"""CREATE VIEW [bi].[vw_tickets] AS
WITH eventos AS (
 SELECT issueid,COUNT_BIG(*) AS cantidad_eventos,
 SUM(CONVERT(bigint,CASE WHEN field COLLATE Latin1_General_100_BIN2=N'status' AND value COLLATE Latin1_General_100_BIN2=N'reopened' THEN 1 ELSE 0 END)) AS eventos_reopened,
 SUM(CONVERT(bigint,CASE WHEN field COLLATE Latin1_General_100_BIN2=N'assignee' THEN 1 ELSE 0 END)) AS eventos_assignee
 FROM stg.issue_change_history GROUP BY issueid
), limites AS (SELECT MIN(created) AS inicio FROM stg.issue_change_history)
SELECT i.id AS ticket_id,i.issue_proj AS proyecto,i.issue_type AS tipo,i.issue_priority AS prioridad,
 i.issue_status AS estado,i.issue_resolution AS resolucion,
 CAST(SWITCHOFFSET(i.issue_created,'+00:00') AS datetime2(7)) AS creacion_utc,
 CAST(SWITCHOFFSET(i.issue_resolution_date,'+00:00') AS datetime2(7)) AS resolucion_utc,
 CAST(SWITCHOFFSET(i.issue_created,'+00:00') AS date) AS fecha_creacion_utc,
 YEAR(SWITCHOFFSET(i.issue_created,'+00:00')) AS anio_creacion,
 MONTH(SWITCHOFFSET(i.issue_created,'+00:00')) AS mes_creacion,
 DATEFROMPARTS(YEAR(SWITCHOFFSET(i.issue_created,'+00:00')),MONTH(SWITCHOFFSET(i.issue_created,'+00:00')),1) AS periodo_creacion,
 d.segundos AS intervalo_calendario_segundos,
 CASE WHEN e.elegible=1 THEN d.segundos END AS tiempo_calendario_segundos,
 CAST(CASE WHEN e.elegible=1 THEN d.segundos/86400.0 END AS decimal(28,12)) AS tiempo_calendario_dias,
 CAST(e.elegible AS bit) AS elegible_calendario,
 CAST(CASE WHEN e.elegible=1 AND i.issue_resolution COLLATE Latin1_General_100_BIN2=N'Done' THEN 1 ELSE 0 END AS bit) AS elegible_done,
 CAST(CASE WHEN e.elegible=1 AND i.issue_resolution COLLATE Latin1_General_100_BIN2<>N'Done' THEN 1 ELSE 0 END AS bit) AS elegible_otra_resolucion,
 CAST(CASE WHEN i.issue_resolution IS NULL THEN N'sin_resolucion'
 WHEN i.issue_created IS NULL OR i.issue_resolution_date IS NULL THEN N'sin_fechas'
 WHEN i.issue_resolution_date<i.issue_created THEN N'orden_negativo' ELSE N'elegible' END AS nvarchar(32)) AS motivo_elegibilidad,
 COALESCE(h.cantidad_eventos,CONVERT(bigint,0)) AS cantidad_eventos,
 COALESCE(h.eventos_reopened,CONVERT(bigint,0)) AS eventos_reopened,
 COALESCE(h.eventos_assignee,CONVERT(bigint,0)) AS eventos_assignee,
 CAST(CASE WHEN h.issueid IS NOT NULL THEN 1 ELSE 0 END AS bit) AS tiene_historial,
 CAST(SWITCHOFFSET(l.inicio,'+00:00') AS datetime2(7)) AS inicio_historial_observado_utc,
 CAST(CASE WHEN i.issue_created IS NULL OR l.inicio IS NULL THEN NULL
 WHEN i.issue_created<l.inicio THEN 1 ELSE 0 END AS bit) AS creacion_anterior_inicio_historial,
 CAST(CASE WHEN h.issueid IS NULL THEN N'Sin eventos observados'
 WHEN i.issue_created IS NULL OR l.inicio IS NULL THEN N'Cobertura temporal desconocida'
 WHEN i.issue_created<l.inicio THEN N'Creación anterior al historial'
 ELSE N'Creación desde inicio historial' END AS nvarchar(50)) AS cobertura_historica,
 i.wfe_reopened AS visitas_reopened_agregadas,
 CAST(CASE WHEN h.issueid IS NOT NULL AND i.wfe_reopened IS NOT NULL THEN 1 ELSE 0 END AS bit) AS reaperturas_comparables,
 CASE WHEN h.issueid IS NOT NULL AND i.wfe_reopened IS NOT NULL THEN i.wfe_reopened-h.eventos_reopened END AS diferencia_reopened,
 i.wf_total_time AS wf_total_time_segundos,
 {ticket_flags}
FROM stg.issues i LEFT JOIN eventos h ON h.issueid=i.id CROSS JOIN limites l
CROSS APPLY (SELECT CAST(
 CAST(DATEDIFF_BIG(SECOND,i.issue_created,i.issue_resolution_date) AS decimal(28,7))+
 CAST((DATEPART(NANOSECOND,i.issue_resolution_date)-DATEPART(NANOSECOND,i.issue_created))/1000000000.0 AS decimal(10,7))
 AS decimal(28,7)) AS segundos) d
CROSS APPLY (SELECT CASE WHEN i.issue_resolution IS NOT NULL AND i.issue_created IS NOT NULL
 AND i.issue_resolution_date>=i.issue_created THEN 1 ELSE 0 END AS elegible) e;"""
    q['vw_ticket_events']=f"""CREATE VIEW [bi].[vw_ticket_events] AS
SELECT h.id AS event_id,h.issueid AS ticket_id,h.field AS campo,h.value AS valor,
 CAST(SWITCHOFFSET(h.created,'+00:00') AS datetime2(7)) AS evento_utc,
 CAST(SWITCHOFFSET(h.created,'+00:00') AS date) AS fecha_evento_utc,
 h.change_group_id AS grupo_cambio_id,
 {event_audit}
FROM stg.issue_change_history h;"""
    pairs=state_pairs([c.name for c in schema['issues']])
    values=',\n '.join(f"(N'{s}',i.[{wf}],i.[{wfe}])" for wf,wfe,s in pairs)
    q['vw_ticket_state_durations']=f"""CREATE VIEW [bi].[vw_ticket_state_durations] AS
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
 {values}
) e(estado,duracion_segundos,numero_visitas);"""
    return q


def ddl(definitions):
    # Todos los conflictos se comprueban antes de crear ningún objeto.
    lines=['-- Ejecutar en HelpDeskAnalytics; conserva objetos existentes compatibles.', 'USE [HelpDeskAnalytics];','GO',
    "IF DB_NAME()<>N'HelpDeskAnalytics' THROW 50001,'Base incorrecta.',1;",'SET XACT_ABORT ON;']
    for n,(name,definition) in enumerate(definitions.items()):
        literal=definition.replace("'","''")
        lines += [f"DECLARE @v{n} nvarchar(max)=N'{literal}';",
        f"IF OBJECT_ID(N'bi.{name}') IS NOT NULL AND (OBJECT_ID(N'bi.{name}',N'V') IS NULL OR ISNULL(OBJECT_DEFINITION(OBJECT_ID(N'bi.{name}')),N'') COLLATE Latin1_General_100_BIN2<>@v{n} COLLATE Latin1_General_100_BIN2)",
        f"    THROW 50002,'Objeto bi.{name} existente incompatible; no se modifica.',1;"]
    lines += ['BEGIN TRANSACTION;',"IF SCHEMA_ID(N'bi') IS NULL EXEC(N'CREATE SCHEMA [bi] AUTHORIZATION [dbo]');"]
    for n,name in enumerate(definitions):
        lines += [f"IF OBJECT_ID(N'bi.{name}',N'V') IS NULL EXEC sys.sp_executesql @v{n};"]
    lines += ['COMMIT TRANSACTION;','GO']
    return '\n'.join(lines)+'\n'


def source_fingerprints(connection):
    out={}
    for name in ('issues','issue_change_history'):
        cur=connection.cursor()
        cur.execute(f"SELECT (SELECT t.* FOR JSON PATH,WITHOUT_ARRAY_WRAPPER,INCLUDE_NULL_VALUES) FROM stg.[{name}] t ORDER BY t.id")
        digest=hashlib.sha256(); count=0
        while True:
            rows=cur.fetchmany(1000)
            if not rows:break
            for row in rows:
                value=row[0].encode('utf-8');digest.update(len(value).to_bytes(8,'big'));digest.update(value);count+=1
        out[name]={'rows':count,'sha256':digest.hexdigest()};cur.close()
    return out


def preflight(connection,definitions):
    actions={}
    cur=connection.cursor()
    for name,definition in definitions.items():
        obj=cur.execute('SELECT type FROM sys.objects WHERE object_id=OBJECT_ID(?)','bi.'+name).fetchone()
        if obj:
            existing=cur.execute('SELECT OBJECT_DEFINITION(OBJECT_ID(?))','bi.'+name).fetchone()[0]
            require(obj[0].strip()=='V' and existing==definition,f'Objeto bi.{name} incompatible; no se modifica')
            actions[name]='Existente compatible'
        else:actions[name]='Creada'
    return actions


def validate(connection,schema):
    from src.advanced_sql import BASE
    cur=connection.cursor(); checks=[]
    def check(label,condition):
        require(bool(condition),label);checks.append(label)
    for name,expected,key in [('vw_tickets',66691,'ticket_id'),('vw_ticket_events',257508,'event_id'),('vw_ticket_state_durations',66691*20,None)]:
        count=cur.execute(f'SELECT COUNT_BIG(*) FROM bi.[{name}]').fetchone()[0]
        check(name+' cantidad',count==expected)
        if key:
            distinct=cur.execute(f'SELECT COUNT_BIG(DISTINCT [{key}]) FROM bi.[{name}]').fetchone()[0]
            check(name+' clave única/no NULL',count==distinct)
    for name in ('vw_ticket_events','vw_ticket_state_durations'):
        missing=cur.execute(f'SELECT COUNT_BIG(*) FROM bi.[{name}] e LEFT JOIN bi.vw_tickets t ON t.ticket_id=e.ticket_id WHERE t.ticket_id IS NULL').fetchone()[0]
        check(name+' integridad referencial',missing==0)
    dupe=cur.execute('SELECT COUNT_BIG(*) FROM (SELECT ticket_id,estado FROM bi.vw_ticket_state_durations GROUP BY ticket_id,estado HAVING COUNT_BIG(*)<>1) x').fetchone()[0]
    check('Clave ticket/estado única',dupe==0)
    # EXCEPT bidireccional, sin JOIN que multiplique los tickets.
    pairs=state_pairs([c.name for c in schema['issues']])
    vals=','.join(f"(N'{s}',i.[{a}],i.[{b}])" for a,b,s in pairs)
    original=f'SELECT i.id,e.* FROM stg.issues i CROSS APPLY (VALUES {vals}) e(estado,duracion_segundos,numero_visitas)'
    projected='SELECT ticket_id,estado,duracion_segundos,numero_visitas FROM bi.vw_ticket_state_durations'
    for a,b in [(original,projected),(projected,original)]:
        check('Parejas y valores exactos estados',cur.execute(f'SELECT COUNT_BIG(*) FROM ({a} EXCEPT {b}) x').fetchone()[0]==0)
    eventcols=[c.name for c in schema['issue_change_history'] if c.name.startswith('dq_') or c.name.endswith('__raw')]
    expected='SELECT id,issueid,field,value,CAST(SWITCHOFFSET(created,\'+00:00\') AS datetime2(7)) AS created_utc,change_group_id,'+','.join('['+x+']' for x in eventcols)+' FROM stg.issue_change_history'
    actual='SELECT event_id,ticket_id,campo,valor,evento_utc,grupo_cambio_id,'+','.join('['+x+']' for x in eventcols)+' FROM bi.vw_ticket_events'
    for a,b in [(expected,actual),(actual,expected)]:
        check('Eventos, NULL y auditoría exactos',cur.execute(f'SELECT COUNT_BIG(*) FROM ({a} EXCEPT {b}) x').fetchone()[0]==0)
    mismatch=cur.execute('''SELECT COUNT_BIG(*) FROM bi.vw_tickets v JOIN stg.issues i ON i.id=v.ticket_id
     WHERE EXISTS (SELECT v.proyecto,v.tipo,v.prioridad,v.estado,v.resolucion,v.creacion_utc,v.resolucion_utc
     EXCEPT SELECT i.issue_proj,i.issue_type,i.issue_priority,i.issue_status,i.issue_resolution,
     CAST(SWITCHOFFSET(i.issue_created,'+00:00') AS datetime2(7)),CAST(SWITCHOFFSET(i.issue_resolution_date,'+00:00') AS datetime2(7)))''').fetchone()[0]
    check('Atributos y fechas UTC de tickets intactos',mismatch==0)
    flags=[c.name for c in schema['issues'] if c.name.startswith('dq_')]
    flags_select=','.join('v.['+c+']' for c in flags); flag_orig=','.join('i.['+c+']' for c in flags)
    check('Todos los dq de tickets intactos',cur.execute(f'SELECT COUNT_BIG(*) FROM bi.vw_tickets v JOIN stg.issues i ON i.id=v.ticket_id WHERE EXISTS(SELECT {flags_select} EXCEPT SELECT {flag_orig})').fetchone()[0]==0)
    check('Eventos preagrupados por ticket exactos',cur.execute('''WITH h AS (
      SELECT issueid,COUNT_BIG(*) AS n,SUM(CONVERT(bigint,CASE WHEN field COLLATE Latin1_General_100_BIN2=N'status' AND value COLLATE Latin1_General_100_BIN2=N'reopened' THEN 1 ELSE 0 END)) AS r,
      SUM(CONVERT(bigint,CASE WHEN field COLLATE Latin1_General_100_BIN2=N'assignee' THEN 1 ELSE 0 END)) AS a FROM stg.issue_change_history GROUP BY issueid)
      SELECT COUNT_BIG(*) FROM bi.vw_tickets v LEFT JOIN h ON h.issueid=v.ticket_id
      WHERE v.cantidad_eventos<>COALESCE(h.n,0) OR v.eventos_reopened<>COALESCE(h.r,0) OR v.eventos_assignee<>COALESCE(h.a,0)
      OR CONVERT(int,v.tiene_historial)<>CASE WHEN h.issueid IS NULL THEN 0 ELSE 1 END''').fetchone()[0]==0)
    check('Elegibilidad y calendario contra Fase 3.5',cur.execute(f''';WITH {BASE}
      SELECT COUNT_BIG(*) FROM base b JOIN bi.vw_tickets v ON v.ticket_id=b.id
      WHERE CONVERT(int,v.elegible_calendario)<>CASE WHEN b.segundos IS NOT NULL THEN 1 ELSE 0 END
      OR (b.segundos IS NOT NULL AND (ABS(b.segundos-v.tiempo_calendario_segundos)>0.0000001 OR ABS(b.segundos/86400.0-v.tiempo_calendario_dias)>0.00000001))
      OR (b.segundos IS NULL AND (v.tiempo_calendario_segundos IS NOT NULL OR v.tiempo_calendario_dias IS NOT NULL))
      OR CONVERT(int,v.elegible_done)<>CASE WHEN b.grupo=N'Done' AND b.segundos IS NOT NULL THEN 1 ELSE 0 END
      OR CONVERT(int,v.elegible_otra_resolucion)<>CASE WHEN b.grupo=N'Otras resoluciones' AND b.segundos IS NOT NULL THEN 1 ELSE 0 END''').fetchone()[0]==0)
    check('Negativos/NULL/cero/no recorrido consistentes',cur.execute('''SELECT COUNT_BIG(*) FROM bi.vw_ticket_state_durations
      WHERE CONVERT(int,indicador_duracion_negativa)<>CASE WHEN duracion_segundos<0 THEN 1 ELSE 0 END
      OR CONVERT(int,duracion_faltante)<>CASE WHEN duracion_segundos IS NULL THEN 1 ELSE 0 END
      OR CONVERT(int,duracion_cero)<>CASE WHEN duracion_segundos=0 THEN 1 ELSE 0 END
      OR CONVERT(int,estado_no_recorrido)<>CASE WHEN numero_visitas=0 AND duracion_segundos IS NULL THEN 1 ELSE 0 END
      OR CONVERT(int,estado_recorrido)<>CASE WHEN numero_visitas>0 THEN 1 ELSE 0 END
      OR CONVERT(int,elegible_duracion_no_negativa)<>CASE WHEN duracion_segundos>=0 THEN 1 ELSE 0 END
      OR CONVERT(int,elegible_promedio_visita)<>CASE WHEN duracion_segundos>=0 AND numero_visitas>0 THEN 1 ELSE 0 END
      OR (elegible_promedio_visita=1 AND ABS(promedio_por_visita_segundos-CONVERT(float,duracion_segundos)/numero_visitas)>0.00001)
      OR (elegible_promedio_visita=0 AND promedio_por_visita_segundos IS NOT NULL)
      OR (duracion_segundos IS NOT NULL AND CONVERT(decimal(38,16),duracion_segundos_exacta)<>duracion_segundos)
      OR (duracion_segundos IS NULL AND duracion_segundos_exacta IS NOT NULL)''').fetchone()[0]==0)
    statistics={}
    statistics['tickets']=[tuple(r) for r in cur.execute('''SELECT COUNT_BIG(*) AS tickets,SUM(CONVERT(bigint,elegible_done)) AS done,
      SUM(CONVERT(bigint,elegible_otra_resolucion)) AS otras,SUM(CONVERT(bigint,tiene_historial)) AS con_historial,
      SUM(eventos_reopened) AS reopened,SUM(eventos_assignee) AS assignee,
      SUM(CONVERT(bigint,CASE WHEN eventos_assignee>1 THEN 1 ELSE 0 END)) AS multiples,
      SUM(CONVERT(bigint,CASE WHEN reaperturas_comparables=1 AND diferencia_reopened<>0 THEN 1 ELSE 0 END)) AS discrepancias
      FROM bi.vw_tickets''').fetchall()]
    check('Resumen Fase 3.5',statistics['tickets'][0]==(66691,62034,3804,66650,2325,62706,16791,39))
    percent=cur.execute('''SELECT DISTINCT PERCENTILE_CONT(0.5) WITHIN GROUP(ORDER BY tiempo_calendario_dias) OVER(),
       PERCENTILE_CONT(0.9) WITHIN GROUP(ORDER BY tiempo_calendario_dias) OVER()
       FROM bi.vw_tickets WHERE elegible_done=1''').fetchone()
    check('Mediana y P90 Done Fase 3.5',abs(percent[0]-35.86748263888889)<1e-6 and abs(percent[1]-2858.352345961806)<1e-6)
    statistics['percentiles_done_dias']=list(percent)
    statistics['estados']=[tuple(r) for r in cur.execute('''SELECT estado,COUNT_BIG(*) AS tickets,COUNT_BIG(duracion_segundos) AS observados,
      SUM(CONVERT(bigint,indicador_duracion_negativa)) AS negativos,SUM(CONVERT(bigint,duracion_cero)) AS ceros,
      SUM(CONVERT(bigint,estado_no_recorrido)) AS no_recorridos FROM bi.vw_ticket_state_durations GROUP BY estado ORDER BY estado''').fetchall()]
    check('55 tickets con negativos conservados',cur.execute('SELECT COUNT_BIG(DISTINCT ticket_id) FROM bi.vw_ticket_state_durations WHERE indicador_duracion_negativa=1').fetchone()[0]==55)
    # Tipos y columnas reales para el diccionario, sin inferir desde CSV.
    metadata=[tuple(r) for r in cur.execute('''SELECT o.name,c.name,t.name,c.max_length,c.precision,c.scale,c.is_nullable
      FROM sys.columns c JOIN sys.objects o ON o.object_id=c.object_id JOIN sys.types t ON t.user_type_id=c.user_type_id
      WHERE o.schema_id=SCHEMA_ID(N'bi') AND o.name IN (N'vw_tickets',N'vw_ticket_events',N'vw_ticket_state_durations')
      ORDER BY o.name,c.column_id''').fetchall()]
    cur.close();return checks,statistics,metadata


def file_hashes():
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'data').glob('*/*.csv'))}


def deploy(connection,schema,definitions):
    inspect_tables(connection,schema,empty=False)
    cur=connection.cursor()
    actual=[r[0] for r in cur.execute("SELECT name FROM sys.columns WHERE object_id=OBJECT_ID(N'stg.issues') ORDER BY column_id").fetchall()]
    require(state_pairs(actual)==state_pairs([c.name for c in schema['issues']]),'Parejas reales diferentes al contrato')
    actions=preflight(connection,definitions)
    before=source_fingerprints(connection)
    sql=ddl(definitions)
    # No hay ALTER/CREATE OR ALTER: todos los objetos se inspeccionan antes de crear faltantes.
    cur.execute('SET XACT_ABORT ON; BEGIN TRANSACTION;')
    try:
        cur.execute("IF SCHEMA_ID(N'bi') IS NULL EXEC(N'CREATE SCHEMA [bi] AUTHORIZATION [dbo]')")
        for name,definition in definitions.items():
            if actions[name]=='Creada':cur.execute(definition)
        checks,stats,metadata=validate(connection,schema)
        after=source_fingerprints(connection)
        require(before==after,'Huella stg cambió durante el despliegue')
        cur.execute('COMMIT TRANSACTION;')
    except BaseException:
        cur.execute('IF @@TRANCOUNT>0 ROLLBACK TRANSACTION;');raise
    finally:cur.close()
    return actions,checks,stats,metadata,before


def main(apply=False):
    schema=contracts(); definitions=view_definitions(schema)
    (ROOT/'sql/05_bi_views.sql').write_text(ddl(definitions),encoding='utf-8')
    if not apply:
        print('SQL generado. Usar --apply para preflight, creación y validación.');return
    before=file_hashes()
    c=connect(database='HelpDeskAnalytics')
    try:actions,checks,stats,metadata,fingerprints=deploy(c,schema,definitions)
    finally:c.close()
    require(before==file_hashes(),'CSV modificados')
    # El texto de diseño se conserva en un recurso versionado separado del resultado generado.
    design=(ROOT/'reports/bi_data_model_design.md').read_text(encoding='utf-8')
    lines=[design,'','## Ejecución y validación real','',f'UTC: {datetime.now(timezone.utc).isoformat()}. COMMIT del DDL confirmado.','']
    lines += ['- '+name+': '+action for name,action in actions.items()]
    lines += ['']+['- SUPERADA: '+check for check in checks]
    lines += ['','Huellas SHA-256 de todas las filas/columnas stg (JSON ordenado por PK) idénticas antes y después: '+str(fingerprints),
      '','Huellas de CSV intactas: '+str(before),'','Resumen tickets: '+str(stats['tickets'])+'. Orden: total, Done elegibles, otras elegibles, con historial, eventos reopened, eventos assignee, múltiples assignee, discrepancias reopened.',
      '', 'Mediana/P90 Done en días: '+str(stats['percentiles_done_dias']), '',
      *table(['Estado','Filas','Duración no NULL','Negativos','Ceros','No recorridos'],stats['estados']),
      '', '## Diccionario de columnas real','',
      'La nulabilidad de catálogo de una vista puede ser conservadora; claves y condiciones se validan sobre los valores. NVARCHAR mide unidades UTF-16; las fechas con sufijo _utc son UTC sin offset.', '']
    for name in definitions:
        rows=[]
        for view,col,typ,length,p,s,null in metadata:
            if view!=name:continue
            kind=typ.upper()+ (f'({length//2})' if typ=='nvarchar' else f'({p},{s})' if typ in ('decimal','numeric') else f'({s})' if typ=='datetime2' else '')
            rows.append((col,kind,'sí' if null else 'no'))
        lines+=['',f'### bi.{name}','',*table(['Columna','Tipo SQL','Nullable catálogo'],rows)]
    (ROOT/'reports/bi_data_model.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('Vistas confirmadas:',actions);print('Validaciones:',len(checks));print('Resumen:',stats)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    try:main(args.apply)
    except pyodbc.Error as error:raise SystemExit(f'Error ODBC SQLSTATE={error.args[0] if error.args else "desconocido"}')
