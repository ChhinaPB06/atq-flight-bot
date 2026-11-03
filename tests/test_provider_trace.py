"""Exercise real Fli pairing logic with controlled decoded responses; no HTTP."""
import unittest
from unittest.mock import patch
import tracker as t


class ProviderTraceTests(unittest.TestCase):
    def test_empty_initial_and_empty_expansion_are_distinct(self):
        models=t._fli()
        # Real model validates what Fli will use to encode selected_flight.
        from datetime import datetime
        from fli.models import FlightResult, FlightLeg, Airport, Airline
        leg=FlightLeg(departure_airport=Airport.YYC,arrival_airport=Airport.ATQ,
            departure_datetime=datetime(2027,1,25,12),arrival_datetime=datetime(2027,1,26,12),
            airline=Airline.AC,flight_number='1',duration=1440)
        outbound=FlightResult(legs=[leg],price=2200,currency='CAD',duration=1440,stops=0)
        for have_outbound in (False,True):
            def fetch(self, filters, **kwargs):
                if have_outbound and filters.flight_segments[0].selected_flight is None:
                    return [outbound]
                return None
            report={}
            with patch.object(models['SearchFlights'],'_fetch_flights',fetch):
                self.assertEqual(t.search_round_trip('2027-01-25','2027-04-16',top_n=1,diagnostic=report),[])
            self.assertEqual(report['empty_stage'], 'selected_return_expansion' if have_outbound else 'initial_outbound')
            self.assertEqual(len(report['fetch_events']),2 if have_outbound else 1)
            self.assertEqual(report['provider_status'],'empty_response')

    def test_transport_failure_keeps_stage_evidence(self):
        models=t._fli(); report={}
        with patch.object(models['SearchFlights'],'_fetch_flights',side_effect=TimeoutError()):
            with self.assertRaises(TimeoutError):
                t.search_round_trip('2027-01-25','2027-04-16',top_n=1,diagnostic=report)
        self.assertEqual(report['fetch_events'][0]['stage'],'initial_outbound')
        self.assertEqual(report['fetch_events'][0]['error_type'],'TimeoutError')

    def test_real_fli_enums_validate_as_iata_codes(self):
        from datetime import datetime
        from fli.models import FlightResult, FlightLeg, Airport, Airline
        def flight(origin,dest,day):
            leg=FlightLeg(departure_airport=origin,arrival_airport=dest,
                departure_datetime=datetime.fromisoformat(day+'T12:00'),
                arrival_datetime=datetime.fromisoformat(day+'T23:00'),
                airline=Airline.AC,flight_number='1',duration=660)
            return FlightResult(legs=[leg],price=2200,currency='CAD',duration=660,stops=0)
        report={}
        offers=t.classify_round_trip_results([(flight(Airport.YYC,Airport.ATQ,'2027-01-25'),
            flight(Airport.ATQ,Airport.YYC,'2027-04-16'))],report,'2027-01-25','2027-04-16')
        self.assertEqual(t._airport_code(Airport.YYC),'YYC')
        self.assertEqual(len(offers),1)
