"""One bounded, read-only live provider experiment. Never sends notifications."""
import argparse
from contextlib import nullcontext
import importlib.metadata
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import tracker


def experiment(channel):
    diagnostic={}
    report={'channel':channel,'observed_at_utc':tracker.utc(),
            'distribution_version':importlib.metadata.version('flights'),
            'depart':'2027-01-25','return_date':'2027-04-16',
            'requested_currency':'CAD','adults':1,'cabin':'economy',
            'top_n':1,'checkout_verified':False,'diagnostic':diagnostic}
    try:
        transport=None
        if channel=='browser':
            from browser_transport import BrowserTransport
            transport=BrowserTransport()
        with transport.activate() if transport else nullcontext():
            offers=tracker.search_round_trip(report['depart'],report['return_date'],
                                             top_n=1,diagnostic=diagnostic)
        if transport:
            report['browser_events']=transport.events
        report['eligible_count']=len(offers)
        report['sample_offers']=offers[:3]
        report['outcome']='usable_live_quote' if offers else 'no_usable_quote'
        return report, 0 if offers else 1
    except Exception as exc:
        # Exception text can contain authenticated URLs; save only safe metadata.
        report.update(outcome=tracker.classify_failure(exc),error_type=type(exc).__name__)
        return report,1


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--channel',required=True,choices=['stable','upstream','browser'])
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    report,status=experiment(args.channel)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'channel':args.channel,'outcome':report['outcome']}))
    return status


if __name__=='__main__':
    raise SystemExit(main())
