"""Optional maintained API candidate. No billing enrollment or booking support."""
from datetime import datetime, timezone
from collections import Counter
import json
from math import ceil
import os
import re
from providers.timezones import airport_zone, RULES_VERSION
from urllib.parse import urlencode
from urllib.request import urlopen
from urllib.error import HTTPError,URLError


class ProviderAccessError(RuntimeError):
    def __init__(self,message,status_code=None):
        super().__init__(message)
        self.status_code=status_code
class BudgetExhausted(RuntimeError):pass
class ProviderRateLimit(ProviderAccessError):pass
class ProviderBlocked(ProviderAccessError):pass
class ProviderTimeout(ProviderAccessError):pass
class ProviderDataError(RuntimeError):
    def __init__(self,message,reason='parser_error'):
        super().__init__(message)
        self.reason=reason


def reserve(con,now=None,daily_limit=8):
    """Reserve two searches atomically; do not refund potentially billed failures."""
    stamp=(now or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat()
    con.execute('CREATE TABLE IF NOT EXISTS serpapi_usage (at_utc TEXT NOT NULL, searches INTEGER NOT NULL)')
    if con.in_transaction:raise RuntimeError('Commit application writes before quota reservation')
    con.execute('BEGIN IMMEDIATE')
    try:
        month=con.execute('SELECT COALESCE(SUM(searches),0) FROM serpapi_usage WHERE substr(at_utc,1,7)=?',(stamp[:7],)).fetchone()[0]
        day=con.execute('SELECT COALESCE(SUM(searches),0) FROM serpapi_usage WHERE substr(at_utc,1,10)=?',(stamp[:10],)).fetchone()[0]
        hour=con.execute("SELECT COALESCE(SUM(searches),0) FROM serpapi_usage WHERE julianday(at_utc)>julianday(?,'-1 hour')",(stamp,)).fetchone()[0]
        if month+2>240 or day+2>daily_limit or hour+2>40:raise BudgetExhausted('Free search budget deferred')
        reservation=con.execute('INSERT INTO serpapi_usage VALUES (?,2)',(stamp,)).lastrowid
        con.commit()
        return reservation
    except Exception:
        con.rollback();raise


def rows(payload):
    if not isinstance(payload,dict):raise ProviderDataError('Provider payload is not an object')
    if payload.get('error'):
        message=str(payload['error']).lower()
        if any(text in message for text in ('quota','rate limit','hourly limit','run out of searches','too many requests')):
            raise ProviderRateLimit('Provider search quota or rate limit reached')
        if any(text in message for text in ("hasn't returned any results",'has not returned any results','no results found','no flights found')):
            return []  # No usable provider data; not proof of no inventory.
        raise ProviderDataError('Provider reported an unclassified API error')
    parameters=payload.get('search_parameters')
    if not isinstance(parameters,dict) or parameters.get('currency')!='CAD':
        raise ProviderDataError('Returned search currency is not CAD')
    result=[]
    for key in ('best_flights','other_flights'):
        items=payload.get(key,[])
        if not isinstance(items,list):raise ProviderDataError('Provider itinerary collection is not a list')
        result.extend(items)
    return result


def diagnostic_status(offers,report):
    """Distinguish empty selected returns from rejected initial outbounds."""
    if offers:return 'eligible_found'
    returning='return_rows' in report
    count=report.get('return_rows' if returning else 'outbound_rows',0)
    if not count:return 'empty_response'
    reasons=report.get('return_rejection_reasons' if returning else 'outbound_rejection_reasons',{})
    if reasons.get('parser_error',0)+reasons.get('missing_departure_token',0)>0:
        return 'parser_error'
    return 'all_rejected'


def journey(item,origin,destination,day):
    if not isinstance(item,dict):raise ProviderDataError('Provider itinerary is not an object')
    flights=item.get('flights')
    if not isinstance(flights,list) or not flights or any(not isinstance(f,dict) for f in flights):
        raise ProviderDataError('Provider flights are missing or malformed')
    duration=item.get('total_duration')
    if isinstance(duration,bool) or not isinstance(duration,int) or duration<=0:
        raise ProviderDataError('Invalid whole-journey duration')
    if duration>1860:raise ProviderDataError('Whole-journey duration exceeds limit','duration_limit')
    if item.get('type')!='Round trip':raise ProviderDataError('Trip type is unverified','trip_type_unverified')
    if any(f.get('travel_class')!='Economy' for f in flights):
        raise ProviderDataError('Cabin is unverified','cabin_unverified')
    times=[]
    for flight in flights:
        endpoints=[]
        for key in ('departure_airport','arrival_airport'):
            airport=flight.get(key)
            if not isinstance(airport,dict) or not isinstance(airport.get('id'),str) or not re.fullmatch(r'[A-Z]{3}',airport['id']):
                raise ProviderDataError('Flight airport is malformed')
            stamp=airport.get('time')
            if not isinstance(stamp,str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(?::\d{2})?',stamp):
                raise ProviderDataError('Airport-local timestamp is malformed or offset-bearing')
            try:parsed=datetime.fromisoformat(stamp)
            except ValueError:raise ProviderDataError('Airport-local timestamp is invalid') from None
            endpoints.append(parsed)
        times.append(endpoints)
    if flights[0]['departure_airport']['id']!=origin or flights[-1]['arrival_airport']['id']!=destination:
        raise ProviderDataError('Wrong journey endpoints','route_or_date_mismatch')
    if flights[0]['departure_airport']['time'][:10]!=day:
        raise ProviderDataError('Wrong journey date','route_or_date_mismatch')
    for index,(previous,current) in enumerate(zip(flights,flights[1:])):
        if previous['arrival_airport']['id']!=current['departure_airport']['id']:
            raise ProviderDataError('Disconnected journey legs','route_or_date_mismatch')
        # The layover endpoints share one airport, hence one local timezone.
        # Do not infer flying time between different airport-local clocks.
        if times[index][1]>times[index+1][0]:
            raise ProviderDataError('Connection departs before arrival','route_or_date_mismatch')
    start=times[0][0].replace(tzinfo=airport_zone(origin))
    end=times[-1][1].replace(tzinfo=airport_zone(destination))
    elapsed_seconds=(end.astimezone(timezone.utc)-start.astimezone(timezone.utc)).total_seconds()
    if elapsed_seconds<=0:raise ProviderDataError('Actual elapsed journey is invalid','route_or_date_mismatch')
    if elapsed_seconds>1860*60:raise ProviderDataError('Actual elapsed journey exceeds limit','duration_limit')
    elapsed=ceil(elapsed_seconds/60)
    duration=max(duration,elapsed)  # Conservative if provider and local-time reconstruction differ.
    return duration,[{'airline':f.get('airline'),'number':f.get('flight_number'),
        'from':f['departure_airport']['id'],'to':f['arrival_airport']['id'],
        'depart_at':f['departure_airport']['time'],'arrive_at':f['arrival_airport']['time']} for f in flights]


class Client:
    def __init__(self,key=None,request=None):
        self.key=key or os.getenv('SERPAPI_API_KEY')
        if not self.key:raise ProviderAccessError('SERPAPI_API_KEY is missing')
        self.request=request or self._request

    def _request(self,path,params):
        # Never log URL/exception text: the API key is a query credential.
        url='https://serpapi.com/'+path+'?'+urlencode({**params,'api_key':self.key})
        try:
            with urlopen(url,timeout=30) as response:return json.load(response)
        except HTTPError as exc:
            if exc.code==429:raise ProviderRateLimit('Provider quota or rate limit reached',exc.code) from None
            if exc.code in (403,451):raise ProviderBlocked('Provider access blocked or denied',exc.code) from None
            raise ProviderAccessError('Provider HTTP access failed',exc.code) from None
        except (json.JSONDecodeError,UnicodeDecodeError):
            raise ProviderDataError('Provider response is not valid JSON') from None
        except TimeoutError:
            raise ProviderTimeout('Provider request timed out') from None
        except URLError as exc:
            if isinstance(exc.reason,TimeoutError):raise ProviderTimeout('Provider request timed out') from None
            raise ProviderAccessError('Provider transport access failed') from None
        except Exception:
            raise ProviderAccessError('Provider request failed; credentials and URLs withheld') from None

    def check_access(self):
        account=self.request('account.json',{})
        if not isinstance(account,dict):raise ProviderAccessError('Provider account response is malformed')
        self.account_metadata={k:account.get(k) for k in ('plan_name','plan_id','plan_monthly_price','searches_per_month','total_searches_left')}
        self.account_metadata['field_names']=sorted(account)
        if account.get('plan_id')!='free' or str(account.get('plan_monthly_price')) not in ('0','0.0','0.00'):
            raise ProviderAccessError('Only an explicitly confirmed Free account is allowed')
        remaining=account.get('total_searches_left')
        if isinstance(remaining,bool) or not isinstance(remaining,int) or remaining<2:
            raise BudgetExhausted('Provider free allowance unavailable')
        return remaining

    def search(self,con,depart,return_date,daily_limit=8):
        self.check_access()
        reservation=reserve(con,daily_limit=daily_limit)
        params={'engine':'google_flights','departure_id':'YYC','arrival_id':'ATQ',
                'outbound_date':depart,'return_date':return_date,'currency':'CAD',
                'adults':1,'travel_class':1,'type':1,'hl':'en','gl':'ca'}
        outbound_payload=self.request('search.json',params)
        candidates=sorted(rows(outbound_payload),key=lambda item: item.get('price') if isinstance(item,dict) and type(item.get('price')) is int and item['price']>0 else float('inf'))
        selected=None;out_reasons=Counter()
        for item in candidates:
            try:out_duration,out_legs=journey(item,'YYC','ATQ',depart)
            except ProviderDataError as exc:
                out_reasons[exc.reason]+=1;continue
            if isinstance(item.get('departure_token'),str) and item['departure_token']:
                selected=item;break
            out_reasons['missing_departure_token']+=1
        if selected is None:
            # The second HTTP call is provably not made; this is unused local
            # capacity, not a refund of an ambiguous or provider-billed failure.
            con.execute('UPDATE serpapi_usage SET searches=1 WHERE rowid=? AND searches=2',(reservation,))
            con.commit()
            report={'status':'no_usable_outbound','outbound_rows':len(candidates),'requests_made':1,
                    'rejected_outbounds':sum(out_reasons.values()),'outbound_rejection_reasons':dict(out_reasons)}
            report['provider_status']=diagnostic_status([],report)
            return [],report
        returns=rows(self.request('search.json',{**params,'departure_token':selected['departure_token']}))
        offers=[];rejected=Counter()
        for item in returns:
            try:
                back_duration,back_legs=journey(item,'ATQ','YYC',return_date)
                price=item.get('price')
                if isinstance(price,bool) or not isinstance(price,int) or price<=0:
                    raise ProviderDataError('Invalid total price','price_unverified')
                # Unknown separate-ticket/self-transfer semantics stay unverified.
                extensions=[]
                for part in (selected,item):
                    values=part.get('extensions',[])
                    if values is None:values=[]
                    if not isinstance(values,list) or any(not isinstance(v,str) for v in values):
                        raise ProviderDataError('Provider ticket extensions are malformed')
                    extensions.extend(values)
                if any('separate ticket' in x.lower() for x in extensions):
                    raise ProviderDataError('Separate tickets require alternative-offer handling','separate_tickets_unverified')
                offers.append({'price_cad':price,'currency':'CAD','outbound_min':out_duration,
                    'inbound_min':back_duration,'outbound':out_legs,'return':back_legs,
                    'source':'serpapi_google_flights','ticket_type':'provider_round_trip_quote',
                    'timezone_rules':RULES_VERSION,
                    'verification':'api_search_not_checkout'})
            except ProviderDataError as exc:rejected[exc.reason]+=1
        report={'status':'eligible_found' if offers else 'no_usable_return',
            'outbound_rows':len(candidates),'return_rows':len(returns),'rejected_returns':sum(rejected.values()),
            'rejected_outbounds':sum(out_reasons.values()),'outbound_rejection_reasons':dict(out_reasons),
            'return_rejection_reasons':dict(rejected)}
        report['provider_status']=diagnostic_status(offers,report)
        return offers,report
