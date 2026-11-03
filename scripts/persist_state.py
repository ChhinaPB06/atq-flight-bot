"""Fast-forward-only SQLite persistence on flight-data, independent of code branches."""
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
from contextlib import closing


def git(*args, cwd=None):
    return subprocess.check_output(['git', *args], cwd=cwd, text=True).strip()


def backup(source, destination):
    source, destination = Path(source), Path(destination)
    if not source.is_file():
        raise FileNotFoundError('SQLite backup source does not exist')
    if source.resolve() == destination.resolve():
        raise ValueError('SQLite backup source and destination must differ')
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        # A missing source must never become a new empty SQLite database.
        with closing(sqlite3.connect(source.resolve().as_uri()+'?mode=ro', uri=True)) as src:
            if src.execute('PRAGMA integrity_check').fetchall() != [('ok',)]:
                raise RuntimeError('Database integrity check failed')
            tables={r[0] for r in src.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if not {'pairs','observations'}.issubset(tables):
                raise RuntimeError('History database schema is missing; refusing an empty reset')
            with tempfile.NamedTemporaryFile(prefix='.flight-backup-', dir=destination.parent,
                                             delete=False) as handle:
                temporary = Path(handle.name)
            with closing(sqlite3.connect(temporary)) as dst:
                src.backup(dst)
                if dst.execute('PRAGMA integrity_check').fetchall() != [('ok',)]:
                    raise RuntimeError('Backup database integrity check failed')
        # Replace only after the complete, validated backup has closed. A failed
        # restore leaves neither a new empty destination nor a damaged old one.
        with temporary.open('rb') as handle:
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main(mode):
    root = Path.cwd()
    data = Path(os.environ['RUNNER_TEMP']) / 'flight-data'
    database = Path(os.environ['FLIGHT_DB'])
    if mode == 'restore':
        data.mkdir(exist_ok=False)
        git('init', cwd=data)
        git('remote', 'add', 'origin', git('remote', 'get-url', 'origin'), cwd=data)
        # Include checkout's scoped Git configuration by path, without reading,
        # copying, or passing authentication headers through command arguments.
        config_path = Path(git('rev-parse', '--git-path', 'config')).resolve()
        git('config', 'include.path', str(config_path), cwd=data)
        heads = git('ls-remote', '--heads', 'origin', 'refs/heads/flight-data', cwd=data)
        if heads:
            git('fetch', '--depth=1', 'origin', 'flight-data', cwd=data)
            git('checkout', '-b', 'flight-data', 'FETCH_HEAD', cwd=data)
            if not (data/'fares.sqlite3').is_file():
                raise RuntimeError('Existing data branch has no database; refusing reset')
            backup(data/'fares.sqlite3', database)
        else:
            git('checkout', '--orphan', 'flight-data', cwd=data)
            backup(root/'state/fares.sqlite3', database)
    elif mode == 'save':
        backup(database, data/'fares.sqlite3')
        git('config', 'user.name', 'github-actions[bot]', cwd=data)
        git('config', 'user.email', '41898282+github-actions[bot]@users.noreply.github.com', cwd=data)
        git('add', 'fares.sqlite3', cwd=data)
        changed = subprocess.run(['git','diff','--cached','--quiet'], cwd=data).returncode
        if changed:
            git('commit', '-m', 'Persist flight scan history', cwd=data)
            # No force push and no binary merge. A racing writer fails visibly.
            git('push', 'origin', 'HEAD:refs/heads/flight-data', cwd=data)
    else:
        raise ValueError(mode)


if __name__ == '__main__':
    main(sys.argv[1])
