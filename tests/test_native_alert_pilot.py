"""Synthetic email fixtures only; not proof of a real Google email template."""
from email.message import EmailMessage
import tempfile
from pathlib import Path
import unittest
from unittest.mock import Mock,patch
import sys
import tracker
from signals.native_email import parse_export,import_export,verify_event,NativeAlertError


def email(body,subject="Calgary to Amritsar price update"):
    message=EmailMessage();message['Date']='Tue, 3 Nov 2026 06:00:00 +0000'
    message['Subject']=subject
    message.set_content(body)
    return message.as_bytes()


BODY='Calgary to Amritsar: Depart 2027-01-27 Return 2027-04-20. CAD 1,800.49'


class NativeAlertPilotTests(unittest.TestCase):
    def test_cents_and_html_without_network(self):
        self.assertEqual(parse_export(email(BODY))['reported_price_cents'],180049)
        message=EmailMessage();message['Date']='Tue, 3 Nov 2026 06:00:00 +0000'
        message.set_content('<p>'+BODY+'</p><script>CAD 10</script>',subtype='html')
        self.assertEqual(parse_export(message.as_bytes())['reported_price_cents'],180049)

    def test_ambiguous_currency_prices_dates_and_wrong_route_rejected(self):
        for body in [BODY.replace('CAD','$'),BODY+' CAD 2,000',
                     BODY+' 2027-04-21',BODY.replace('2027-01-27','2027-01-25')]:
            with self.subTest(body=body),self.assertRaises(NativeAlertError):parse_export(email(body))

    def test_wrong_route_rejected(self):
        with self.assertRaises(NativeAlertError):
            parse_export(email(BODY.replace('Calgary to Amritsar','Amritsar to Calgary'),subject='Amritsar to Calgary update'))

    def test_forward_subject_cannot_mask_reverse_route_in_body(self):
        with self.assertRaises(NativeAlertError):
            parse_export(email(BODY.replace('Calgary to Amritsar','Amritsar to Calgary')))

    def test_unrelated_extra_iso_date_is_not_silently_ignored(self):
        with self.assertRaises(NativeAlertError):parse_export(email(BODY+' Other trip 2027-12-31'))

    def test_ambiguous_duplicate_headers_rejected(self):
        raw=email(BODY)
        for header in (b'Date: Tue, 3 Nov 2026 06:00:00 +0000\n',
                       b'Subject: Another trip\n'):
            with self.subTest(header=header),self.assertRaises(NativeAlertError):
                parse_export(header+raw)

    def test_import_deduplicates_and_does_not_create_live_observations(self):
        with tempfile.TemporaryDirectory() as tmp,tracker.init(Path(tmp)/'db') as con:
            first=import_export(con,email(BODY));second=import_export(con,email(BODY))
            self.assertEqual(first['event_id'],second['event_id'])
            self.assertEqual(con.execute('SELECT COUNT(*) FROM native_events').fetchone()[0],1)
            self.assertEqual(con.execute('SELECT COUNT(*) FROM observations').fetchone()[0],0)
            self.assertEqual(first['verification'],'notification_reported_unverified')

    def test_verification_uses_actual_fare_and_is_not_repeated(self):
        with tempfile.TemporaryDirectory() as tmp,tracker.init(Path(tmp)/'db') as con:
            event=import_export(con,email(BODY))
            client=Mock();client.search.return_value=([{'price_cad':2200,'outbound_min':1800,
                'inbound_min':1800,'outbound':[],'return':[],'source':'serpapi_google_flights'}],{'return_rows':1})
            result=verify_event(con,event['event_id'],client)
            self.assertEqual(result['actual_min_price_cad'],2200)
            self.assertFalse(result['qualifies_for_alert']);self.assertFalse(result['notification_sent'])
            self.assertEqual(verify_event(con,event['event_id'],client)['status'],'already_checked')
            self.assertEqual(client.search.call_count,1)

    def test_quota_deferral_keeps_signal_unverified(self):
        from providers.serpapi import BudgetExhausted
        with tempfile.TemporaryDirectory() as tmp,tracker.init(Path(tmp)/'db') as con:
            event=import_export(con,email(BODY));client=Mock()
            client.search.side_effect=BudgetExhausted('test quota')
            self.assertEqual(verify_event(con,event['event_id'],client)['status'],'quota_deferred')
            self.assertEqual(con.execute('SELECT COUNT(*) FROM observations').fetchone()[0],0)

    def test_missing_dependency_does_not_strand_event_lock(self):
        with tempfile.TemporaryDirectory() as tmp,tracker.init(Path(tmp)/'db') as con:
            event=import_export(con,email(BODY))
            with patch.dict(sys.modules,{'providers.serpapi':None}):
                with self.assertRaises(ImportError):verify_event(con,event['event_id'])
            self.assertEqual(con.execute('SELECT status FROM native_events').fetchone()[0],'unverified')

    def test_rejected_nonempty_outbounds_are_not_provider_empty(self):
        with tempfile.TemporaryDirectory() as tmp,tracker.init(Path(tmp)/'db') as con:
            event=import_export(con,email(BODY));client=Mock()
            client.search.return_value=([],{'status':'no_usable_outbound','outbound_rows':2,
                'rejected_outbounds':2,'outbound_rejection_reasons':{'duration_limit':2}})
            result=verify_event(con,event['event_id'],client)
            self.assertEqual(result['status'],'no_usable_quote')
            self.assertEqual(con.execute('SELECT status FROM live_diagnostics').fetchone()[0],'all_rejected')
            self.assertEqual(con.execute("SELECT live_status FROM pairs WHERE last_live IS NOT NULL").fetchone()[0],'no_eligible_itinerary')

    def test_parser_failure_is_not_provider_empty(self):
        with tempfile.TemporaryDirectory() as tmp,tracker.init(Path(tmp)/'db') as con:
            event=import_export(con,email(BODY));client=Mock()
            client.search.return_value=([],{'status':'no_usable_outbound','outbound_rows':2,
                'rejected_outbounds':2,'outbound_rejection_reasons':{'parser_error':2}})
            result=verify_event(con,event['event_id'],client)
            self.assertEqual(result['status'],'verification_failed')
            self.assertEqual(result['provider_status'],'parser_error')
            self.assertEqual(con.execute('SELECT status FROM live_diagnostics').fetchone()[0],'parser_error')
            self.assertEqual(con.execute("SELECT live_status FROM pairs WHERE last_live IS NOT NULL").fetchone()[0],'parser_error')

    def test_attachment_does_not_override_message_price(self):
        message=EmailMessage();message['Date']='Tue, 3 Nov 2026 06:00:00 +0000'
        message.set_content(BODY)
        message.add_attachment('CAD 1.00 Calgary to Amritsar 2027-01-27 2027-04-20',subtype='plain',filename='attachment.txt')
        self.assertEqual(parse_export(message.as_bytes())['reported_price_cents'],180049)
