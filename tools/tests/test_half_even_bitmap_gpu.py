import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_jiraiya_bitmap_binding import decode
from tools.probes.run_half_even_bitmap import compare_leaves
from tools.probes.build_bitmap_godot_fixture import build
from tools.probes.run_bitmap_godot_fixture import validate_report

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r92/gpu'


class HalfEvenBitmapGpuTests(unittest.TestCase):
    def test_exact_native_old_and_source_bound_images(self):
        report=json.loads((EVIDENCE/'report.json').read_text())
        fixture=build();digest=hashlib.sha256((json.dumps(fixture,separators=(',',':'))+'\n').encode()).hexdigest()
        validate_report(report['controls'],fixture,digest)
        source,images=decode(ROOT/'evidence/importer-loud-fail/r89/native')
        leaves=compare_leaves(source,images,EVIDENCE)
        self.assertEqual(leaves,report['leaves'])
        self.assertEqual(report['exact_images'],6)
        self.assertTrue(all(r['samples']==r['exact']==98304 for r in leaves))
        self.assertFalse(report['production_admitted'])

    def test_sources_and_readbacks_are_pinned(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('readback_sha256',EVIDENCE),('reference_sha256',ROOT/'evidence/importer-loud-fail'),('source_leaf_reference_sha256',ROOT/'evidence/importer-loud-fail/r89/native')]:
            for name,digest in p[key].items():
                self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)

    def test_isolated_delta_keeps_repeat_and_partition_unchanged(self):
        old=(ROOT/'godot/tests/bitmap_sampler_diagnostic.gd').read_text()
        old=old.replace('# Positive axis transforms, identity bitmap fill matrix and fully covered pixels.','# Isolated r91 half-even candidate; positive axis transforms, translation-only fills.')
        old=old.replace('(not repeat or half % 2 == 1)','half % 2 == 1')
        old=old.replace('var y := axis(c.sy, c.ty, int(c.y), height, repeat)','var y := axis(c.sy, c.ty, int(c.y), height, repeat) - float(c.get("fill_y", 0))')
        old=old.replace('xs.append(axis(c.sx, c.tx, x, width, repeat))','xs.append(axis(c.sx, c.tx, x, width, repeat) - float(c.get("fill_x", 0)))')
        self.assertEqual(old,(ROOT/'godot/tests/half_even_bitmap_sampler.gd').read_text())
