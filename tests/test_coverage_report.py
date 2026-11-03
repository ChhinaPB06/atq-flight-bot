"""Audit stored data independently; these fixtures are synthetic, not live fares."""
import json
from pathlib import Path
import tempfile
import unittest

import tracker
from scripts.coverage_report import collect


class CoverageReportTests(unittest.TestCase):
    def test_all_54_pairs_exported_without_inventing_checks_or_prices(self):
        with tempfile.TemporaryDirectory() as tmp, tracker.init(Path(tmp)/'db') as con:
            report=collect(con)
            self.assertTrue(report['exact_date_grid'])
            self.assertEqual(len(report['pairs']),54)
            self.assertEqual(report['pairs_attempted'],0)
            self.assertEqual(report['pairs_with_observed_quotes'],0)
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
            # Database fields still claim 810min; independently detect altered endpoints.
            quote['return'][0]['arrive_at']='2027-04-22 14:00'
            con.execute('UPDATE observations SET details=?',(json.dumps(quote),))
            report=collect(con)
            self.assertEqual(len(report['quote_validation_errors']),1)


if __name__=='__main__':
    unittest.main()
