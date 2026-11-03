import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import tracker
from scripts.persist_state import main, git


class PersistenceTests(unittest.TestCase):
    def test_restore_save_restore_and_non_fast_forward_protection(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp); remote=base/'remote.git'; code=base/'code'
            git('init','--bare',str(remote))
            code.mkdir(); git('init',cwd=code); git('remote','add','origin',str(remote),cwd=code)
            with tracker.init(code/'state/fares.sqlite3') as con:
                tracker.log(con,'seed','original')
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
