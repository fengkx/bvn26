import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from PIL import Image
from tools.probes.run_nested_filters import decode, compare
from tools.probes.analyze_filter_cxform import analyze
from tools.probes.analyze_materialized_controls import analyze as analyze_controls

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r38'


class NestedFilterTests(unittest.TestCase):
    def test_identity_filters_exact_but_cxform_must_stay_red(self):
        report=compare(decode(EVIDENCE/'native'),EVIDENCE/'render')
        self.assertFalse(report['passed'])
        self.assertFalse(report['production_admitted'])
        self.assertEqual((report['exact'],report['pixels']),(64262,72576))
        for row in report['rows']:
            if row['key'][5]==0 or row['stage'].startswith('child'):
                self.assertEqual(row['exact'],row['pixels'])
            else:
                self.assertLess(row['exact'],row['pixels'])
                self.assertEqual(max(row['max_channel_delta']),1)
                self.assertEqual(row['max_channel_delta'][3],0)

    def test_scalar_success_cannot_admit_inexact_nested_candidate(self):
        report=analyze(EVIDENCE/'cx',EVIDENCE/'native')
        self.assertEqual(report['scalar']['exact'],96)
        self.assertEqual((report['nested']['exact'],report['nested']['samples']),(3144,3456))
        self.assertFalse(report['candidate_admitted'])
        self.assertFalse(report['production_admitted'])

    def test_integer_candidate_is_not_admitted_by_intermediate_success(self):
        report=compare(decode(EVIDENCE/'native'),EVIDENCE/'integer')
        self.assertEqual((report['exact'],report['pixels']),(67774,72576))
        self.assertFalse(report['passed'])
        for row in report['rows']:
            if row['stage']!='final' or row['key'][5]==0:
                self.assertEqual(row['exact'],row['pixels'])
            else:
                self.assertLess(row['exact'],row['pixels'])
        controls=analyze_controls(EVIDENCE)
        self.assertEqual(controls['scores']['dense']['exact'],3072)
        self.assertEqual(controls['scores']['spans']['exact'],5292)
        self.assertEqual(controls['scores']['varied']['exact'],5922)
        self.assertFalse(controls['candidate_admitted'])
        self.assertFalse(controls['production_admitted'])

    def test_missing_or_reordered_native_stage_rejects(self):
        lines=(EVIDENCE/'native/native.log').read_text().splitlines()
        wrong=lines.copy();wrong[2]=wrong[2].replace(',child_input,',',parent_input,')
        for changed in (lines[:-1],[*lines,lines[-1]],wrong):
            with tempfile.TemporaryDirectory() as directory:
                path=Path(directory)
                shutil.copyfile(EVIDENCE/'native/build.json',path/'build.json')
                (path/'native.log').write_text('\n'.join(changed))
                with self.assertRaises(ValueError):decode(path)

    def test_bad_buffer_extent_fails_instead_of_cropping(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)
            Image.new('RGBA',(11,12*48)).save(path/'child_input.png')
            with self.assertRaisesRegex(ValueError,'dimensions'):
                compare(decode(EVIDENCE/'native'),path)

    def test_actual_production_filter_passes_and_provenance(self):
        provenance=json.loads((EVIDENCE/'integer/provenance.json').read_text())
        for name,digest in provenance['source_sha256'].items():
            self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),digest,name)
        for name,digest in provenance['native_sha256'].items():
            self.assertEqual(hashlib.sha256((EVIDENCE/'native'/name).read_bytes()).hexdigest(),digest,name)
        for name,digest in provenance['readback_sha256'].items():
            self.assertEqual(hashlib.sha256((EVIDENCE/'integer'/name).read_bytes()).hexdigest(),digest,name)
        records=json.loads((EVIDENCE/'render/buffers.json').read_text())
        self.assertEqual(len(records),48)
        for i,record in enumerate(records):
            self.assertEqual(record['case'],i)
            self.assertFalse(record['production_admitted'])
            child,parent=record['groups']
            self.assertEqual(child,{'size':[12,12],'origin':[3,3],'passes':[[12,12]]*(3 if i<24 else 2)})
            self.assertEqual(parent,{'size':[18,18],'origin':[1,1],'passes':[[18,18]]*(2 if i<24 else 3)})
