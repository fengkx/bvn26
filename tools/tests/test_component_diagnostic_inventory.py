import json
import unittest

from tools.probes.build_bound_bitmap_component import ROOT
from tools.probes.inventory_component_diagnostics import inventory
from tools.probes.inventory_orochimaru_bitmap import inventory as bitmap_inventory


class ComponentDiagnosticInventoryTests(unittest.TestCase):
    def test_case_tick_bindings_retain_native_and_source_hashes(self):
        result = inventory()
        self.assertEqual(result, json.loads((ROOT / 'evidence/importer-loud-fail/r209/inventory.json').read_text()))
        self.assertEqual(result['source_backed_diagnostic_exact'], 36)
        self.assertFalse(result['production_admitted'])

    def test_original_jpeg3_remains_rejected_by_lossless_binding(self):
        evidence = ROOT / 'evidence/importer-loud-fail/r209'
        result = bitmap_inventory(evidence / 'orochimaru-bounded.xml')
        self.assertEqual(json.loads(json.dumps(result)), json.loads((evidence / 'orochimaru.json').read_text()))
        self.assertEqual(result['bitmap']['alpha_histogram'], {0: 30941, 255: 39367})
        self.assertFalse(result['decoder_parity_proved'])
