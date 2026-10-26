import json
import unittest
from tools.probes.build_bound_bitmap_component import ROOT
from tools.probes.analyze_cached_component_boundaries import analyze
from tools.probes.inventory_jinye_component import inventory


class CachedComponentBoundaryTests(unittest.TestCase):
    def test_source_graph_matches_pinned_inventory(self):
        evidence = ROOT/'evidence/importer-loud-fail/r220'
        result = inventory(evidence/'jinye-bounded.xml')
        self.assertEqual(json.loads(json.dumps(result)), json.loads((evidence/'inventory.json').read_text()))
        self.assertEqual(len(result['graph']['events']), 231)
        self.assertFalse(result['ratio_consumption_proved'])
        self.assertFalse(result['production_admitted'])

    def test_native_cache_preserves_original_clocks_and_stage(self):
        evidence = ROOT/'evidence/importer-loud-fail/r220'
        result = analyze(evidence/'native')
        self.assertEqual(result, json.loads((evidence/'boundaries.json').read_text()))
        self.assertEqual(result['clocks_exact'], 48)
        for row in result['rows']:
            for key in ('pinned', 'cache_vs_authored', 'normal_composite_vs_stage'):
                self.assertEqual(row[key]['exact'], 240000)
        self.assertEqual([240000-r['cache_vs_clear']['exact'] for r in result['rows']], [25,101,0,48])
        self.assertFalse(result['source_sampler_admitted'])
        self.assertFalse(result['production_admitted'])
