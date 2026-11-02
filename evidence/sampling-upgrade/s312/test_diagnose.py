"""Source-bound header and complete callback boundary regressions."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('s312_diagnose', HERE / 'diagnose.py')
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)


class BindingAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = d.diagnose()
        cls.graphs = json.loads((HERE.parent / 's283/diagnosis.json').read_text())
        cls.structural = json.loads((HERE.parent / 's291/diagnosis.json').read_text())['audit']
        cls.source = (HERE / 'ActionDefineFunction2.java').read_text()

    def test_header_changes_and_preload_names(self):
        audit = self.report['binding_audit']
        self.assertEqual(audit['changed_header_fields'], ['register_count', 'suppressThisFlag', 'preloadThisFlag'])
        self.assertEqual(audit['headers']['original']['exporter_preload_names'], {'1': '_root', '2': '_parent'})
        self.assertEqual(audit['headers']['candidate']['exporter_preload_names'], {'1': 'this', '2': '_root', '3': '_parent'})

    def test_owner_is_read_eight_times_never_explicitly_stored(self):
        uses = self.report['binding_audit']['candidate_added_this_uses']
        self.assertEqual(len(uses), 8)
        self.assertTrue(all(n['instruction'] == 'Push register1' for n in uses))

    def test_complete_inventory(self):
        for side in ('original', 'candidate'):
            nodes = self.graphs[side + '_projection']['nodes']
            inventory = self.report['binding_audit']['full_callback_inventory'][side]
            self.assertEqual(inventory['node_count'], len(nodes))
            self.assertEqual([x['node']['index'] for x in inventory['calls']],
                             [n['index'] for n in nodes if n['instruction'].startswith('Call')])
            self.assertEqual(len(inventory['returns']), 6)

    def test_initialization_lexical_boundaries_not_execution(self):
        rows = self.report['binding_audit']['initialization_cut_context']
        self.assertEqual([r['store_index'] for r in rows], [234, 237, 240, 432])
        self.assertEqual(rows[0]['helper_calls_at_lower_node_indices'], [68, 105])
        self.assertEqual(len(rows[-1]['helper_calls_at_lower_node_indices']), 8)
        self.assertTrue(all(r['live_activation_visibility'] is None for r in rows))

    def test_unknowns_stay_unknown(self):
        self.assertIsNone(self.report['historical_execution_observed'])
        self.assertFalse(self.report['production_admitted'])
        self.assertFalse(self.report['native_parity_proven'])
        self.assertEqual(self.report['m0_02_status'], 'pending')
        self.assertTrue(all(not g['proved'] for g in self.report['gates'].values()))

    def test_exporter_order_mutation_rejected(self):
        source = self.source.replace('+ ", " + preloadParentFlag', '+ ", " + preloadThisFlag')
        with self.assertRaisesRegex(ValueError, 'flag order'):
            d.decode_header(self.graphs['original_projection']['header'], source)

    def test_exporter_preload_name_mutation_rejected(self):
        with self.assertRaisesRegex(ValueError, 'preload naming'):
            d.decode_header(self.graphs['original_projection']['header'], self.source.replace('put(pos, "this")', 'put(pos, "_root")'))

    def test_unmapped_header_rejected_even_with_updated_structural_header(self):
        graph = copy.deepcopy(self.graphs['candidate_projection'])
        graph['header'] = graph['header'].replace('13, true, true', '13, false, true')
        structural = copy.deepcopy(self.structural)
        structural['candidate_header'] = graph['header']
        with self.assertRaisesRegex(ValueError, 'Preload name'):
            d.audit(self.graphs['original_projection'], graph, structural, self.source)

    def test_full_body_mutation_rejected(self):
        graph = copy.deepcopy(self.graphs['candidate_projection'])
        graph['nodes'][-1]['instruction'] = 'Pop'
        with self.assertRaises(ValueError):
            d.audit(self.graphs['original_projection'], graph, self.structural, self.source)

    def test_hash_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'pins.json'
            path.write_text(json.dumps({'evidence/sampling-upgrade/s312/diagnose.py': '0' * 64}))
            with self.assertRaisesRegex(ValueError, 'Locked input'):
                d.verify_pins(path)

    def test_all_gates_fail_individually(self):
        with tempfile.TemporaryDirectory() as tmp:
            for flag, code in d.GATES.items():
                result = subprocess.run([sys.executable, str(HERE / 'diagnose.py'), '--output', str(Path(tmp) / 'report.json'), '--require-' + flag], capture_output=True, text=True)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertIn(code, result.stdout)


if __name__ == '__main__':
    unittest.main()
