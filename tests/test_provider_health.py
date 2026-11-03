import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
import tracker as t


class ProviderHealthTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.con = t.init(Path(self.tmp.name) / 'test.sqlite3')

    def tearDown(self):
        self.con.close()
        self.tmp.cleanup()

    def test_healthy_one_way_directions(self):
        probes = {key: {'returned':1} for key in ['control','outbound','return']}
        self.assertEqual(t.classify_provider_health(probes),'one_way_routes_healthy')

    def test_empty_control_is_unhealthy_not_no_flights(self):
        probes = {key: {'returned':0} for key in ['control','outbound','return']}
        self.assertEqual(t.classify_provider_health(probes),'provider_unhealthy_or_blocked')

    def test_control_good_route_empty_is_inconclusive(self):
        probes = {'control':{'returned':7},'outbound':{'returned':0},'return':{'returned':0}}
        self.assertEqual(t.classify_provider_health(probes),'control_healthy_target_inconclusive')

    def test_provider_errors_are_explicit(self):
        probes = {'control':{'error':'SearchTimeout'},'outbound':{'returned':3},'return':{'returned':3}}
        self.assertEqual(t.classify_provider_health(probes),'provider_error')

    def test_health_probe_saved(self):
        with patch.object(t,'probe_one_way',side_effect=[{'returned':12},{'returned':7},{'returned':3}]):
            report=t.run_provider_health(self.con)
        self.assertEqual(report['status'],'one_way_routes_healthy')
        self.assertEqual(self.con.execute('SELECT count(*) FROM health_checks').fetchone()[0],1)

    def test_live_empty_diagnostic_is_not_valid_quote(self):
        t.persist_live_diagnostic(self.con,'2027-01-25','2027-04-11',
            {'provider_status':'empty_response','raw_pairs':0,'eligible':0})
        self.assertEqual(self.con.execute('SELECT count(*) FROM live_diagnostics').fetchone()[0],1)
        self.assertEqual(self.con.execute("SELECT count(*) FROM observations WHERE source='fli_live'").fetchone()[0],0)

    def test_secondary_is_not_verified(self):
        t.record_secondary_quote(self.con,'2027-01-27','2027-04-15',1570)
        row=self.con.execute('SELECT verification FROM secondary_quotes').fetchone()
        self.assertEqual(row[0],'cached_unverified_no_durations')
        self.assertEqual(self.con.execute('SELECT count(*) FROM alerts').fetchone()[0],0)

    def test_fair_live_rotation(self):
        picks=t.choose_live(self.con,2)
        first=(picks[0]['depart'],picks[0]['return_date'])
        self.con.execute('UPDATE pairs SET last_live=? WHERE depart=? AND return_date=?',
            (t.utc(),*first))
        self.con.commit()
        nextp=t.choose_live(self.con,2)
        self.assertNotEqual(first,(nextp[0]['depart'],nextp[0]['return_date']))


if __name__=='__main__':unittest.main()
