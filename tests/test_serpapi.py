from datetime import datetime,timezone,timedelta
import sqlite3
import io
import unittest
from unittest.mock import patch
from urllib.error import HTTPError,URLError
from providers.serpapi import Client,reserve,BudgetExhausted,ProviderAccessError


def flight(origin,destination,day,price=2500,duration=1800):
    return {'type':'Round trip','total_duration':duration,'price':price,
        'flights':[{'departure_airport':{'id':origin,'time':day+' 12:00'},
                    'arrival_airport':{'id':destination,'time':((datetime.fromisoformat(day)+timedelta(days=1)).date().isoformat() if origin=='YYC' else day)+' 23:00'},'travel_class':'Economy'}]}


class SerpApiTests(unittest.TestCase):
    def test_pinned_rules_handle_calgary_january_2027_offset(self):
        from providers.timezones import airport_zone,RULES_VERSION
        self.assertEqual(RULES_VERSION,'2026.6')
        self.assertEqual(datetime(2027,1,27,12,tzinfo=airport_zone('YYC')).utcoffset(),timedelta(hours=-6))

    def test_underreported_duration_cannot_hide_current_rule_31_hour_violation(self):
        from providers.serpapi import journey,ProviderDataError
        item=flight('YYC','ATQ','2027-01-27',duration=1860)
        item['flights'][0]['arrival_airport']['time']='2027-01-29 07:00'
        # Old Calgary winter rules gave 30h30; pinned current rules give 31h30.
        with self.assertRaises(ProviderDataError):journey(item,'YYC','ATQ','2027-01-27')

    def test_paid_account_cannot_search(self):
        calls=[]
        def request(path,params):calls.append(path);return {'plan_name':'Developer','total_searches_left':100}
        with sqlite3.connect(':memory:') as con:
            with self.assertRaises(ProviderAccessError):Client('test-only',request).search(con,'2027-01-25','2027-04-16')
        self.assertEqual(calls,['account.json'])

    def test_specific_return_total_and_whole_duration(self):
        out=flight('YYC','ATQ','2027-01-25',price=1800);out['departure_token']='ephemeral-test-token'
        back=flight('ATQ','YYC','2027-04-16',price=2300)
        replies=[{'plan_name':'Free Plan','plan_id':'free','plan_monthly_price':0,'total_searches_left':250},
                 {'search_parameters':{'currency':'CAD'},'best_flights':[out]},
                 {'search_parameters':{'currency':'CAD'},'best_flights':[back]}]
        with sqlite3.connect(':memory:') as con:
            offers,diagnostic=Client('test-only',lambda p,q:replies.pop(0)).search(con,'2027-01-25','2027-04-16')
            self.assertEqual(offers[0]['price_cad'],2300)
            self.assertEqual(offers[0]['outbound_min'],1800)
            self.assertNotIn('ephemeral-test-token',str(offers))
            self.assertEqual(con.execute('SELECT SUM(searches) FROM serpapi_usage').fetchone()[0],2)

    def test_daily_and_monthly_limits(self):
        now=datetime(2026,11,3,tzinfo=timezone.utc)
        with sqlite3.connect(':memory:') as con:
            for _ in range(4):reserve(con,now)
            with self.assertRaises(BudgetExhausted):reserve(con,now)
            con.execute('DELETE FROM serpapi_usage');con.execute('INSERT INTO serpapi_usage VALUES (?,240)',('2026-11-01T00:00:00+00:00',));con.commit()
            with self.assertRaises(BudgetExhausted):reserve(con,now)

    def test_non_cad_response_rejected(self):
        from providers.serpapi import ProviderDataError
        replies=[{'plan_name':'Free Plan','plan_id':'free','plan_monthly_price':0,'total_searches_left':250},
                 {'search_parameters':{'currency':'USD'},'best_flights':[]}]
        with sqlite3.connect(':memory:') as con:
            with self.assertRaises(ProviderDataError):Client('test-only',lambda p,q:replies.pop(0)).search(con,'2027-01-25','2027-04-16')

    def test_over_limit_and_separate_ticket_returns_not_accepted(self):
        out=flight('YYC','ATQ','2027-01-25');out['departure_token']='ephemeral-test-token'
        over=flight('ATQ','YYC','2027-04-16',duration=1900)
        separate=flight('ATQ','YYC','2027-04-16');separate['extensions']=['Separate tickets booked together']
        replies=[{'plan_name':'Free Plan','plan_id':'free','plan_monthly_price':0,'total_searches_left':250},
                 {'search_parameters':{'currency':'CAD'},'best_flights':[out]},
                 {'search_parameters':{'currency':'CAD'},'best_flights':[over,separate]}]
        with sqlite3.connect(':memory:') as con:
            offers,report=Client('test-only',lambda p,q:replies.pop(0)).search(con,'2027-01-25','2027-04-16')
        self.assertEqual(offers,[])
        self.assertEqual(report['rejected_returns'],2)

    def test_initial_batch_keeps_rolling_hour_cap(self):
        now=datetime(2026,11,3,tzinfo=timezone.utc)
        with sqlite3.connect(':memory:') as con:
            for _ in range(20):reserve(con,now,daily_limit=120)
            with self.assertRaises(BudgetExhausted):reserve(con,now,daily_limit=120)
            self.assertEqual(con.execute('SELECT SUM(searches) FROM serpapi_usage').fetchone()[0],40)

    def test_steady_budget_limits_two_pairs_daily(self):
        now=datetime(2026,11,3,tzinfo=timezone.utc)
        with sqlite3.connect(':memory:') as con:
            reserve(con,now,daily_limit=4);reserve(con,now,daily_limit=4)
            with self.assertRaises(BudgetExhausted):reserve(con,now,daily_limit=4)

    def test_cheapest_valid_outbound_is_expanded(self):
        expensive=flight('YYC','ATQ','2027-01-27',price=2500);expensive['departure_token']='expensive'
        cheap=flight('YYC','ATQ','2027-01-27',price=2100);cheap['departure_token']='cheaper'
        back=flight('ATQ','YYC','2027-04-20',price=2245)
        calls=[]
        replies=[{'plan_name':'Free Plan','plan_id':'free','plan_monthly_price':0,'total_searches_left':250},
                 {'search_parameters':{'currency':'CAD'},'best_flights':[expensive],'other_flights':[cheap]},
                 {'search_parameters':{'currency':'CAD'},'best_flights':[back]}]
        def request(path,params):calls.append(params);return replies.pop(0)
        with sqlite3.connect(':memory:') as con:
            offers,_=Client('test-only',request).search(con,'2027-01-27','2027-04-20')
        self.assertEqual(calls[-1]['departure_token'],'cheaper')
        self.assertEqual(offers[0]['price_cad'],2245)

    def test_provider_no_results_is_unverified_data_absence(self):
        from providers.serpapi import rows
        self.assertEqual(rows({'error':"Google Flights hasn't returned any results for this query."}),[])

    def test_provider_quota_json_is_not_swallowed_as_empty(self):
        from providers.serpapi import rows,ProviderRateLimit
        with self.assertRaises(ProviderRateLimit):rows({'error':'You have reached your plan hourly limit.'})

    def test_unmade_return_request_does_not_consume_local_capacity(self):
        calls=[]
        responses=[{'plan_id':'free','plan_monthly_price':0,'total_searches_left':250},
                   {'search_parameters':{'currency':'CAD'},'best_flights':[]}]
        def request(path,params):calls.append(path);return responses.pop(0)
        with sqlite3.connect(':memory:') as con:
            offers,report=Client('test-only',request).search(con,'2027-01-27','2027-04-17')
            self.assertEqual(offers,[])
            self.assertEqual(report['requests_made'],1)
            self.assertEqual(con.execute('SELECT SUM(searches) FROM serpapi_usage').fetchone()[0],1)
        self.assertEqual(calls,['account.json','search.json'])

    def test_ambiguous_return_failure_keeps_full_reservation(self):
        out=flight('YYC','ATQ','2027-01-27');out['departure_token']='test-token'
        replies=[{'plan_id':'free','plan_monthly_price':0,'total_searches_left':250},
                 {'search_parameters':{'currency':'CAD'},'best_flights':[out]}]
        def request(path,params):
            if not replies:raise ProviderAccessError('Request failed')
            return replies.pop(0)
        with sqlite3.connect(':memory:') as con:
            with self.assertRaises(ProviderAccessError):Client('test-only',request).search(con,'2027-01-27','2027-04-17')
            self.assertEqual(con.execute('SELECT SUM(searches) FROM serpapi_usage').fetchone()[0],2)

    def test_disconnected_or_negative_layover_cannot_be_accepted(self):
        from providers.serpapi import journey,ProviderDataError
        for second_origin,second_depart in [('JFK','2027-04-20 18:00'),('DOH','2027-04-20 14:00')]:
            item=flight('ATQ','YYC','2027-04-20')
            item['flights']=[
                {'departure_airport':{'id':'ATQ','time':'2027-04-20 12:00'},
                 'arrival_airport':{'id':'DOH','time':'2027-04-20 15:00'},'travel_class':'Economy'},
                {'departure_airport':{'id':second_origin,'time':second_depart},
                 'arrival_airport':{'id':'YYC','time':'2027-04-20 23:00'},'travel_class':'Economy'}]
            with self.subTest(second_origin=second_origin),self.assertRaises(ProviderDataError) as error:
                journey(item,'ATQ','YYC','2027-04-20')
            self.assertEqual(error.exception.reason,'route_or_date_mismatch')

    def test_malformed_timestamp_is_counted_as_parser_rejection_not_empty(self):
        out=flight('YYC','ATQ','2027-01-27');out['departure_token']='test-token'
        bad=flight('ATQ','YYC','2027-04-20')
        bad['flights'][0]['arrival_airport']['time']='not-a-timestamp'
        valid=flight('ATQ','YYC','2027-04-20',price=2400)
        responses=[{'plan_id':'free','plan_monthly_price':0,'total_searches_left':250},
                   {'search_parameters':{'currency':'CAD'},'best_flights':[out]},
                   {'search_parameters':{'currency':'CAD'},'best_flights':[bad,valid]}]
        with sqlite3.connect(':memory:') as con:
            offers,report=Client('test-only',lambda p,q:responses.pop(0)).search(con,'2027-01-27','2027-04-20')
        self.assertEqual([o['price_cad'] for o in offers],[2400])
        self.assertEqual(report['return_rejection_reasons'],{'parser_error':1})
        self.assertEqual(report['provider_status'],'eligible_found')

    def test_all_rejected_outbounds_are_not_reported_as_provider_empty(self):
        over=flight('YYC','ATQ','2027-01-27',duration=1900)
        responses=[{'plan_id':'free','plan_monthly_price':0,'total_searches_left':250},
                   {'search_parameters':{'currency':'CAD'},'best_flights':[over]}]
        with sqlite3.connect(':memory:') as con:
            offers,report=Client('test-only',lambda p,q:responses.pop(0)).search(con,'2027-01-27','2027-04-20')
            self.assertEqual(con.execute('SELECT SUM(searches) FROM serpapi_usage').fetchone()[0],1)
        self.assertEqual(offers,[])
        self.assertEqual(report['outbound_rejection_reasons'],{'duration_limit':1})
        self.assertEqual(report['provider_status'],'all_rejected')

    def test_mixed_parser_and_duration_rejections_remain_parser_failure(self):
        from providers.serpapi import diagnostic_status
        self.assertEqual(diagnostic_status([],{'outbound_rows':2,
            'outbound_rejection_reasons':{'parser_error':1,'duration_limit':1}}),'parser_error')
        self.assertEqual(diagnostic_status([],{'outbound_rows':4,'return_rows':0}),'empty_response')

    def test_wrong_provider_collection_and_offset_timestamp_are_rejected(self):
        from providers.serpapi import rows,journey,ProviderDataError
        for payload in [[],{'search_parameters':{'currency':'CAD'},'best_flights':None},
                        {'search_parameters':{'currency':'CAD'},'best_flights':{'flights':[]}}]:
            with self.subTest(payload=payload),self.assertRaises(ProviderDataError):rows(payload)
        for stamp in ['2027-04-20','2027-04-20 23:00+00:00','2027-04-20 25:00']:
            item=flight('ATQ','YYC','2027-04-20')
            item['flights'][0]['arrival_airport']['time']=stamp
            with self.subTest(stamp=stamp),self.assertRaises(ProviderDataError) as error:
                journey(item,'ATQ','YYC','2027-04-20')
            self.assertEqual(error.exception.reason,'parser_error')

    def test_transport_failures_are_classified_without_leaking_request_credentials(self):
        from providers.serpapi import ProviderBlocked,ProviderTimeout,ProviderRateLimit,ProviderDataError
        private_url='https://provider.invalid/?api_key=never-export-this-value'
        failures=[(HTTPError(private_url,403,'Forbidden',{},None),ProviderBlocked),
                  (HTTPError(private_url,429,'Too many requests',{},None),ProviderRateLimit),
                  (HTTPError(private_url,503,'Service unavailable',{},None),ProviderAccessError),
                  (TimeoutError(private_url),ProviderTimeout),
                  (URLError(TimeoutError(private_url)),ProviderTimeout)]
        for failure,expected in failures:
            with self.subTest(expected=expected),patch('providers.serpapi.urlopen',side_effect=failure) as request:
                with self.assertRaises(expected) as caught:Client('never-export-this-value')._request('search.json',{})
                self.assertNotIn('never-export-this-value',str(caught.exception))
                self.assertNotIn('https:',str(caught.exception))
                self.assertEqual(request.call_count,1)
        with patch('providers.serpapi.urlopen',return_value=io.BytesIO(b'not JSON')):
            with self.assertRaises(ProviderDataError):Client('never-export-this-value')._request('search.json',{})

    def test_quota_error_has_priority_over_incidental_no_results_text(self):
        from providers.serpapi import rows,ProviderRateLimit
        with self.assertRaises(ProviderRateLimit):rows({'error':'No results found because the hourly limit was reached.'})

    def test_seconds_over_31_hours_are_not_truncated_into_an_eligible_fare(self):
        from providers.serpapi import journey,ProviderDataError
        item=flight('YYC','ATQ','2027-01-27',duration=1860)
        item['flights'][0]['arrival_airport']['time']='2027-01-29 06:30:01'
        with self.assertRaises(ProviderDataError) as caught:journey(item,'YYC','ATQ','2027-01-27')
        self.assertEqual(caught.exception.reason,'duration_limit')
