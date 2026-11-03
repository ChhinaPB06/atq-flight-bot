"""Read public first-party API/pricing docs. No credentials or flight searches."""
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


sources=['https://serpapi.com/pricing','https://serpapi.com/google-flights-api',
         'https://www.searchapi.io/pricing','https://www.searchapi.io/docs/google-flights']
results=[]
for url in sources:
    report={'url':url}
    try:
        with urlopen(url,timeout=25) as response:
            report['status']=response.status;html=response.read(3_000_000).decode(errors='replace')
        parser=Text();parser.feed(html);text=re.sub(r'\s+',' ',' '.join(parser.parts))
        expressions=['free','credit card','automatically','bill','return_flights','departure_token','currency','round trip']
        excerpts=[]
        for expression in expressions:
            for match in list(re.finditer(re.escape(expression),text,re.I))[:6]:
                excerpts.append(text[max(0,match.start()-100):match.end()+230])
        report['excerpts']=list(dict.fromkeys(excerpts))
    except Exception as exc:report['error_type']=type(exc).__name__
    results.append(report)
output=Path(sys.argv[1]);output.parent.mkdir(parents=True,exist_ok=True)
output.write_text(json.dumps({'sources':results},indent=2)+'\n')
