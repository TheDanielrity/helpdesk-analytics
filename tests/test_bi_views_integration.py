"""Integración real de sólo lectura: HELPDESK_BI_INTEGRATION=1."""
from decimal import Decimal,localcontext
import os
import unittest

import pandas as pd

from src.bi_views import preflight,view_definitions
from src.clean_data import ROOT,read_csv
from src.load_to_sql import contracts
from src.sql_connection import connect


@unittest.skipUnless(os.environ.get('HELPDESK_BI_INTEGRATION')=='1','Integración SQL opcional, sólo SELECT')
class BIIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.connection=connect(database='HelpDeskAnalytics')
        cls.frame=read_csv(ROOT/'data/processed/issues_clean.csv')

    @classmethod
    def tearDownClass(cls):cls.connection.close()

    def test_filtered_percentiles_against_pandas(self):
        f=self.frame
        seconds=(pd.to_datetime(f.issue_resolution_date,utc=True,format='ISO8601')-pd.to_datetime(f.issue_created,utc=True,format='ISO8601')).dt.total_seconds()
        done=f.issue_resolution.eq('Done') & seconds.ge(0)
        cases=[("prioridad=?",('unknown',),f.issue_priority.eq('unknown')),
               ("prioridad=? AND tipo=? AND anio_creacion>=2016",('Medium','Ticket'),f.issue_priority.eq('Medium')&f.issue_type.eq('Ticket')&pd.to_datetime(f.issue_created,utc=True,format='ISO8601').dt.year.ge(2016)),
               ("dq_has_problem=1",(),f.dq_has_problem.eq('True'))]
        for where,parameters,mask in cases:
            query=f'''SELECT DISTINCT COUNT_BIG(*) OVER(),
             PERCENTILE_CONT(0.5) WITHIN GROUP(ORDER BY tiempo_calendario_dias) OVER(),
             PERCENTILE_CONT(0.9) WITHIN GROUP(ORDER BY tiempo_calendario_dias) OVER()
             FROM bi.vw_tickets WHERE elegible_done=1 AND {where}'''
            row=self.connection.cursor().execute(query,*parameters).fetchone()
            values=seconds.loc[done&mask]/86400
            self.assertEqual(row[0],len(values))
            self.assertAlmostEqual(row[1],values.quantile(.5),places=8)
            self.assertAlmostEqual(row[2],values.quantile(.9),places=8)

    def test_long_states_exact_sums_and_missing_values(self):
        rows=self.connection.cursor().execute('''SELECT estado,COUNT_BIG(*),COUNT_BIG(duracion_segundos),
         SUM(CONVERT(bigint,indicador_duracion_negativa)),SUM(CONVERT(bigint,duracion_cero)),SUM(CONVERT(bigint,estado_no_recorrido)),
         CONVERT(varchar(50),SUM(duracion_segundos)) FROM bi.vw_ticket_state_durations GROUP BY estado''').fetchall()
        self.assertEqual(len(rows),20)
        with localcontext() as context:
            context.prec=50
            for state,total,observed,negative,zero,unvisited,signed in rows:
                original=self.frame['wf_'+state]; visits=self.frame['wfe_'+state]
                numbers=original.dropna().map(Decimal)
                self.assertEqual(total,len(self.frame))
                self.assertEqual(observed,len(numbers))
                self.assertEqual(negative,int(numbers.lt(0).sum()))
                self.assertEqual(zero,int(numbers.eq(0).sum()))
                self.assertEqual(unvisited,int((original.isna()&visits.eq('0')).sum()))
                self.assertEqual(Decimal(signed),sum(numbers,Decimal(0)))

    def test_creation_cohorts_and_history(self):
        f=self.frame
        dates=pd.to_datetime(f.issue_created,utc=True,format='ISO8601')
        expected=dates.dt.strftime('%Y-%m').value_counts().to_dict()
        rows=self.connection.cursor().execute('SELECT anio_creacion,mes_creacion,COUNT_BIG(*) FROM bi.vw_tickets GROUP BY anio_creacion,mes_creacion').fetchall()
        self.assertEqual({f'{year:04d}-{month:02d}':n for year,month,n in rows},expected)
        row=self.connection.cursor().execute('''SELECT COUNT_BIG(*),SUM(CONVERT(bigint,creacion_anterior_inicio_historial)),
          SUM(CONVERT(bigint,CASE WHEN resolucion IS NULL THEN 1 ELSE 0 END)),
          SUM(CONVERT(bigint,CASE WHEN prioridad=N'unknown' THEN 1 ELSE 0 END)),
          SUM(CONVERT(bigint,CASE WHEN tiene_historial=0 AND cantidad_eventos=0 THEN 1 ELSE 0 END)) FROM bi.vw_tickets''').fetchone()
        self.assertEqual(tuple(row),(66691,20222,853,33965,41))

    def test_deployed_definitions_reused_without_ddl(self):
        result=preflight(self.connection,view_definitions(contracts()))
        self.assertTrue(all(v=='Existente compatible' for v in result.values()))


if __name__=='__main__':unittest.main()
