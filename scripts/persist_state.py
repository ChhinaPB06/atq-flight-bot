"""Fast-forward-only SQLite persistence on flight-data, independent of code branches."""
import os
from pathlib import Path
import sqlite3
import subprocess
import sys


def git(*args, cwd=None):
    return subprocess.check_output(['git', *args], cwd=cwd, text=True).strip()


def backup(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(source) as src, sqlite3.connect(destination) as dst:
        if src.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise RuntimeError('Database integrity check failed')
        src.backup(dst)


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
