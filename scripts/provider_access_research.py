"""Read public first-party API/pricing docs. No credentials or flight searches."""
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from urllib.request import urlopen


class Text(HTMLParser):
    def __init__(self):super().__init__();self.skip=0;self.parts=[]
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style'):self.skip+=1
    def handle_endtag(self,tag):
        if tag in ('script','style') and self.skip:self.skip-=1
    def handle_data(self,data):
        if not self.skip:self.parts.append(data)


sources=[
 'https://hasdata.com/prices','https://docs.hasdata.com/apis/google-travel/flights',
 'https://flightpowers.com/pricing','https://flightpowers.com/docs',
 'https://rapidapi.com/mtnrabi/api/google-flights-live-api/pricing',
 'https://flightapi.io/pricing','https://docs.flightapi.io/round-trip-flights-api',
 'https://www.searchapi.io/pricing','https://www.searchapi.io/docs/google-flights-calendar-api']

def fetch(url):
    report={'url':url}
    try:
        with urlopen(url,timeout=20) as response:
            report['status']=response.status;html=response.read(3_000_000).decode(errors='replace')
        parser=Text();parser.feed(html);text=re.sub(r'\s+',' ',' '.join(parser.parts))
        expressions=['free','credit card','automatically','bill','departure_token',
          'currency','round trip','round-trip','calendar','Google Flights',
          'credit','requests','searches',r'\$','overage','USD','CAD','2,500','roundtrip']
        excerpts=[]
        for expression in expressions:
            for match in list(re.finditer(expression if expression==r'\$' else re.escape(expression),text,re.I))[:12]:
                excerpts.append(text[max(0,match.start()-130):match.end()+370])
        report['excerpts']=list(dict.fromkeys(excerpts))
    except Exception as exc:
        report['error_type']=type(exc).__name__
        report['http_error_status']=getattr(exc,'code',None)
    return report
with ThreadPoolExecutor(max_workers=3) as pool:
    results=list(pool.map(fetch,sources))
output=Path(sys.argv[1]);output.parent.mkdir(parents=True,exist_ok=True)
output.write_text(json.dumps({'sources':results},indent=2)+'\n')
