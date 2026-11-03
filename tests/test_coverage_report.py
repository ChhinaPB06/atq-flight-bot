"""Audit stored data independently; these fixtures are synthetic, not live fares."""
import json
from contextlib import redirect_stdout
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import tracker
from scripts.coverage_report import collect,main


class CoverageReportTests(unittest.TestCase):
    def test_all_54_pairs_exported_without_inventing_checks_or_prices(self):
        with tempfile.TemporaryDirectory() as tmp, tracker.init(Path(tmp)/'db') as con:
            report=collect(con)
            self.assertTrue(report['exact_date_grid'])
            self.assertEqual(len(report['pairs']),54)
            self.assertEqual(report['pairs_attempted'],0)
            self.assertEqual(report['pairs_with_observed_quotes'],0)
            self.assertEqual(report['pairs_with_current_usable_quotes'],0)
            self.assertEqual(report['status_counts'],{'not_checked':54})
            self.assertEqual([sum(r['depart']==f'2027-01-{day}' for r in report['pairs'])
                              for day in range(27,32)], [11,11,11,11,10])

    def test_persisted_quote_rechecked_and_corruption_detected(self):
        quote={'currency':'CAD','ticket_type':'provider_round_trip_quote','price_cad':2200,
            'outbound_min':1110,'inbound_min':810,'source':'serpapi_google_flights',
            'outbound':[{'from':'YYC','to':'ATQ','depart_at':'2027-01-27 12:00',
                         'arrive_at':'2027-01-28 18:00'}],
            'return':[{'from':'ATQ','to':'YYC','depart_at':'2027-04-20 12:00',
                       'arrive_at':'2027-04-20 14:00'}]}
        with tempfile.TemporaryDirectory() as tmp, tracker.init(Path(tmp)/'db') as con:
            tracker.record_live(con,'2027-01-27','2027-04-20',[quote])
            report=collect(con)
            self.assertEqual(report['stored_quotes_audited'],1)
            self.assertEqual(report['quote_validation_errors'],[],str(report['quote_validation_errors']))
            self.assertEqual(report['pairs_with_observed_quotes'],1)
            self.assertEqual(report['pairs_with_validated_observed_quotes'],1)
            self.assertEqual(report['pairs_with_current_usable_quotes'],1)
            # Database fields still claim 810min; independently detect altered endpoints.
            quote['return'][0]['arrive_at']='2027-04-22 14:00'
            con.execute('UPDATE observations SET details=?',(json.dumps(quote),))
            report=collect(con)
            self.assertEqual(len(report['quote_validation_errors']),1)
            self.assertEqual(report['pairs_with_validated_observed_quotes'],0)
            self.assertEqual(report['pairs_with_current_usable_quotes'],0)
            self.assertEqual(report['pairs_with_quotes_observed_within_four_hours'],0)
            pair=next(r for r in report['pairs'] if r['depart']=='2027-01-27'
                      and r['return_date']=='2027-04-20')
            self.assertEqual(pair['latest_observed_price_cad'],2200)
            self.assertIsNone(pair['current_usable_price_cad'])
            self.assertEqual(pair['confidence'],'stored_quote_invalid')

    def test_prior_quote_is_historical_after_new_empty_attempt(self):
        quote={'currency':'CAD','ticket_type':'provider_round_trip_quote','price_cad':2200,
            'outbound_min':1110,'inbound_min':810,'source':'serpapi_google_flights',
            'outbound':[{'from':'YYC','to':'ATQ','depart_at':'2027-01-27 12:00',
                         'arrive_at':'2027-01-28 18:00'}],
            'return':[{'from':'ATQ','to':'YYC','depart_at':'2027-04-20 12:00',
                       'arrive_at':'2027-04-20 14:00'}]}
        with tempfile.TemporaryDirectory() as tmp, tracker.init(Path(tmp)/'db') as con:
            tracker.record_live(con,'2027-01-27','2027-04-20',[quote])
            tracker.record_live(con,'2027-01-27','2027-04-20',[])
            report=collect(con)
            pair=next(r for r in report['pairs'] if r['depart']=='2027-01-27'
                      and r['return_date']=='2027-04-20')
            self.assertEqual(report['pairs_with_observed_quotes'],1)
            self.assertEqual(report['pairs_with_validated_observed_quotes'],1)
            self.assertEqual(report['pairs_with_current_usable_quotes'],0)
            self.assertEqual(pair['latest_observed_price_cad'],2200)
            self.assertIsNone(pair['current_usable_price_cad'])
            self.assertEqual(pair['confidence'],'historical_live_search_not_current_attempt')

    def test_naive_observation_time_is_an_audit_failure_not_a_report_crash(self):
        with tempfile.TemporaryDirectory() as tmp, tracker.init(Path(tmp)/'db') as con:
            con.execute('''INSERT INTO observations
                (at_utc,depart,return_date,price_cad,source,verification,details)
                VALUES ('2026-11-03T12:00:00','2027-01-27','2027-04-20',2200,
                'serpapi_google_flights','live_search_not_checkout','{}')''')
            report=collect(con)
            self.assertEqual(report['quote_validation_errors'][0]['reason'],'observation_time')
            self.assertEqual(report['pairs_with_quotes_observed_within_four_hours'],0)

    def test_empty_grid_returns_structured_failure_without_creating_pairs(self):
        with tempfile.TemporaryDirectory() as tmp:
            database=Path(tmp)/'db';output=Path(tmp)/'empty.csv'
            with tracker.init(database) as con:
                con.execute('DELETE FROM pairs');con.commit()
                captured=io.StringIO()
                with patch('sys.argv',['coverage_report','--db',str(database),'--csv',str(output)]),redirect_stdout(captured):
                    self.assertEqual(main(),1)
                report=json.loads(captured.getvalue())
                self.assertFalse(report['exact_date_grid'])
                self.assertEqual(report['pairs'],[])
                self.assertEqual(con.execute('SELECT COUNT(*) FROM pairs').fetchone()[0],0)


if __name__=='__main__':
    unittest.main()
