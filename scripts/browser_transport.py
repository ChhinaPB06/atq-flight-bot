"""Experimental standard-browser observation of the ordinary Flights page.

No stealth plugins, proxy rotation, token replay or challenge solving. Stop on
blocks/consent. Kept outside production until real fares and repeatability pass.
"""
import threading
import time
from unittest.mock import patch


class BrowserBlockedError(RuntimeError):
    pass


class BrowserNoPayloadError(RuntimeError):
    pass


class BrowserTransport:
    def __init__(self):
        self.lock=threading.Lock()
        self.events=[]

    def fetch(self, client, url):
        from playwright.sync_api import sync_playwright
        from fli.search._tfs import extract_payload
        from fli.search._wire import iter_wrb_chunks
        with self.lock:
            with sync_playwright() as pw:
                browser=pw.chromium.launch()
                try:
                    page=browser.new_page(locale='en-CA')
                    responses=[]
                    page.on('response',lambda response: responses.append(response)
                            if 'FlightsFrontendService/GetShoppingResults' in response.url else None)
                    main=page.goto(url,wait_until='domcontentloaded',timeout=30000)
                    if main is None or main.status in (401,403,429):
                        raise BrowserBlockedError('Page access denied')
                    page.wait_for_timeout(10000)
                    body=page.locator('body').inner_text(timeout=5000).lower()
                    if any(marker in body for marker in ('unusual traffic','verify you are human',
                           "verify you're human",'before you continue to google')) or '/sorry/' in page.url:
                        raise BrowserBlockedError('Challenge or consent page; stopped')
                    payload=extract_payload(page.content())
                    source='rendered_inline'
                    for response in responses:
                        if response.status in (401,403,429):
                            raise BrowserBlockedError('Search request denied')
                        if response.ok:
                            for candidate in iter_wrb_chunks(response.text()):
                                if isinstance(candidate,list) and len(candidate)>3 and any(
                                        candidate[i] for i in (2,3)):
                                    payload=candidate;source='browser_search_response'
                    if payload is None:
                        raise BrowserNoPayloadError('No decoded browser payload')
                    counts=[len(payload[i][0] or []) if isinstance(payload[i],list) and payload[i] else 0 for i in (2,3)]
                    self.events.append({'source':source,'row_groups':counts})
                    return payload
                finally:
                    browser.close()
                    time.sleep(10)

    def activate(self):
        return patch('fli.search.flights.fetch_payload',self.fetch)
