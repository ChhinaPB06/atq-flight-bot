import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
import tracker as t


class NotificationTests(unittest.TestCase):
    def test_delivery_dedup_drop_and_retry(self):
        with tempfile.TemporaryDirectory() as tmp, t.init(Path(tmp)/'db') as con:
            offer={'price_cad':1800,'outbound_min':1800,'inbound_min':1800,
                   'outbound':[{'number':'1'}],'return':[{'number':'2'}]}
            with patch.object(t,'send_telegram',return_value=True) as send:
                self.assertTrue(t.maybe_alert(con,'2027-01-27','2027-04-15',offer))
                self.assertFalse(t.maybe_alert(con,'2027-01-27','2027-04-15',offer))
                self.assertEqual(send.call_count,1)
                self.assertIn('Source: Fli',send.call_args.args[0])
                offer['price_cad']=1700
                self.assertTrue(t.maybe_alert(con,'2027-01-27','2027-04-15',offer))
            offer['price_cad']=1600
            with patch.object(t,'send_telegram',return_value=False):
                self.assertFalse(t.maybe_alert(con,'2027-01-27','2027-04-15',offer))
            with patch.object(t,'send_telegram',return_value=True):
                self.assertTrue(t.maybe_alert(con,'2027-01-27','2027-04-15',offer))
