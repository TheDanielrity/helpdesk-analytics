"""Pruebas de DDL conservador y granularidad sin conexión SQL."""
import unittest
from unittest.mock import MagicMock

from src.bi_views import state_pairs, view_definitions, ddl, preflight
from src.load_to_sql import contracts, LoadError, split_batches


class BIViewsTests(unittest.TestCase):
    def test_pairs_complete_and_total_not_a_state(self):
        pairs=state_pairs([c.name for c in contracts()['issues']])
        self.assertEqual(len(pairs),20)
        self.assertTrue(all(a=='wf_'+s and b=='wfe_'+s for a,b,s in pairs))
        self.assertNotIn('wf_total_time',[p[0] for p in pairs])
        with self.assertRaises(LoadError):state_pairs(['wf_open','wfe_closed'])

    def test_preaggregation_and_legitimate_nulls(self):
        definitions=view_definitions(contracts())
        tickets=definitions['vw_tickets'];events=definitions['vw_ticket_events'];states=definitions['vw_ticket_state_durations']
        self.assertIn('GROUP BY issueid',tickets)
        self.assertIn('LEFT JOIN eventos h ON h.issueid=i.id',tickets)
        self.assertIn("SWITCHOFFSET(i.issue_created,'+00:00')",tickets)
        self.assertNotIn('COALESCE(i.issue_resolution',tickets)
        self.assertNotIn('COALESCE(h.value',events)
        self.assertNotIn('wf_total_time',states)
        self.assertNotIn('WHERE',states)
        self.assertIn('e.numero_visitas=0 AND e.duracion_segundos IS NULL',states)
        self.assertIn('NULLIF(e.numero_visitas,0)',states)
        for text in definitions.values():
            self.assertNotIn('PERCENTILE_CONT',text)
            self.assertNotIn('WHERE dq_has_problem',text)

    def test_conflict_refused_before_creation(self):
        connection=MagicMock()
        connection.cursor.return_value.execute.return_value.fetchone.side_effect=[('V',),('CREATE VIEW different',)]
        with self.assertRaises(LoadError):preflight(connection,{'vw_tickets':'CREATE VIEW expected'})
        calls=[c.args[0] for c in connection.cursor.return_value.execute.call_args_list]
        self.assertTrue(all(q.startswith('SELECT') for q in calls))

    def test_identical_view_reused(self):
        connection=MagicMock()
        connection.cursor.return_value.execute.return_value.fetchone.side_effect=[('V',),('CREATE VIEW expected',)]
        self.assertEqual(preflight(connection,{'vw_tickets':'CREATE VIEW expected'}),{'vw_tickets':'Existente compatible'})

    def test_ddl_batches_and_no_mutations_to_tables(self):
        text=ddl(view_definitions(contracts()))
        self.assertEqual(len(split_batches(text)),2)
        for word in ('DROP ','ALTER ','TRUNCATE ','DELETE ','UPDATE ','INSERT '):
            self.assertNotIn(word,text.upper())
        self.assertLess(text.index('THROW 50002'),text.index('BEGIN TRANSACTION'))

    def test_tsql_parser(self):
        from sqlfluff.core import FluffConfig,Linter
        config=FluffConfig(configs={'core':{'dialect':'tsql','templater':'raw'}})
        definitions=view_definitions(contracts())
        for text in list(definitions.values())+split_batches(ddl(definitions)):
            result=Linter(config=config).parse_string(text)
            self.assertFalse(result.violations,str(result.violations))


if __name__=='__main__':unittest.main()
