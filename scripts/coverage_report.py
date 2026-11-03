"""Read-only coverage export and independent audit of stored SerpApi quotes."""
import argparse
import csv
from datetime import date, datetime, timezone, timedelta
import json
from pathlib import Path
import sqlite3
import sys
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import tracker


def audit_quote(row):
    """Recheck persisted facts without a provider request or a quota change."""
    def require(condition, reason):
        if not condition:
            raise ValueError(reason)
    quote = json.loads(row['details'])
    require(quote['currency'] == 'CAD', 'currency')
    require(quote['ticket_type'] == 'provider_round_trip_quote', 'ticket_type')
    require(row['verification'] == 'live_search_not_checkout', 'verification')
    require(type(quote['price_cad']) is int and quote['price_cad'] > 0, 'price')
    require(row['price_cad'] == quote['price_cad'], 'stored_price')
    zones = {'YYC': ZoneInfo('America/Edmonton'), 'ATQ': ZoneInfo('Asia/Kolkata')}
    for key, origin, destination, day, duration_key in (
        ('outbound', 'YYC', 'ATQ', row['depart'], 'outbound_min'),
        ('return', 'ATQ', 'YYC', row['return_date'], 'inbound_min'),
    ):
        legs = quote[key]
        require(legs and legs[0]['from'] == origin and legs[-1]['to'] == destination, 'endpoints')
        require(legs[0]['depart_at'][:10] == day, 'departure_date')
        require(all(a['to'] == b['from'] for a, b in zip(legs, legs[1:])), 'connections')
        start = datetime.fromisoformat(legs[0]['depart_at']).replace(tzinfo=zones[origin])
        end = datetime.fromisoformat(legs[-1]['arrive_at']).replace(tzinfo=zones[destination])
        elapsed = (end.astimezone(timezone.utc) - start.astimezone(timezone.utc)).total_seconds()/60
        require(type(quote[duration_key]) is int, 'duration_type')
        require(0 < elapsed <= quote[duration_key] <= 1860, 'duration')
        require(row[duration_key] == quote[duration_key], 'stored_duration')


def collect(con):
    expected = {(d.isoformat(), r.isoformat()) for d, r in tracker.date_pairs()}
    actual = {(r['depart'], r['return_date']) for r in con.execute('SELECT * FROM pairs')}
    errors = []
    observations = con.execute('''SELECT o.* FROM observations o JOIN pairs p USING(depart,return_date)
        WHERE o.source='serpapi_google_flights' ORDER BY o.id''').fetchall()
    for row in observations:
        try:
            audit_quote(row)
        except (AssertionError, KeyError, TypeError, ValueError, IndexError) as exc:
            errors.append({'observation_id': row['id'], 'error_type': type(exc).__name__,
                           'reason': str(exc) if str(exc) in {
                               'currency','ticket_type','verification','price','stored_price','endpoints',
                               'departure_date','connections','duration_type','duration','stored_duration'
                           } else 'invalid stored quote'})
    rows = []
    for pair in con.execute('''SELECT p.*,a.checked_at FROM pairs p
            LEFT JOIN api_pair_checks a USING(depart,return_date) ORDER BY p.depart,p.return_date'''):
        latest = con.execute('''SELECT * FROM observations WHERE depart=? AND return_date=?
            AND source='serpapi_google_flights' ORDER BY at_utc DESC,price_cad,id DESC LIMIT 1''',
            (pair['depart'], pair['return_date'])).fetchone()
        rows.append({'depart': pair['depart'], 'return_date': pair['return_date'],
            'nights': (date.fromisoformat(pair['return_date'])-date.fromisoformat(pair['depart'])).days,
            'last_calendar_check': pair['last_discovered'], 'last_detailed_check': pair['last_live'],
            'api_check_completed_at': pair['checked_at'], 'status': pair['live_status'],
            'provider': 'serpapi_google_flights' if pair['checked_at'] or latest else '',
            'latest_observed_price_cad': latest['price_cad'] if latest else None,
            'price_observed_at': latest['at_utc'] if latest else None,
            'outbound_minutes': latest['outbound_min'] if latest else None,
            'return_minutes': latest['inbound_min'] if latest else None,
            'confidence': 'live_search_not_checkout' if latest else 'availability_unverified',
            'checkout_verified': False, 'search_link': tracker.flight_link(pair['depart'],pair['return_date'])})
    attempted = sum(r['api_check_completed_at'] is not None for r in rows)
    now = datetime.now(timezone.utc)
    fresh = sum(bool(r['price_observed_at']) and
                now-timedelta(hours=4) <= datetime.fromisoformat(r['price_observed_at']) <= now for r in rows)
    return {'generated_at': now.isoformat(), 'integrity': con.execute('PRAGMA integrity_check').fetchone()[0],
        'expected_pairs': len(expected), 'exact_date_grid': actual == expected,
        'pairs_attempted': attempted, 'attempted_pct': round(100*attempted/len(expected),1),
        'pairs_with_observed_quotes': sum(r['latest_observed_price_cad'] is not None for r in rows),
        'pairs_with_quotes_observed_within_four_hours': fresh,
        'status_counts': {s: sum(r['status']==s for r in rows) for s in sorted({r['status'] for r in rows})},
        'stored_quotes_audited': len(observations), 'quote_validation_errors': errors,
        'coverage_kind': 'cumulative; quote timestamps are explicit; not checkout verification',
        'pairs': rows}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db',type=Path,required=True)
    parser.add_argument('--csv',type=Path,required=True)
    args=parser.parse_args()
    with sqlite3.connect(args.db.resolve().as_uri()+'?mode=ro',uri=True) as con:
        con.row_factory=sqlite3.Row
        report=collect(con)
    with args.csv.open('w',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=list(report['pairs'][0]))
        writer.writeheader();writer.writerows(report['pairs'])
    print(json.dumps(report,indent=2))
    return 0 if report['exact_date_grid'] and report['integrity']=='ok' and not report['quote_validation_errors'] else 1


if __name__=='__main__':
    raise SystemExit(main())
