import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as S
from unittest.mock import patch
import tracker as t
from scripts.persist_state import backup


def flight(origin, dest, day, currency='CAD', price=2200):
    return S(price=price, duration=1800, currency=currency, legs=[S(
        departure_airport=origin, arrival_airport=dest, departure_datetime=day+'T10:00',
        arrival_datetime=day+'T20:00', airline='AC', flight_number=1)])


class ValidationTests(unittest.TestCase):
    def test_identity_and_currency_rejection(self):
        for origin, day, currency, reason in [
            ('YYC','2027-01-27','USD','currency_unverified_or_not_cad'),
            ('JFK','2027-01-27','CAD','route_or_date_mismatch'),
            ('YYC','2027-01-28','CAD','route_or_date_mismatch')]:
            report={}
            offers=t.classify_round_trip_results([(flight(origin,'ATQ',day,currency),
                flight('ATQ','YYC','2027-04-15'))],report,'2027-01-27','2027-04-15')
            self.assertEqual(offers,[])
            self.assertEqual(report['rejected'][reason],1)

    def test_above_threshold_persists_and_roundtrip_not_summed(self):
        report={}
        offers=t.classify_round_trip_results([(flight('YYC','ATQ','2027-01-27'),
            flight('ATQ','YYC','2027-04-15',price=2500))],report,'2027-01-27','2027-04-15')
        self.assertEqual(offers[0]['price_cad'],2200)
        with tempfile.TemporaryDirectory() as tmp:
            db=Path(tmp)/'source.db'; dst=Path(tmp)/'copy.db'
            con=t.init(db)
            t.record_live(con,'2027-01-27','2027-04-15',offers)
            backup(db,dst); backup(db,dst)
            with t.init(dst) as restored:
                self.assertEqual(restored.execute('SELECT price_cad FROM observations').fetchone()[0],2200)
            con.close()

    def test_health_failure_stops_provider_traffic(self):
        with tempfile.TemporaryDirectory() as tmp, t.init(Path(tmp)/'db') as con:
            with patch.object(t,'run_provider_health',return_value={'status':'provider_error'}), patch.object(t,'discover_stay') as search:
                with self.assertRaisesRegex(RuntimeError,'SCAN DEGRADED'):t.run(con,pause=0)
                search.assert_not_called()

    def test_failed_attempt_rotates_and_counts(self):
        with tempfile.TemporaryDirectory() as tmp, t.init(Path(tmp)/'db') as con:
            first=dict(t.choose_live(con,1)[0])
            with patch.object(t,'run_provider_health',return_value={'status':'one_way_routes_healthy'}), patch.object(t,'search_round_trip',side_effect=ValueError('shape')):
                with self.assertRaisesRegex(RuntimeError,'SCAN DEGRADED'):t.run(con,calendar_per_run=0,live_per_run=1,pause=0)
            self.assertNotEqual(dict(t.choose_live(con,1)[0]),first)
            self.assertEqual(con.execute('SELECT status FROM live_diagnostics').fetchone()[0],'parser_error')
