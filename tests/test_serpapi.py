from datetime import datetime,timezone
import sqlite3
import unittest
from providers.serpapi import Client,reserve,BudgetExhausted,ProviderAccessError


def flight(origin,destination,day,price=2500,duration=1800):
    return {'type':'Round trip','total_duration':duration,'price':price,
        'flights':[{'departure_airport':{'id':origin,'time':day+' 12:00'},
                    'arrival_airport':{'id':destination,'time':day+' 23:00'},'travel_class':'Economy'}]}


class SerpApiTests(unittest.TestCase):
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
