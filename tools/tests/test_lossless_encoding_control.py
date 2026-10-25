import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from tools.probes.analyze_lossless_encoding_control import analyze
from tools.probes.build_lossless_encoding_control import rewrite
from tools.probes.build_bound_bitmap_component import source_tags

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r145'


class LosslessEncodingControlTests(unittest.TestCase):
    def test_encoding_intervention_is_exact_but_original_still_rejects(self):
        r=analyze(EVIDENCE/'native')
        self.assertEqual(json.loads(json.dumps(r)),json.loads((EVIDENCE/'summary.json').read_text()))
        self.assertTrue(r['format5_variant_matches_as'])
        for v in r['comparisons']['api_comparisons'].values():self.assertEqual(v['exact'],240000)
        self.assertEqual(r['comparisons']['prior_tag_reference']['cache']['exact'],239338)
        self.assertFalse(r['original_indexed_sampling_admitted'])
        self.assertFalse(r['production_admitted'])

    def test_only_encoding_tag_changes_and_locked_source_rejects(self):
        original=ROOT/'game/fighter/lanran.swf';before=original.read_bytes()
        with self.assertRaisesRegex(ValueError,'locked source'):rewrite(original,7)
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'variant.swf';shutil.copyfile(original,path);r=rewrite(path,7)
            self.assertTrue(r['all_other_tags_byte_identical'])
            self.assertEqual(r['unchanged_tag_count'],len(list(source_tags(original)))-1)
            self.assertEqual(r['before_format'],3);self.assertEqual(r['after_format'],5)
            with self.assertRaises(AssertionError):rewrite(path,7)
        self.assertEqual(original.read_bytes(),before)

    def test_source_and_native_pins(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():
                self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
