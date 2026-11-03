import tempfile
from pathlib import Path
import unittest
import tracker as t


class ScopeMigrationTests(unittest.TestCase):
    def test_old_pair_archived_observation_preserved_and_migration_repeatable(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'history.db'
            with t.init(path) as con:
                con.execute("INSERT INTO pairs(depart,return_date) VALUES ('2027-01-25','2027-04-16')")
                con.execute("INSERT INTO observations(at_utc,depart,return_date,price_cad,source,verification,details) VALUES ('2026-11-03','2027-01-25','2027-04-16',2304,'serpapi_google_flights','live_search_not_checkout','{}')")
                con.commit()
            for _ in range(2):
                with t.init(path) as con:
                    self.assertEqual(con.execute('SELECT COUNT(*) FROM pairs').fetchone()[0],54)
                    self.assertEqual(con.execute('SELECT COUNT(*) FROM archived_pairs').fetchone()[0],1)
                    self.assertEqual(con.execute('SELECT COUNT(*) FROM observations').fetchone()[0],1)
                    self.assertEqual(con.execute("SELECT COUNT(*) FROM pairs WHERE return_date>'2027-04-30'").fetchone()[0],0)
