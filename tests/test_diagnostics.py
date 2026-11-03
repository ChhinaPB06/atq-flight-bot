import unittest
from types import SimpleNamespace
import tracker as t

class DiagnosticsTests(unittest.TestCase):
    @staticmethod
    def flight(price, duration):
        return SimpleNamespace(price=price, duration=duration, legs=[])

    def test_raw_fares_and_rejection_categories(self):
        raw=[(self.flight(2200,1500), self.flight(2100,1700)),
             (self.flight(1500,1900), self.flight(1400,1300)),
             (self.flight(1600,1400), self.flight(1500,None)),
             ('bad',)]
        report={}
        offers=t.classify_round_trip_results(raw,report)
        self.assertEqual(len(offers),1)
        self.assertEqual(offers[0]['price_cad'],2200) # No hidden 1900 price hard filter
        self.assertEqual(report['raw_pairs'],4)
        self.assertEqual(report['rejected']['outbound_over_31h'],1)
        self.assertEqual(report['rejected']['missing_duration'],1)
        self.assertEqual(report['rejected']['unexpected_provider_shape'],1)
    def test_empty_is_not_absence_of_flights(self):
        report={}
        self.assertEqual(t.classify_round_trip_results([],report),[])
        self.assertEqual(report['provider_status'],'empty_response')
    def test_both_directions_and_equality_boundary(self):
        report={}
        offers=t.classify_round_trip_results([
             (self.flight(2300,1860),self.flight(2300,1860)),
             (self.flight(1200,1900),self.flight(1200,2000))],report)
        self.assertEqual(len(offers),1)
        self.assertEqual(report['rejected']['both_directions_over_31h'],1)

    def test_malformed_api_payload_is_parser_failure_not_provider_outage(self):
        from providers.serpapi import ProviderDataError
        self.assertEqual(t.classify_failure(ProviderDataError('Malformed provider payload')),'parser_error')

if __name__=='__main__': unittest.main()
