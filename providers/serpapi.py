"""Optional maintained API candidate. No billing enrollment or booking support."""
from datetime import datetime, timezone
import json
import os
from urllib.parse import urlencode
from urllib.request import urlopen


class ProviderAccessError(RuntimeError):pass
class BudgetExhausted(RuntimeError):pass
class ProviderDataError(RuntimeError):pass


def reserve(con,now=None):
    """Reserve two searches atomically; do not refund potentially billed failures."""
    stamp=(now or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat()
    con.execute('CREATE TABLE IF NOT EXISTS serpapi_usage (at_utc TEXT NOT NULL, searches INTEGER NOT NULL)')
    if con.in_transaction:raise RuntimeError('Commit application writes before quota reservation')
    con.execute('BEGIN IMMEDIATE')
    try:
        month=con.execute('SELECT COALESCE(SUM(searches),0) FROM serpapi_usage WHERE substr(at_utc,1,7)=?',(stamp[:7],)).fetchone()[0]
        day=con.execute('SELECT COALESCE(SUM(searches),0) FROM serpapi_usage WHERE substr(at_utc,1,10)=?',(stamp[:10],)).fetchone()[0]
        if month+2>240 or day+2>8:raise BudgetExhausted('Free search budget deferred')
        con.execute('INSERT INTO serpapi_usage VALUES (?,2)',(stamp,));con.commit()
    except Exception:
        con.rollback();raise


def rows(payload):
    if payload.get('error'):raise ProviderDataError('Provider reported an API error')
    if payload.get('search_parameters',{}).get('currency')!='CAD':
        raise ProviderDataError('Returned search currency is not CAD')
    return [*payload.get('best_flights',[]),*payload.get('other_flights',[])]


def journey(item,origin,destination,day):
    flights=item.get('flights') or []
    duration=item.get('total_duration')
    if isinstance(duration,bool) or not isinstance(duration,int) or not 0<duration<=1860:
        raise ProviderDataError('Invalid or over-limit whole-journey duration')
    if not flights or flights[0].get('departure_airport',{}).get('id')!=origin or flights[-1].get('arrival_airport',{}).get('id')!=destination:
        raise ProviderDataError('Wrong journey endpoints')
    if flights[0].get('departure_airport',{}).get('time','')[:10]!=day:
        raise ProviderDataError('Wrong journey date')
    if item.get('type')!='Round trip' or any(f.get('travel_class')!='Economy' for f in flights):
        raise ProviderDataError('Trip type or cabin is unverified')
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
        except Exception:
            raise ProviderAccessError('Provider request failed; credentials and URLs withheld') from None

    def search(self,con,depart,return_date):
        account=self.request('account.json',{})
        if str(account.get('plan_name','')).casefold()!='free':
            raise ProviderAccessError('Only an explicitly confirmed Free account is allowed')
        remaining=account.get('total_searches_left')
        if isinstance(remaining,bool) or not isinstance(remaining,int) or remaining<2:
            raise BudgetExhausted('Provider free allowance unavailable')
        reserve(con)
        params={'engine':'google_flights','departure_id':'YYC','arrival_id':'ATQ',
                'outbound_date':depart,'return_date':return_date,'currency':'CAD',
                'adults':1,'travel_class':1,'type':1,'hl':'en','gl':'ca'}
        outbound_payload=self.request('search.json',params)
        candidates=rows(outbound_payload)
        selected=None
        for item in candidates:
            try:out_duration,out_legs=journey(item,'YYC','ATQ',depart)
            except ProviderDataError:continue
            if item.get('departure_token'):
                selected=item;break
        if selected is None:return [],{'status':'no_usable_outbound','outbound_rows':len(candidates)}
        returns=rows(self.request('search.json',{**params,'departure_token':selected['departure_token']}))
        offers=[];rejected=0
        for item in returns:
            try:
                back_duration,back_legs=journey(item,'ATQ','YYC',return_date)
                price=item.get('price')
                if isinstance(price,bool) or not isinstance(price,int) or price<=0:raise ProviderDataError('Invalid total price')
                # Unknown separate-ticket/self-transfer semantics stay unverified.
                if any('separate ticket' in str(x).lower() for x in [*selected.get('extensions',[]),*item.get('extensions',[])]):
                    raise ProviderDataError('Separate tickets require alternative-offer handling')
                offers.append({'price_cad':price,'currency':'CAD','outbound_min':out_duration,
                    'inbound_min':back_duration,'outbound':out_legs,'return':back_legs,
                    'source':'serpapi_google_flights','ticket_type':'provider_round_trip_quote',
                    'verification':'api_search_not_checkout'})
            except ProviderDataError:rejected+=1
        return offers,{'status':'eligible_found' if offers else 'no_usable_return',
            'outbound_rows':len(candidates),'return_rows':len(returns),'rejected_returns':rejected}
