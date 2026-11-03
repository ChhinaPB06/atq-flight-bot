import io
import json
from types import SimpleNamespace as S
import unittest
from unittest.mock import patch
import zipfile
from scripts.inspect_ci import inspect_run


class CIEvidenceTests(unittest.TestCase):
    def test_scanner_events_require_step_and_date_provenance(self):
        data=io.BytesIO()
        fixture={'depart':'2027-01-27','return_date':'2027-04-20',
                 'provider_status':'eligible_found','eligible':1,'raw_pairs':1,'rejected':None}
        line='2026-11-03T00:01:00Z LIVE DIAGNOSTIC '+json.dumps(fixture)+'\n'
        fake_line='2026-11-03T00:01:00Z LIVE DIAGNOSTIC '+json.dumps({**fixture,'depart':'2027-01-28'})+'\n'
        with zipfile.ZipFile(data,'w') as archive:
            archive.writestr('0_offline.txt',fake_line)
            archive.writestr('offline/5_Run python -m unittest.txt',fake_line)
            archive.writestr('scan/7_Flight watch task.txt',line)
        with patch('scripts.inspect_ci.command',return_value=S(returncode=0,stdout=data.getvalue())):
            report=inspect_run(123)
        self.assertEqual(report['live'],[fixture])

    def test_undated_scanner_event_cannot_prove_live_search(self):
        data=io.BytesIO()
        with zipfile.ZipFile(data,'w') as archive:
            archive.writestr('scan/7_Flight watch task.txt',
                '2026-11-03T00:01:00Z LIVE DIAGNOSTIC '+json.dumps({'eligible':1})+'\n')
        with patch('scripts.inspect_ci.command',return_value=S(returncode=0,stdout=data.getvalue())):
            self.assertEqual(inspect_run(123)['live'],[])

    def test_unit_fixture_output_is_not_live_evidence(self):
        data=io.BytesIO()
        fixture={'status':'fixture_health','probes':{'control':{'returned':12}}}
        live={'status':'actual_health','probes':{'control':{'returned':20,'route':'JFK-LHR'}}}
        with zipfile.ZipFile(data,'w') as archive:
            archive.writestr('job.txt','2026-11-03T00:00:00Z test_health ... PROVIDER HEALTH '+json.dumps(fixture)+'\n2026-11-03T00:00:01Z PROVIDER HEALTH '+json.dumps(fixture)+'\n2026-11-03T00:01:00Z PROVIDER HEALTH '+json.dumps(live)+'\n')
        with patch('scripts.inspect_ci.command',return_value=S(returncode=0,stdout=data.getvalue())):
            report=inspect_run(123)
        self.assertEqual(len(report['health']),1)
        self.assertEqual(report['health'][0]['status'],'actual_health')
        self.assertEqual(report['health'][0]['probes']['control']['returned'],20)
