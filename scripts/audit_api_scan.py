"""Audit one real scanner run; credentials are never included in output."""
import json
import os
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import tracker

report={'source':'serpapi_google_flights','checkout_verified':False}
with tracker.init() as con:
    report['observations_before']=con.execute('SELECT COUNT(*) FROM observations').fetchone()[0]
    try:
        tracker.run_api(con)
        report['status']='scan_completed'
    except Exception as exc:
        report.update(status='scan_failed',error_type=type(exc).__name__)
    report['observations_after']=con.execute('SELECT COUNT(*) FROM observations').fetchone()[0]
    report['date_pairs']=con.execute('SELECT COUNT(*) FROM pairs').fetchone()[0]
    report['api_reserved_searches']=con.execute('SELECT COALESCE(SUM(searches),0) FROM serpapi_usage').fetchone()[0]
    report['integrity']=con.execute('PRAGMA integrity_check').fetchone()[0]
    report['latest_diagnostic']=dict(con.execute('SELECT * FROM live_diagnostics ORDER BY id DESC LIMIT 1').fetchone() or {})
    report['recent_api_prices']=[dict(r) for r in con.execute("SELECT depart,return_date,price_cad,outbound_min,inbound_min,source,verification FROM observations WHERE source='serpapi_google_flights' ORDER BY id DESC LIMIT 5")]
output=Path(sys.argv[1]);output.parent.mkdir(parents=True,exist_ok=True)
output.write_text(json.dumps(report,indent=2)+'\n')
raise SystemExit(0 if report['status']=='scan_completed' and report['observations_after']>report['observations_before'] else 1)
