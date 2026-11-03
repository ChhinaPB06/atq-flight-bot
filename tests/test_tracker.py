import tempfile
import unittest
from pathlib import Path
from datetime import date
from unittest.mock import patch
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import tracker as t

class TestTracker(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.conn=t.init(Path(self.tmp.name)/'db.sqlite3')
    def tearDown(self):
        self.conn.close();self.tmp.cleanup()
    def test_complete_date_pairs(self):
        ps=t.date_pairs()
        self.assertEqual(len(ps),216)
        self.assertEqual(len(set(ps)),216)
        self.assertTrue(all(60<=(r-d).days<=90 and r<=date(2027,4,30) for d,r in ps))
        self.assertTrue(any(d.isoformat()=='2027-01-27' and r.isoformat()=='2027-04-15' for d,r in ps))
    def test_strict_duration(self):
        self.assertTrue(t.valid_itinerary(1600,1860,1860))
        self.assertFalse(t.valid_itinerary(1400,1861,1400))
        self.assertFalse(t.valid_itinerary(1400,1000,None))
        self.assertFalse(t.valid_itinerary(0,1000,900))
    def test_full_rotation_with_no_quotes(self):
        stays=[]
        for i in range(16):
            batch=t.choose_stays(self.conn,2)
            stays.extend(batch)
            for s in batch:t.record_discovery(self.conn,s,{})
        self.assertEqual(set(stays),set(range(60,91)))
        self.assertEqual(self.conn.execute('SELECT COUNT(*) FROM pairs WHERE last_discovered IS NOT NULL').fetchone()[0],216)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM pairs WHERE discovery_status='no_quote'").fetchone()[0],216)
    def test_quote_recording_and_selection(self):
        key=('2027-01-27','2027-04-15')
        t.record_discovery(self.conn,78,{key:1550})
        self.assertEqual(self.conn.execute('SELECT discovery_price FROM pairs WHERE depart=? AND return_date=?',key).fetchone()[0],1550)
        self.assertTrue(any((x['depart'],x['return_date'])==key for x in t.choose_live(self.conn,3)))
    def test_bootstrap_without_calendar_quotes(self):
        picks=t.choose_live(self.conn,1)
        self.assertEqual((picks[0]["depart"],picks[0]["return_date"]),("2027-01-27","2027-04-15"))
    def test_live_filter_unknown_and_overlimit(self):
        class Fake:
            def __init__(self,price,duration):self.price=price;self.duration=duration;self.legs=[]
        self.assertFalse(t.valid_itinerary(*[t.flight_info(Fake(1500,1861))['price'],1861,1800]))
    def test_alert_never_claims_checkout(self):
        item={'price_cad':1500,'outbound_min':1500,'inbound_min':1550,'outbound':[],'return':[]}
        with patch.object(t,'send_telegram',return_value=True) as send:
            self.assertTrue(t.maybe_alert(self.conn,'2027-01-27','2027-04-15',item))
            self.assertFalse(t.maybe_alert(self.conn,'2027-01-27','2027-04-15',item))
            self.assertIn('NOT CHECKOUT VERIFIED',send.call_args.args[0])

if __name__=='__main__':unittest.main()
