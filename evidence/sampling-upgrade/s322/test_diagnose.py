"""Source-bound exposure boundaries and fail-closed qualification tests."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('s322_diagnose', HERE / 'diagnose.py')
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)


class ExposureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = d.diagnose()
        cls.graphs = json.loads((HERE.parent / 's283/diagnosis.json').read_text())
        cls.structural = json.loads((HERE.parent / 's291/diagnosis.json').read_text())['audit']

    def test_source_boundaries(self):
        rows = self.report['audit']['initialization_exposure']
        self.assertEqual([r['initializer']['index'] for r in rows], [234, 237, 240, 432])
        self.assertEqual([r['candidate']['boundaries']['overwrite'] for r in rows], [[353], [368], [381], [444]])
        for row in rows[:3]:
            self.assertEqual(row['candidate']['boundaries']['return'], [430, 465, 481, 504])
        self.assertEqual(rows[3]['candidate']['boundaries']['return'], [504])
        for row in rows:
            self.assertEqual(row['candidate']['boundaries']['body-end'], [543])
            self.assertEqual(row['original']['boundaries']['body-end'], [485])

    def test_calls_before_overwrite_are_retained(self):
        rows = self.report['audit']['initialization_exposure']
        for row in rows[:3]:
            self.assertEqual(row['candidate']['explicit_calls'], [251, 275, 287, 310, 319, 321, 326, 443])
            self.assertEqual(row['original']['explicit_calls'], [271, 385])
        self.assertEqual(rows[-1]['candidate']['explicit_calls'], [443])
        self.assertEqual(rows[-1]['original']['explicit_calls'], [385])

    def test_witness_paths_and_successor_closure(self):
        for region in self.report['audit']['initialization_exposure']:
            for side in ('original', 'candidate'):
                graph = self.graphs[side + '_projection']['nodes']
                rows = region[side]['rows']
                indices = {r['index'] for r in rows}
                for row in rows:
                    path = row['path']
                    self.assertEqual(path[-1], row['index'])
                    for a, b in zip(path, path[1:]):
                        self.assertIn(b, graph[a]['successors'])
                    if row['kind'] == 'intermediate':
                        self.assertTrue(set(row['node']['successors']) <= indices)
                    for i in path[:-1]:
                        self.assertNotEqual(graph[i]['instruction'], f"StoreRegister {region[side + '_register']}")
                        self.assertNotEqual(graph[i]['instruction'], 'Return')

    def test_coercion_read_is_scope_dependent_not_live_boolean(self):
        cut = self.report['audit']['coercion_cut']
        self.assertEqual([n['instruction'] for n in cut['original_window']],
                         ['Push "dashing"', 'GetVariable', 'Not', 'Not', 'If 159'])
        self.assertEqual([n['instruction'] for n in cut['candidate_window']],
                         ['Push "dashing"', 'GetVariable', 'If 169'])
        self.assertIsNone(cut['actual_type'])
        self.assertIsNone(cut['actual_value'])
        self.assertIsNone(cut['coercion_effect'])

    def test_unknowns_never_promoted(self):
        r = self.report
        self.assertFalse(r['production_admitted'])
        self.assertFalse(r['native_parity_proven'])
        self.assertEqual(r['m0_02_status'], 'pending')
        self.assertTrue(all(v is None for v in r['independent_live_observations'].values()))
        self.assertTrue(all(not v['proved'] for v in r['gates'].values()))
        self.assertIsNone(r['historical_execution_observed'])

    def test_full_body_mutation_rejected(self):
        graphs = copy.deepcopy(self.graphs)
        graphs['candidate_projection']['nodes'][540]['instruction'] = 'Pop'
        with self.assertRaises(ValueError):
            d.audit(graphs, self.structural)

    def test_invalid_edge_and_terminal_rejected(self):
        graph = copy.deepcopy(self.graphs['candidate_projection'])
        graph['nodes'][250]['successors'] = [99999]
        with self.assertRaisesRegex(ValueError, 'edge'):
            d.exposure(graph, 235, 7)
        graph['nodes'][250]['successors'] = []
        with self.assertRaisesRegex(ValueError, 'terminal'):
            d.exposure(graph, 235, 7)

    def test_hash_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'pins.json'
            p.write_text(json.dumps({'evidence/sampling-upgrade/s312/diagnose.py': '0' * 64}))
            with self.assertRaisesRegex(ValueError, 'Locked input'):
                d.load_prior().verify_pins(p)

    def test_all_proof_flags_fail_individually(self):
        with tempfile.TemporaryDirectory() as tmp:
            for flag, code in d.GATES.items():
                result = subprocess.run([sys.executable, str(HERE / 'diagnose.py'), '--output', str(Path(tmp) / 'r.json'), '--require-' + flag], capture_output=True, text=True)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertIn(code, result.stdout)


if __name__ == '__main__':
    unittest.main()
