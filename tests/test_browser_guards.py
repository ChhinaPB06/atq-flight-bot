"""Browser experimentation must stop on denial; no browser download needed."""
import sys
from types import SimpleNamespace as S
import unittest
from unittest.mock import MagicMock, Mock, patch
from scripts.browser_transport import BrowserTransport, BrowserBlockedError


class BrowserGuardTests(unittest.TestCase):
    def check_stop(self,status,body):
        page=MagicMock()
        page.goto.return_value=S(status=status)
        page.locator.return_value.inner_text.return_value=body
        page.url='https://www.google.com/travel/flights'
        browser=MagicMock();browser.new_page.return_value=page
        pw=MagicMock();pw.chromium.launch.return_value=browser
        context=MagicMock();context.__enter__.return_value=pw
        decode=Mock()
        modules={'playwright':S(), 'playwright.sync_api':S(sync_playwright=lambda:context),
                 'fli.search._tfs':S(extract_payload=decode),
                 'fli.search._wire':S(iter_wrb_chunks=Mock())}
        transport=BrowserTransport()
        with patch.dict(sys.modules,modules),patch('scripts.browser_transport.time.sleep'):
            with self.assertRaises(BrowserBlockedError):
                transport.fetch(None,'https://www.google.com/travel/flights')
        self.assertEqual(page.goto.call_count,1)
        browser.close.assert_called_once()
        decode.assert_not_called()
        self.assertEqual(transport.events,[])

    def test_http_block_stops_without_decoding_or_retry(self):
        self.check_stop(403,'')

    def test_consent_stops_without_clicking_or_decoding(self):
        self.check_stop(200,'Before you continue to Google')
