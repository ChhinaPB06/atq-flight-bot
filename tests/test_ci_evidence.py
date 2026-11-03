import io
import json
from types import SimpleNamespace as S
import unittest
from unittest.mock import patch
import zipfile
from scripts.inspect_ci import inspect_run


class CIEvidenceTests(unittest.TestCase):
    def test_unit_fixture_output_is_not_live_evidence(self):
        data=io.BytesIO()
        fixture={'status':'fixture_health','probes':{'control':{'returned':12}}}
        live={'status':'actual_health','probes':{'control':{'returned':20}}}
        with zipfile.ZipFile(data,'w') as archive:
            archive.writestr('job.txt','2026-11-03T00:00:00Z test_health ... PROVIDER HEALTH '+json.dumps(fixture)+'\n2026-11-03T00:01:00Z PROVIDER HEALTH '+json.dumps(live)+'\n')
        with patch('scripts.inspect_ci.command',return_value=S(returncode=0,stdout=data.getvalue())):
            report=inspect_run(123)
        self.assertEqual(len(report['health']),1)
        self.assertEqual(report['health'][0]['status'],'actual_health')
        self.assertEqual(report['health'][0]['probes']['control']['returned'],20)
