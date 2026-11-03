"""Publish sanitized JSON to an independent evidence branch, fast-forward only."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
from persist_state import git


def main(source):
    root=Path.cwd();target=Path(os.environ['RUNNER_TEMP'])/'ci-evidence-git'
    target.mkdir(exist_ok=False);git('init',cwd=target)
    git('remote','add','origin',git('remote','get-url','origin'),cwd=target)
    git('config','include.path',str(root/'.git/config'),cwd=target)
    if git('ls-remote','--heads','origin','refs/heads/flight-provider-evidence',cwd=target):
        git('fetch','--depth=1','origin','flight-provider-evidence',cwd=target)
        git('checkout','-b','flight-provider-evidence','FETCH_HEAD',cwd=target)
    else:git('checkout','--orphan','flight-provider-evidence',cwd=target)
    run=os.environ['GITHUB_RUN_ID']+'-'+os.environ['GITHUB_RUN_ATTEMPT']
    output=target/'runs'/run;output.mkdir(parents=True,exist_ok=False)
    for path in Path(source).glob('*.json'):shutil.copyfile(path,output/path.name)
    (output/'publisher-commit.txt').write_text(os.environ['GITHUB_SHA']+'\n')
    git('config','user.name','github-actions[bot]',cwd=target)
    git('config','user.email','41898282+github-actions[bot]@users.noreply.github.com',cwd=target)
    git('add','runs',cwd=target);git('commit','-m','Record CI inspection '+run,cwd=target)
    git('push','origin','HEAD:refs/heads/flight-provider-evidence',cwd=target)


if __name__=='__main__':main(sys.argv[1])
