import tempfile
from pathlib import Path
import unittest
import io
from contextlib import redirect_stdout
from unittest.mock import patch
import tracker as t


class ApiScannerTests(unittest.TestCase):
    def test_records_provider_source_and_diagnostics(self):
        with tempfile.TemporaryDirectory() as tmp,t.init(Path(tmp)/'db') as con:
            offer={'price_cad':2304,'outbound_min':1810,'inbound_min':1702,
                   'outbound':[],'return':[],'source':'serpapi_google_flights'}
            with patch('providers.serpapi.Client') as client,patch.object(t,'maybe_alert'):
                client.return_value.search.return_value=([offer],{'return_rows':4})
                t.run_api(con)
            row=con.execute('SELECT source,price_cad FROM observations').fetchone()
            self.assertEqual(row['source'],'serpapi_google_flights')
            self.assertEqual(row['price_cad'],2304)
            self.assertEqual(con.execute('SELECT status FROM live_diagnostics').fetchone()[0],'eligible_found')

    def test_rejected_nonempty_is_not_empty_response(self):
        with tempfile.TemporaryDirectory() as tmp,t.init(Path(tmp)/'db') as con:
            with patch('providers.serpapi.Client') as client:
                client.return_value.search.return_value=([],{'return_rows':4})
                with self.assertRaisesRegex(RuntimeError,'SCAN DEGRADED'):t.run_api(con)
            self.assertEqual(con.execute('SELECT status FROM live_diagnostics').fetchone()[0],'all_rejected')

    def test_empty_provider_data_is_explicitly_unverified(self):
        with tempfile.TemporaryDirectory() as tmp,t.init(Path(tmp)/'db') as con:
            with patch('providers.serpapi.Client') as client:
                client.return_value.search.return_value=([],{'return_rows':0})
                with self.assertRaisesRegex(RuntimeError,'SCAN DEGRADED'):t.run_api(con)
            self.assertEqual(con.execute("SELECT live_status FROM pairs WHERE last_live IS NOT NULL").fetchone()[0],'provider_empty_unverified')

    def test_provider_error_does_not_starve_other_unchecked_pairs(self):
        from providers.serpapi import ProviderAccessError
        with tempfile.TemporaryDirectory() as tmp,t.init(Path(tmp)/'db') as con:
            attempted=[]
            def fail(_con,depart,back,**kwargs):
                attempted.append((depart,back))
                raise ProviderAccessError('Provider access failed')
            with patch('providers.serpapi.Client') as client:
                client.return_value.search.side_effect=fail
                for _ in range(2):
                    with self.assertRaisesRegex(RuntimeError,'API scan failed'):t.run_api(con)
            self.assertEqual(len(set(attempted)),2)
            self.assertEqual(con.execute('SELECT COUNT(*) FROM api_pair_checks').fetchone()[0],0)

    def test_rejected_nonempty_outbounds_are_not_provider_empty(self):
        with tempfile.TemporaryDirectory() as tmp,t.init(Path(tmp)/'db') as con:
            report={'status':'no_usable_outbound','outbound_rows':3,
                    'outbound_rejection_reasons':{'duration_limit':3}}
            with patch('providers.serpapi.Client') as client:
                client.return_value.search.return_value=([],report)
                with self.assertRaisesRegex(RuntimeError,'SCAN DEGRADED'):t.run_api(con)
            self.assertEqual(con.execute('SELECT status FROM live_diagnostics').fetchone()[0],'all_rejected')
            self.assertEqual(con.execute('SELECT live_status FROM pairs WHERE last_live IS NOT NULL').fetchone()[0],'no_eligible_itinerary')

    def test_failed_refresh_clears_current_price_but_preserves_history(self):
        from providers.serpapi import ProviderAccessError
        with tempfile.TemporaryDirectory() as tmp,t.init(Path(tmp)/'db') as con:
            pair=('2027-01-27','2027-04-17')
            offer={'price_cad':2300,'outbound_min':1800,'inbound_min':1800,
                   'outbound':[],'return':[],'source':'serpapi_google_flights'}
            t.record_live(con,*pair,[offer])
            con.execute('UPDATE pairs SET last_live=?',(t.utc(),))
            con.execute("UPDATE pairs SET last_live='2020-01-01T00:00:00+00:00' WHERE depart=? AND return_date=?",pair)
            con.executemany('INSERT INTO api_pair_checks VALUES (?,?,?)',
                [(d.isoformat(),r.isoformat(),t.utc()) for d,r in t.date_pairs()]);con.commit()
            with patch('providers.serpapi.Client') as client:
                client.return_value.search.side_effect=ProviderAccessError('Provider access failed')
                with self.assertRaisesRegex(RuntimeError,'API scan failed'):t.run_api(con)
            row=con.execute('SELECT live_price,live_status FROM pairs WHERE depart=? AND return_date=?',pair).fetchone()
            self.assertIsNone(row['live_price'])
            self.assertEqual(row['live_status'],'api_failure')
            self.assertEqual(con.execute('SELECT COUNT(*) FROM observations').fetchone()[0],1)

    def test_idle_run_is_audited_without_provider_traffic(self):
        with tempfile.TemporaryDirectory() as tmp,t.init(Path(tmp)/'db') as con:
            con.executemany('INSERT INTO api_pair_checks VALUES (?,?,?)',
                [(d.isoformat(),r.isoformat(),t.utc()) for d,r in t.date_pairs()])
            con.execute('UPDATE pairs SET last_live=?',(t.utc(),));con.commit()
            with patch('providers.serpapi.Client') as client,redirect_stdout(io.StringIO()) as output:
                t.run_api(con)
            client.assert_not_called()
            self.assertIn('SCAN IDLE',output.getvalue())
            self.assertEqual(con.execute("SELECT COUNT(*) FROM operations WHERE kind='scan_idle'").fetchone()[0],1)

    def test_malformed_return_data_is_parser_error_not_constraint_rejection(self):
        with tempfile.TemporaryDirectory() as tmp,t.init(Path(tmp)/'db') as con:
            report={'status':'no_usable_return','outbound_rows':3,'return_rows':2,
                    'return_rejection_reasons':{'parser_error':2}}
            with patch('providers.serpapi.Client') as client:
                client.return_value.search.return_value=([],report)
                with self.assertRaisesRegex(RuntimeError,'SCAN DEGRADED'):t.run_api(con)
            self.assertEqual(con.execute('SELECT status FROM live_diagnostics').fetchone()[0],'parser_error')
            self.assertEqual(con.execute('SELECT live_status FROM pairs WHERE last_live IS NOT NULL').fetchone()[0],'parser_error')
