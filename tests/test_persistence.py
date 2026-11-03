import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import sqlite3
from unittest.mock import patch
import tracker
from scripts.persist_state import main, git, backup


class PersistenceTests(unittest.TestCase):
    def test_corrupt_source_does_not_create_restore_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); source=root/'corrupt.db'; destination=root/'restored.db'
            source.write_bytes(b'not a SQLite database')
            with self.assertRaises(sqlite3.DatabaseError):backup(source,destination)
            self.assertFalse(destination.exists())
            self.assertEqual(list(root.glob('.flight-backup-*')),[])

    def test_failed_backup_preserves_existing_good_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); source=root/'corrupt.db'; destination=root/'restored.db'
            source.write_bytes(b'not a SQLite database')
            with tracker.init(destination) as con:tracker.log(con,'preserved','keep this history')
            before=destination.read_bytes()
            with self.assertRaises(sqlite3.DatabaseError):backup(source,destination)
            self.assertEqual(destination.read_bytes(),before)

    def test_missing_source_is_not_silently_created(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); source=root/'missing.db'; destination=root/'restored.db'
            with self.assertRaises(FileNotFoundError):backup(source,destination)
            self.assertFalse(source.exists())
            self.assertFalse(destination.exists())

    def test_empty_sqlite_file_is_not_valid_fare_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); source=root/'empty.db'; destination=root/'restored.db'
            source.touch()  # SQLite integrity_check calls this valid, despite no history schema.
            with self.assertRaisesRegex(RuntimeError,'schema is missing'):backup(source,destination)
            self.assertFalse(destination.exists())

    def test_failed_atomic_replace_keeps_prior_history_and_cleans_tempfile(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); source=root/'new.db'; destination=root/'prior.db'
            with tracker.init(source) as con:tracker.log(con,'new','new history')
            with tracker.init(destination) as con:tracker.log(con,'old','prior history')
            before=destination.read_bytes()
            with patch('scripts.persist_state.os.replace',side_effect=OSError('simulated replacement failure')):
                with self.assertRaises(OSError):backup(source,destination)
            self.assertEqual(destination.read_bytes(),before)
            self.assertEqual(list(root.glob('.flight-backup-*')),[])

    def test_restore_save_restore_and_non_fast_forward_protection(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp); remote=base/'remote.git'; code=base/'code'
            git('init','--bare',str(remote))
            code.mkdir(); git('init',cwd=code); git('remote','add','origin',str(remote),cwd=code)
            with tracker.init(code/'state/fares.sqlite3') as con:
                tracker.log(con,'seed','original')
                con.execute('CREATE TABLE serpapi_usage (at_utc TEXT NOT NULL,searches INTEGER NOT NULL)')
                con.execute("INSERT INTO serpapi_usage VALUES ('2026-11-03T00:00:00+00:00',2)")
                con.execute("INSERT INTO api_pair_checks VALUES ('2027-01-27','2027-04-20','2026-11-03T00:00:00+00:00')")
            old=Path.cwd()
            try:
                os.chdir(code)
                for iteration in range(2):
                    run=base/f'run{iteration}'; run.mkdir()
                    db=run/'db.sqlite3'
                    with patch.dict(os.environ,{'RUNNER_TEMP':str(run),'FLIGHT_DB':str(db)}):
                        main('restore')
                        with tracker.init(db) as con:
                            self.assertEqual(con.execute('SELECT COUNT(*) FROM operations').fetchone()[0],iteration+1)
                            self.assertEqual(con.execute('SELECT SUM(searches) FROM serpapi_usage').fetchone()[0],2)
                            self.assertEqual(con.execute('SELECT COUNT(*) FROM api_pair_checks').fetchone()[0],1)
                            tracker.log(con,'run',str(iteration))
                        main('save')
                        main('save')
                # A stale writer cannot overwrite a newer committed database.
                stale=base/'stale'; stale.mkdir(); newer=base/'newer'; newer.mkdir()
                for run in (stale,newer):
                    with patch.dict(os.environ,{'RUNNER_TEMP':str(run),'FLIGHT_DB':str(run/'db')}):main('restore')
                with patch.dict(os.environ,{'RUNNER_TEMP':str(newer),'FLIGHT_DB':str(newer/'db')}):
                    with tracker.init(newer/'db') as con:tracker.log(con,'new','new')
                    main('save')
                with patch.dict(os.environ,{'RUNNER_TEMP':str(stale),'FLIGHT_DB':str(stale/'db')}):
                    with tracker.init(stale/'db') as con:tracker.log(con,'stale','stale')
                    with self.assertRaises(subprocess.CalledProcessError):main('save')
            finally:
                os.chdir(old)
