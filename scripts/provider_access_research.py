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
 'https://support.google.com/travel/answer/6235879?hl=en',
 'https://help.skyscanner.net/hc/en-gb/articles/201152602-How-do-I-set-up-or-cancel-email-price-alerts',
 'https://docs.github.com/en/billing/concepts/product-billing/github-actions',
 'https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm',
 'https://cloud.google.com/free/docs/free-cloud-features',
 'https://developers.skyscanner.net/docs/getting-started/overview',
 'https://www.travelpayouts.com/en/tools/api',
 'https://openflights.org/data.html',
 'https://duffel.com/pricing',
 'https://developers.google.com/optimization/routing/shortest_path']

def fetch(url):
    report={'url':url}
    try:
        with urlopen(url,timeout=20) as response:
            report['status']=response.status;html=response.read(3_000_000).decode(errors='replace')
        parser=Text();parser.feed(html);text=re.sub(r'\s+',' ',' '.join(parser.parts))
        expressions=['price alert','track prices','email','free','billing','credit card',
          'minute','2,000','always free','reclaim','paid','cache','live','partner',
          'search','fare','route','inventory','quota','price change','any dates']
        excerpts=[]
        for expression in expressions:
            for match in list(re.finditer(expression if expression==r'\$' else re.escape(expression),text,re.I))[:12]:
                excerpts.append(text[max(0,match.start()-130):match.end()+370])
        report['excerpts']=list(dict.fromkeys(excerpts))
        if 'calendar-api' in url:
            report['response_examples']=[text[max(0,m.start()-100):m.end()+1300] for m in list(re.finditer('JSON Example',text))[:3]]
    except Exception as exc:
        report['error_type']=type(exc).__name__
        report['http_error_status']=getattr(exc,'code',None)
    return report
with ThreadPoolExecutor(max_workers=3) as pool:
    results=list(pool.map(fetch,sources))
output=Path(sys.argv[1]);output.parent.mkdir(parents=True,exist_ok=True)
output.write_text(json.dumps({'sources':results},indent=2)+'\n')
