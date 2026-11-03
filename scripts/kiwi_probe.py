"""Single ordinary Kiwi page observation; no account, bypass, or booking."""
import argparse
import json
from pathlib import Path
from urllib.parse import urlparse

URL='https://www.kiwi.com/en/search/results/calgary-alberta-canada/amritsar-india/2027-01-25/2027-04-16?adults=1&currency=cad'


def shape(value,depth=0):
    if depth>4:return type(value).__name__
    if isinstance(value,dict):return {k:shape(v,depth+1) for k,v in list(value.items())[:35]}
    if isinstance(value,list):return [shape(value[0],depth+1)] if value else []
    return type(value).__name__


def safe_sector(value):
    result={'duration':value.get('duration'),'segments':[]}
    for entry in value.get('sectorSegments',[]):
        segment=entry.get('segment',{})
        row={'duration':segment.get('duration')}
        for end in ('source','destination'):
            node=segment.get(end,{})
            row[end]={k:node.get(k) for k in ('localTime','utcTime')}
            station=node.get('station',{})
            row[end]['station']={k:station.get(k) for k in ('code','name')}
        result['segments'].append(row)
    return result


def observe():
    from playwright.sync_api import sync_playwright
    report={'provider':'kiwi_public_page','requested_currency':'CAD','depart':'2027-01-25',
            'return_date':'2027-04-16','checkout_verified':False,'outcome':'unrun'}
    with sync_playwright() as pw:
        browser=pw.chromium.launch()
        try:
            page=browser.new_page(locale='en-CA')
            captured=[]
            def capture(response):
                url=urlparse(response.url)
                if url.hostname=='api.skypicker.com' and 'SearchReturnItineraries' in response.url:
                    captured.append(response)
            page.on('response',capture)
            response=page.goto(URL,wait_until='domcontentloaded',timeout=30000)
            report['page_status']=response.status if response else None
            if response is None or response.status in (401,403,429):
                report['outcome']='provider_blocked';return report
            # Wait for the normal site's search, without reloading or clicking a challenge.
            for _ in range(8):
                text=page.locator('body').inner_text(timeout=5000).lower()
                if any(m in text for m in ('verify you are human',"verify you're human",'access denied','unusual traffic','captcha')):
                    report['outcome']='provider_challenge_or_block';return report
                if captured:break
                page.wait_for_timeout(5000)
            report['matching_search_responses']=len(captured)
            for response in captured:
                if response.status in (401,403,429):
                    report['outcome']='provider_blocked';return report
                if not response.ok:continue
                payload=response.json()
                report['response_shape']=shape(payload)
                data=payload.get('data',{}).get('returnItineraries',{}) or {}
                nodes=data.get('itineraries',[]) or []
                report['raw_itineraries']=len(nodes)
                report['samples']=[]
                for node in nodes[:3]:
                    price=node.get('price',{})
                    report['samples'].append({'price':{k:price.get(k) for k in ('amount','currency','currencyCode')},
                        'outbound':safe_sector(node.get('outbound',{})),
                        'inbound':safe_sector(node.get('inbound',{}))})
                report['outcome']='observed_unvalidated_candidates' if nodes else 'no_available_provider_data'
                if nodes:return report
            if report['outcome']=='unrun':report['outcome']='no_available_provider_data'
            return report
        finally:browser.close()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    try:report=observe()
    except Exception as exc:report={'provider':'kiwi_public_page','outcome':'experiment_error','error_type':type(exc).__name__}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'outcome':report['outcome']}))
    # This is observation only; it never passes the live-quote acceptance gate.
    raise SystemExit(1)
