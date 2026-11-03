"""Free-first personal flight tracker. No scraping/checkout promises; Fli unofficial source.

Dependency `flights` (https://github.com/punitarani/fli) is imported only in live modes.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import sqlite3
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
DB = Path(os.getenv('FLIGHT_DB', str(ROOT / 'state' / 'fares.sqlite3')))
DEP = [date(2027,1,d) for d in (25,26,27,28,29,30,31)]
TARGET = 1600
ALERT = 1900
MAX_MINS = 31*60
END = date(2027,4,30)


def utc(): return datetime.now(timezone.utc).isoformat(timespec='seconds')


def date_pairs():
    """All 60-90-night stays, excluding returns after April 30, 2027."""
    return [(d, d+timedelta(days=n)) for d in DEP for n in range(60,91) if d+timedelta(days=n)<=END]


def init(path=DB):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.row_factory=sqlite3.Row
    con.executescript('''
    CREATE TABLE IF NOT EXISTS pairs (depart TEXT NOT NULL, return_date TEXT NOT NULL,
      last_discovered TEXT, discovery_price INTEGER, discovery_status TEXT NOT NULL DEFAULT 'not_checked',
      last_live TEXT, live_price INTEGER, live_status TEXT NOT NULL DEFAULT 'not_checked',
      PRIMARY KEY(depart,return_date));
    CREATE TABLE IF NOT EXISTS observations (id INTEGER PRIMARY KEY, at_utc TEXT NOT NULL,
      depart TEXT NOT NULL, return_date TEXT NOT NULL, price_cad INTEGER NOT NULL,
      outbound_min INTEGER, inbound_min INTEGER, source TEXT NOT NULL,
      verification TEXT NOT NULL, details TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS alerts (fingerprint TEXT PRIMARY KEY, price_cad INTEGER NOT NULL,
      last_alert_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS operations (id INTEGER PRIMARY KEY, at_utc TEXT NOT NULL,
      kind TEXT NOT NULL, detail TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
    ''')
    con.executemany('INSERT OR IGNORE INTO pairs(depart,return_date) VALUES(?,?)',
                    [(d.isoformat(), r.isoformat()) for d,r in date_pairs()])
    con.commit(); return con


def log(con, kind, detail):
    con.execute('INSERT INTO operations(at_utc,kind,detail) VALUES(?,?,?)',(utc(),kind,str(detail)[:2000]))
    con.commit()


def valid_price(x):
    try:
        f=float(x)
        return round(f) if f>0 and f<100000 else None
    except (TypeError,ValueError):return None


def valid_itinerary(price, out_min, back_min):
    return valid_price(price) is not None and all(isinstance(x,(int,float)) and 0<x<=MAX_MINS for x in (out_min,back_min))


def flight_link(d,r):
    # Generic search link, not guaranteed to reproduce an offer.
    return 'https://www.google.com/travel/flights?'+urlencode({'q':f'Flights from Calgary to Amritsar departing {d} returning {r}'})


def send_telegram(message):
    token=os.getenv('TELEGRAM_BOT_TOKEN',''); chat=os.getenv('TELEGRAM_CHAT_ID','')
    if not token or not chat:
        print('TELEGRAM NOT CONFIGURED; message:\n'+message)
        return False
    data=json.dumps({'chat_id':chat,'text':message,'disable_web_page_preview':True}).encode()
    req=Request(f'https://api.telegram.org/bot{token}/sendMessage',data=data,
                headers={'Content-Type':'application/json'})
    with urlopen(req,timeout=20) as res:
        payload=json.load(res)
    if not payload.get('ok'): raise RuntimeError('Telegram rejected message')
    return True


def _airport_code(obj):
    return getattr(obj,'value',str(obj))


def flight_info(f):
    """Use provider's total itinerary duration; do NOT sum segment flying times."""
    price=valid_price(getattr(f,'price',None))
    duration=getattr(f,'duration',None)
    try: duration=int(duration)
    except (ValueError,TypeError):duration=None
    legs=getattr(f,'legs',[]) or []
    flights=[]
    for l in legs:
        flights.append({'airline':_airport_code(getattr(l,'airline','?')),
                        'number':str(getattr(l,'flight_number','?')),
                        'from':_airport_code(getattr(l,'departure_airport','?')),
                        'to':_airport_code(getattr(l,'arrival_airport','?')),
                        'depart_at':str(getattr(l,'departure_datetime','')),
                        'arrive_at':str(getattr(l,'arrival_datetime',''))})
    return {'price':price,'duration':duration,'legs':flights}


def _fli():
    try:
        from fli.search import SearchDates, SearchFlights
        from fli.models import Airport, FlightSegment, PassengerInfo, DateSearchFilters, FlightSearchFilters, TripType, SeatType, SortBy
    except ImportError as e:
        raise RuntimeError('Install free Fli library: pip install -r requirements.txt') from e
    return locals()


def _seg(models,orig,dest,travel_date):
    Airport=models['Airport']
    def a(code):
        try: return getattr(Airport,code)
        except AttributeError: return Airport(code)
    return models['FlightSegment'](departure_airport=[[a(orig),0]],
        arrival_airport=[[a(dest),0]],travel_date=travel_date)


def discover_stay(stay):
    """One flexible-date request for seven departures with the given stay length.

    Fli calendar is discovery only, and may not list every fare.
    """
    m=_fli()
    fs=[_seg(m,'YYC','ATQ','2027-01-27'),_seg(m,'ATQ','YYC','2027-04-12')]
    filt=m['DateSearchFilters'](trip_type=m['TripType'].ROUND_TRIP,
        passenger_info=m['PassengerInfo'](adults=1),flight_segments=fs,
        from_date='2027-01-25',to_date='2027-01-31',duration=stay,
        seat_type=m['SeatType'].ECONOMY)
    found=m['SearchDates']().search(filt, currency='CAD', language='en-CA', country='CA') or []
    result={}
    for item in found:
        dates=getattr(item,'date',None)
        if not dates or len(dates)<2:continue
        d=dates[0].date() if isinstance(dates[0],datetime) else dates[0]
        r=dates[1].date() if isinstance(dates[1],datetime) else dates[1]
        if isinstance(d,str):
            try:d=date.fromisoformat(d[:10])
            except ValueError:continue
        if isinstance(r,str):
            try:r=date.fromisoformat(r[:10])
            except ValueError:continue
        if not isinstance(d,date) or not isinstance(r,date):continue
        pair=(d.isoformat(),r.isoformat())
        if pair not in {(a.isoformat(), b.isoformat()) for a, b in date_pairs()}:continue
        p=valid_price(getattr(item,'price',None))
        if p is not None and (pair not in result or p<result[pair]):result[pair]=p
    return result


def search_round_trip(d,r, top_n=3):
    """Live *search* offers, not final seller checkout prices.

    Fli README documents tuples (outbound, return) and outbound.price as total.
    """
    m=_fli()
    filt=m['FlightSearchFilters'](trip_type=m['TripType'].ROUND_TRIP,
        passenger_info=m['PassengerInfo'](adults=1),
        flight_segments=[_seg(m,'YYC','ATQ',d),_seg(m,'ATQ','YYC',r)],
        seat_type=m['SeatType'].ECONOMY,sort_by=m['SortBy'].CHEAPEST)
    # Expand up to top_n outbound candidates to obtain paired return itineraries.
    result=m['SearchFlights']().search(filt, top_n=top_n, currency='CAD', language='en-CA', country='CA') or []
    out=[]
    for pair in list(result):
        if not isinstance(pair,(tuple,list)) or len(pair)!=2: continue
        a,b=flight_info(pair[0]),flight_info(pair[1])
        # Fli current docs describe outbound.price as total RT fare.
        total=a['price']
        if not valid_itinerary(total,a['duration'],b['duration']):continue
        out.append({'price_cad':total,'outbound_min':a['duration'],
                    'inbound_min':b['duration'],'outbound':a['legs'],'return':b['legs']})
    return out


def record_discovery(con,stay,found):
    now=utc()
    checked=0
    for d,r in date_pairs():
        if (r-d).days!=stay:continue
        key=(d.isoformat(),r.isoformat()); price=found.get(key)
        con.execute('''UPDATE pairs SET last_discovered=?, discovery_price=?, discovery_status=?
            WHERE depart=? AND return_date=?''',
            (now,price,'price_observed' if price is not None else 'no_quote',*key))
        if price is not None:
            con.execute('''INSERT INTO observations(at_utc,depart,return_date,price_cad,
                source,verification,details) VALUES(?,?,?,?,?,?,?)''',
                (now,*key,price,'fli_calendar','cached_or_calendar',json.dumps({'stay':stay})))
        checked+=1
    con.commit();return checked


def choose_stays(con,per_run):
    # Each duration is checked in increasing order of oldest coverage. This eventually
    # sweeps ALL 60-90 stays, even when calendar results are empty.
    result=[]
    for stay in range(60,91):
        d=DEP[0];r=d+timedelta(days=stay)
        row=con.execute('SELECT MIN(last_discovered) AS last FROM pairs WHERE return_date=DATE(depart, ?)',
                        (f'+{stay} days',)).fetchone()
        result.append((row['last'] or '',abs(stay-78),stay))
    result.sort();return [i[2] for i in result[:per_run]]


def choose_live(con,limit):
    """Prioritize low calendar quotes; bootstrap live searches without calendar data."""
    query = """SELECT * FROM pairs WHERE
        (last_live IS NULL OR last_live < datetime('now','-24 hours'))
        ORDER BY CASE WHEN discovery_price IS NOT NULL AND discovery_price<=? THEN 0
                      WHEN discovery_price IS NOT NULL THEN 1 ELSE 2 END,
        CASE WHEN depart='2027-01-27' THEN 0 ELSE 1 END,
        ABS(julianday(return_date)-julianday('2027-04-15')),
        COALESCE(last_live,''), COALESCE(discovery_price,999999)
        LIMIT ?"""
    return con.execute(query,(ALERT,limit)).fetchall()


def record_live(con,d,r,offers):
    now=utc();best=min((x['price_cad'] for x in offers),default=None)
    con.execute('UPDATE pairs SET last_live=?,live_price=?,live_status=? WHERE depart=? AND return_date=?',
                (now,best,'verified_itinerary' if offers else 'no_eligible_itinerary',d,r))
    for x in offers:
        con.execute('''INSERT INTO observations(at_utc,depart,return_date,price_cad,
            outbound_min,inbound_min,source,verification,details) VALUES(?,?,?,?,?,?,?,?,?)''',
            (now,d,r,x['price_cad'],x['outbound_min'],x['inbound_min'],'fli_live',
             'live_search_not_checkout',json.dumps(x)))
    con.commit()


def maybe_alert(con,d,r,offer):
    p=offer['price_cad']
    if p>ALERT:return False
    flights=offer['outbound']+offer['return']
    key=hashlib.sha256(json.dumps([d,r,flights],sort_keys=True).encode()).hexdigest()[:28]
    old=con.execute('SELECT price_cad FROM alerts WHERE fingerprint=?',(key,)).fetchone()
    if old and p>old['price_cad']-100:return False
    msg=(f"{'🎯 TARGET' if p<=TARGET else '✈️ DEAL'}: Calgary ↔ Amritsar CAD ${p} (LIVE SEARCH, NOT CHECKOUT VERIFIED)\n"
         f"Depart: {d} | Return: {r} | Stay {(date.fromisoformat(r)-date.fromisoformat(d)).days} nights\n"
         f"Travel: outbound {offer['outbound_min']/60:.1f}h, return {offer['inbound_min']/60:.1f}h (max 31h each)\n"
         f"Book/search: {flight_link(d,r)}\n"
         f"Observed (UTC): {utc()}\n"
         "Verify exact itinerary, checked bags, transit visas and TOTAL FINAL CHECKOUT PRICE before paying.")
    delivered=send_telegram(msg)
    if delivered:
        con.execute('INSERT OR REPLACE INTO alerts(fingerprint,price_cad,last_alert_at) VALUES(?,?,?)',(key,p,utc()));con.commit()
    return delivered


def run(con, calendar_per_run=2, live_per_run=1, pause=10, dry_run=False):
    if date.today()>date(2027,1,31):
        print('Departure period has passed: no more scans.');return
    stays=choose_stays(con,calendar_per_run)
    print('Calendar stay-length batches:',stays)
    if dry_run:return
    for stay in stays:
        try:
            res=discover_stay(stay);checked=record_discovery(con,stay,res)
            print(f'Duration {stay}: {checked} pairs accounted for, {len(res)} quotes found')
            log(con,'calendar_ok',f'{stay}: {len(res)} quotes')
        except Exception as exc:
            log(con,'calendar_error',f'{stay}: {type(exc).__name__}: {str(exc)[:300]}')
            print(f'Calendar duration {stay} failed: {exc}',file=sys.stderr)
        time.sleep(max(0,pause))
    for row in choose_live(con,live_per_run):
        d,r=row['depart'],row['return_date']
        try:
            offers=search_round_trip(d,r)
            record_live(con,d,r,offers)
            for item in offers:maybe_alert(con,d,r,item)
            log(con,'live_ok',f'{d}/{r} offers={len(offers)}')
            print(f'Live search {d}/{r}: {len(offers)} eligible offers')
        except Exception as exc:
            log(con,'live_error',f'{d}/{r}: {type(exc).__name__}: {str(exc)[:300]}')
            print(f'Live search failed {d}/{r}: {exc}',file=sys.stderr)
        time.sleep(max(0,pause))


def status(con):
    total=con.execute('SELECT COUNT(*) FROM pairs').fetchone()[0]
    covered=con.execute('SELECT COUNT(*) FROM pairs WHERE last_discovered IS NOT NULL').fetchone()[0]
    priced=con.execute('SELECT COUNT(*) FROM pairs WHERE discovery_price IS NOT NULL').fetchone()[0]
    live=con.execute("SELECT COUNT(*) FROM pairs WHERE live_status='verified_itinerary'").fetchone()[0]
    print(f'Eligible date pairs: {total}; calendar queried: {covered}; calendar quotes: {priced}; live-valid pairs: {live}')
    rows=con.execute('''SELECT depart,return_date,live_price,discovery_price,live_status
        FROM pairs WHERE live_price IS NOT NULL OR discovery_price IS NOT NULL
        ORDER BY COALESCE(live_price,discovery_price) LIMIT 15''').fetchall()
    for x in rows:print(dict(x))


def confirm(con,d,r,price,seller):
    # Explicit user-entered manual confirmation; never claim automated checkout success.
    if (d,r) not in {(a.isoformat(),b.isoformat()) for a,b in date_pairs()}:
        raise ValueError('Date pair outside watch window')
    p=valid_price(price)
    if p is None or not seller.startswith('https://'):raise ValueError('Price and https seller URL required')
    con.execute('''INSERT INTO observations(at_utc,depart,return_date,price_cad,source,
        verification,details) VALUES(?,?,?,?,?,?,?)''',(utc(),d,r,p,'manual',
        'user_confirmed_checkout',json.dumps({'seller_url':seller,'entered_by':'user'})))
    con.commit(); print('Saved user-provided checkout confirmation (not independently verified).')


def main():
    p=argparse.ArgumentParser(description='Free-first YYC–ATQ Level 2 fare monitor')
    p.add_argument('command',nargs='?',choices=['scan','status','pairs','confirm'],default='scan')
    p.add_argument('--dry-run',action='store_true')
    p.add_argument('--calendar-per-run',type=int,default=int(os.getenv('CALENDAR_PER_RUN','2')))
    p.add_argument('--live-per-run',type=int,default=int(os.getenv('LIVE_PER_RUN','1')))
    p.add_argument('--pause',type=float,default=float(os.getenv('PAUSE_SECONDS','10')))
    p.add_argument('--depart');p.add_argument('--return-date');p.add_argument('--price',type=float);p.add_argument('--seller-url')
    args=p.parse_args()
    with init() as con:
        if args.command=='status':status(con)
        elif args.command=='pairs':
            for d,r in date_pairs():print(d,r)
        elif args.command=='confirm':confirm(con,args.depart,args.return_date,args.price,args.seller_url)
        else:run(con,max(0,min(args.calendar_per_run,31)),max(0,min(args.live_per_run,3)),args.pause,args.dry_run)

if __name__=='__main__':main()
