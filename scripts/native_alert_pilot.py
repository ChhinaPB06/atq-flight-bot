"""Import one approved .eml or explicitly verify its event. No mailbox/network on import."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import tracker
from signals.native_email import import_export,verify_event,NativeAlertError

p=argparse.ArgumentParser()
p.add_argument('--db',type=Path,required=True)
sub=p.add_subparsers(dest='command',required=True)
i=sub.add_parser('import');i.add_argument('eml',type=Path)
v=sub.add_parser('verify');v.add_argument('event_id',type=int)
args=p.parse_args()
try:
    with tracker.init(args.db) as con:
        report=import_export(con,args.eml.read_bytes()) if args.command=='import' else verify_event(con,args.event_id)
    print(json.dumps(report,indent=2))
    if report['status'] in ('verification_failed','quota_deferred'):raise SystemExit(1)
except Exception as exc:
    failure={'status':'failed','error_type':type(exc).__name__}
    if isinstance(exc,NativeAlertError):failure['safe_reason']=str(exc)
    print(json.dumps(failure))
    raise SystemExit(1) from None
