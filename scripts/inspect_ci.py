"""Read authorized CI evidence and credential presence; never export secret values."""
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

REPO='ChhinaPB06/atq-flight-bot'


def command(args):
    return subprocess.run(args,capture_output=True,timeout=90)


def inspect_run(run):
    result=command(['gh','api',f'repos/{REPO}/actions/runs/{run}/logs'])
    report={'run_id':run,'log_fetch_exit':result.returncode,'health':[],'live':[]}
    if result.returncode:return report
    with zipfile.ZipFile(io.BytesIO(result.stdout)) as archive:
        for name in archive.namelist():
            if not name.endswith('.txt'):continue
            text=archive.read(name).decode(errors='replace')
            for line in text.splitlines():
                for marker,key in [('PROVIDER HEALTH ','health'),('LIVE DIAGNOSTIC ','live')]:
                    if marker not in line:continue
                    try: data=json.loads(line.split(marker,1)[1])
                    except ValueError:continue
                    if key=='health':
                        data={'status':data.get('status'),'probes':{k:{f:v.get(f) for f in ('route','returned','error')} for k,v in data.get('probes',{}).items()}}
                    else:
                        data={k:data.get(k) for k in ('depart','return_date','raw_pairs','eligible','rejected','provider_status')}
                    if data not in report[key]:report[key].append(data)
    return report


def review():
    existing=command(['gh','pr','list','--repo',REPO,'--head','fix/roundtrip-provider-persistence','--base','main','--state','open','--json','url'])
    if existing.returncode:return {'outcome':'list_denied','exit_code':existing.returncode}
    prs=json.loads(existing.stdout)
    if prs:return {'outcome':'exists','url':prs[0]['url']}
    result=command(['gh','pr','create','--repo',REPO,'--draft','--base','main','--head','fix/roundtrip-provider-persistence','--title','Repair provider validation and durable flight history','--body-file','PR_DESCRIPTION.md'])
    if not result.returncode:return {'outcome':'created','url':result.stdout.decode().strip()}
    error=result.stderr.decode(errors='replace').lower()
    category='unclassified_creation_failure'
    if 'not permitted to create or approve pull requests' in error:category='repository_disallows_actions_pr_creation'
    elif 'resource not accessible by integration' in error:category='token_scope_denied'
    elif 'forbidden' in error:category='forbidden'
    return {'outcome':category,'exit_code':result.returncode}


if __name__=='__main__':
    report={'credential_presence':{name:bool(os.getenv(name)) for name in (
        'AMADEUS_CLIENT_ID','AMADEUS_CLIENT_SECRET','TRAVELPAYOUTS_TOKEN')},
        'historical_runs':[inspect_run(run) for run in (41573652801,41574283529,41574548188)],
        'pull_request':review()}
    output=Path(sys.argv[1]);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
