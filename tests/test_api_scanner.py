import tempfile
from pathlib import Path
import unittest
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
