"""Fail-closed pilot for user-exported native-alert email. No mailbox access."""
from datetime import datetime, timezone
from decimal import Decimal
from email import policy
from email.parser import BytesParser
from email.utils import parsedate_to_datetime
import hashlib
from html.parser import HTMLParser
import json
import re
import tracker


class NativeAlertError(ValueError):pass


class VisibleText(HTMLParser):
    def __init__(self):super().__init__();self.hidden=0;self.parts=[]
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style'):self.hidden+=1
    def handle_endtag(self,tag):
        if tag in ('script','style') and self.hidden:self.hidden-=1
    def handle_data(self,data):
        if not self.hidden:self.parts.append(data)


MONEY=re.compile(r'(?<![A-Z])(?:CAD\s*\$?|CA\$|C\$)\s*((?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d{1,2})?)(?![\d.,])',re.I)


def parse_export(raw):
    if len(raw)>2_000_000:raise NativeAlertError('Message exceeds pilot size limit')
    message=BytesParser(policy=policy.default).parsebytes(raw)
    if len(message.get_all('Date',[]))!=1 or len(message.get_all('Subject',[]))>1:
        raise NativeAlertError('Exactly one Date and at most one Subject header required')
    part=message.get_body(preferencelist=('plain','html'))
    if part is None:raise NativeAlertError('No readable message body')
    content=part.get_content()
    if part.get_content_type()=='text/html':
        parser=VisibleText();parser.feed(content);content=' '.join(parser.parts)
    text=' '.join([str(message.get('Subject','')),content])
    if not re.search(r'(?:YYC|Calgary)\s*(?:to|→|↔|–|-)\s*(?:ATQ|Amritsar)',content,re.I):
        raise NativeAlertError('Explicit Calgary-to-Amritsar route required in message body')
    dates=set(re.findall(r'\b20\d{2}-\d{2}-\d{2}\b',text))
    candidates=[(d.isoformat(),r.isoformat()) for d,r in tracker.date_pairs()
                if d.isoformat() in dates and r.isoformat() in dates]
    if len(candidates)!=1 or dates!=set(candidates[0]):
        raise NativeAlertError('Exactly one in-scope date pair with explicit ISO years required')
    amounts=[]
    for match in MONEY.finditer(text):
        price=Decimal(match.group(1).replace(',',''))
        if not Decimal('0')<price<Decimal('100000'):raise NativeAlertError('Invalid reported amount')
        amounts.append(int(price*100))
    if len(set(amounts))!=1:
        raise NativeAlertError('Exactly one explicit CAD amount required; ambiguous prices rejected')
    try:
        observed=parsedate_to_datetime(message['Date'])
        if observed.tzinfo is None:raise ValueError()
        observed=observed.astimezone(timezone.utc).isoformat()
    except Exception:raise NativeAlertError('Message Date with timezone required') from None
    depart,back=candidates[0]
    facts={'depart':depart,'return_date':back,'currency':'CAD',
           'reported_price_cents':amounts[0],'message_at':observed,
           'verification':'notification_reported_unverified',
           'authentication':'user_export_unverified'}
    facts['fingerprint']=hashlib.sha256(json.dumps(facts,sort_keys=True).encode()).hexdigest()
    return facts


def schema(con):
    con.execute('''CREATE TABLE IF NOT EXISTS native_events (
        id INTEGER PRIMARY KEY,fingerprint TEXT UNIQUE NOT NULL,
        depart TEXT NOT NULL,return_date TEXT NOT NULL,currency TEXT NOT NULL,
        reported_price_cents INTEGER NOT NULL,message_at TEXT NOT NULL,
        imported_at TEXT NOT NULL,status TEXT NOT NULL,verified_at TEXT,
        result TEXT)''');con.commit()


def import_export(con,raw):
    facts=parse_export(raw);schema(con)
    con.execute('''INSERT OR IGNORE INTO native_events
        (fingerprint,depart,return_date,currency,reported_price_cents,message_at,imported_at,status)
        VALUES (?,?,?,?,?,?,?,'unverified')''',
        (facts['fingerprint'],facts['depart'],facts['return_date'],facts['currency'],
         facts['reported_price_cents'],facts['message_at'],tracker.utc()))
    con.commit()
    row=con.execute('SELECT * FROM native_events WHERE fingerprint=?',(facts['fingerprint'],)).fetchone()
    return {'event_id':row['id'],'status':row['status'],**facts}


def verify_event(con,event_id,client=None):
    schema(con)
    row=con.execute('SELECT * FROM native_events WHERE id=?',(event_id,)).fetchone()
    if not row:raise NativeAlertError('Event does not exist')
    if row['status'] in ('verified','no_usable_quote'):
        return {'status':'already_checked','result':json.loads(row['result'])}
    if row['status']=='verifying':return {'status':'verification_in_progress'}
    # Missing dependencies must not strand an event in the in-progress lock.
    from providers.serpapi import Client,BudgetExhausted,diagnostic_status
    changed=con.execute("UPDATE native_events SET status='verifying' WHERE id=? AND status NOT IN ('verifying','verified','no_usable_quote')",(event_id,)).rowcount
    con.commit()
    if not changed:return {'status':'verification_in_progress'}
    try:
        offers,diagnostic=(client or Client()).search(con,row['depart'],row['return_date'],daily_limit=4)
        tracker.record_live(con,row['depart'],row['return_date'],offers)
        report={**diagnostic,'provider':'serpapi_google_flights','raw_pairs':diagnostic.get('return_rows',0),
                'eligible':len(offers),'provider_status':diagnostic_status(offers,diagnostic)}
        tracker.persist_live_diagnostic(con,row['depart'],row['return_date'],report)
        if report['provider_status']=='empty_response':
            con.execute("UPDATE pairs SET live_status='provider_empty_unverified' WHERE depart=? AND return_date=?",(row['depart'],row['return_date']))
        elif report['provider_status']=='parser_error':
            con.execute("UPDATE pairs SET live_status='parser_error' WHERE depart=? AND return_date=?",(row['depart'],row['return_date']))
        con.execute('INSERT OR REPLACE INTO api_pair_checks VALUES (?,?,?)',(row['depart'],row['return_date'],tracker.utc()))
        result={'status':'verified' if offers else 'verification_failed' if report['provider_status']=='parser_error' else 'no_usable_quote',
                'provider_status':report['provider_status'],
                'depart':row['depart'],'return_date':row['return_date'],
                'reported_price_cents':row['reported_price_cents'],
                'actual_min_price_cad':min((o['price_cad'] for o in offers),default=None),
                'qualifies_for_alert':any(o['price_cad']<=tracker.ALERT for o in offers),
                'checkout_verified':False,'notification_sent':False}
        con.execute('UPDATE native_events SET status=?,verified_at=?,result=? WHERE id=?',
            (result['status'],tracker.utc(),json.dumps(result),event_id));con.commit()
        return result
    except Exception as exc:
        status='quota_deferred' if isinstance(exc,BudgetExhausted) else 'verification_failed'
        result={'status':status,'error_type':type(exc).__name__,'checkout_verified':False,'notification_sent':False}
        con.execute('UPDATE native_events SET status=?,result=? WHERE id=?',(status,json.dumps(result),event_id));con.commit()
        return result
