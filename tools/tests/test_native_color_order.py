import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from tools.probes.run_native_color_order import bounds, compare

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'evidence/importer-loud-fail/r61'


class NativeColorOrderTests(unittest.TestCase):
    def test_independent_bounds_and_all_order_groups_exact(self):
        self.assertEqual(bounds(EVIDENCE / 'native'), [37, 37, 70, 70])
        report = compare(EVIDENCE / 'render/order.json')
        self.assertTrue(report['passed'])
        self.assertEqual(report['exact_groups'], 4)
        self.assertEqual(sum(r['exact'] for r in report['rows']), 2560)
        self.assertFalse(report['production_admitted'])

    def test_using_unpadded_extent_still_rejects(self):
        report = compare(EVIDENCE / 'unpadded-order.json')
        self.assertFalse(report['passed'])
        self.assertEqual(report['exact_groups'], 2)
        self.assertEqual(sum(len(r['failures']) for r in report['rows']), 2)

    def test_incomplete_native_bounds_and_changed_pixels_reject(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            shutil.copyfile(EVIDENCE / 'native/build.json', path / 'build.json')
            lines = (EVIDENCE / 'native/native.log').read_text().splitlines()
            (path / 'native.log').write_text('\n'.join(lines[:-1]))
            with self.assertRaises(ValueError):
                bounds(path)
            rows = json.loads((EVIDENCE / 'render/order.json').read_text())
            rows[0]['pixels'][105][0] -= 1
            (path / 'order.json').write_text(json.dumps(rows))
            self.assertFalse(compare(path / 'order.json')['passed'])

    def test_pinned_sources_references_and_readbacks(self):
        provenance = json.loads((EVIDENCE / 'render/provenance.json').read_text())
        for key, root in [('source_sha256', ROOT), ('native_sha256', EVIDENCE / 'native'),
                          ('readback_sha256', EVIDENCE / 'render')]:
            for name, digest in provenance[key].items():
                self.assertEqual(hashlib.sha256((root / name).read_bytes()).hexdigest(), digest)
