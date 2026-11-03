"""One zero-spend-gated API experiment; no alerts or booking."""
import json
import os
from pathlib import Path
import sqlite3
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from providers.serpapi import Client

report={'provider':'serpapi_google_flights','checkout_verified':False,'outcome':'unrun'}
if not os.getenv('SERPAPI_API_KEY'):
    report['outcome']='credential_missing'
else:
    try:
        client=Client()
        with sqlite3.connect(os.environ['FLIGHT_DB']) as con:
            offers,diagnostic=client.search(con,'2027-01-25','2027-04-16')
        report.update(outcome='candidate_quotes_require_live_review' if offers else 'no_usable_quote',
                      diagnostic=diagnostic,sample_offers=offers[:3])
    except Exception as exc:
        report.update(outcome='blocked_or_failed',error_type=type(exc).__name__)
        report['account_metadata']=getattr(locals().get('client'),'account_metadata',{})
        from providers.serpapi import ProviderAccessError, BudgetExhausted, ProviderDataError
        if isinstance(exc,(ProviderAccessError,BudgetExhausted,ProviderDataError)):
            report['safe_reason']=str(exc)
output=Path(sys.argv[1]);output.parent.mkdir(parents=True,exist_ok=True)
output.write_text(json.dumps(report,indent=2)+'\n')
raise SystemExit(1)  # candidate integration is not independently live-validated yet
