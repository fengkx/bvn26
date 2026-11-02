"""Protect explicit source dataflow without promoting it to native proof."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('s309_diagnose', HERE / 'diagnose.py')
analysis = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(analysis)


class DefinitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.locked = json.loads((HERE.parent / 's302/diagnosis.json').read_text())
        cls.result = analysis.diagnose()
        cls.audit = cls.result['audit']

    def test_replay_preserves_unknowns_and_scope(self):
        self.assertEqual(self.result['retained_events'], 5214)
        self.assertEqual(self.result['observations'], self.locked['observations'])
        self.assertTrue(all(v is None for v in self.result['observations'].values()))
        for field in ('production_admitted', 'native_parity_proven', 'activation_preservation_proved',
                      'observer_qualified', 'nested_entry_proved', 'direct_removal_dispatch_proved'):
            self.assertIs(self.result[field], False)
        self.assertEqual(self.result['other_ranks_executed'], [])
        self.assertEqual(self.result['new_captures'], 0)
        self.assertEqual(self.result['m0_02_status'], 'pending')

    def test_complete_raw_nodes_and_initializers_remain(self):
        for side, count in [('original', 87), ('s275_archive', 91)]:
            graph = self.audit['graphs'][side]
            self.assertEqual(len(graph), count)
            for node, raw in zip(graph, self.locked['getHitObj_audit'][side], strict=True):
                self.assertEqual({k: v for k, v in node.items() if k != 'edges'}, raw)
        self.assertEqual([r['added_initializer'] for r in self.audit['rows']], [9, 12])
        self.assertEqual([r['registers'] for r in self.audit['rows']],
                         [{'original': 2, 's275_archive': 6}, {'original': 4, 's275_archive': 7}])
        self.assertEqual(self.audit['activation_headers'], self.locked['activation_headers'])

    def test_source_reads_and_corresponding_stores(self):
        self.assertTrue(self.audit['static_overwrite_property'])
        self.assertTrue(self.audit['explicit_definition_correspondence'])
        for row, stores, count in zip(self.audit['rows'], [(20, 26), (27, 33)], [7, 2], strict=True):
            for side, store in zip(('original', 's275_archive'), stores, strict=True):
                self.assertEqual(len(row['reads'][side]), count)
                self.assertTrue(all(r['definitions'] == [store] for r in row['reads'][side]))

    def test_every_witness_path_has_correct_last_store(self):
        for row in self.audit['rows']:
            for side, reads in row['reads'].items():
                graph = self.audit['graphs'][side]
                for read in reads:
                    for witness in read['witnesses']:
                        path = witness['path']
                        self.assertEqual(path[0], 0)
                        self.assertEqual(path[-1], read['read'])
                        for a, b in zip(path, path[1:]):
                            self.assertIn(b, graph[a]['edges'])
                        stores = [i for i in path[:-1] if graph[i]['op'] == 'StoreRegister'
                                  and graph[i]['operand'] == [row['role']]]
                        self.assertEqual(stores[-1] if stores else -1, witness['definition'])

    def test_independent_backward_traversal(self):
        for row in self.audit['rows']:
            for side, reads in row['reads'].items():
                graph = self.audit['graphs'][side]
                predecessors = {n['id']: [] for n in graph}
                for n in graph:
                    for e in n['edges']:
                        predecessors[e].append(n['id'])
                for read in reads:
                    pending, seen, definitions = list(predecessors[read['read']]), set(), set()
                    while pending:
                        i = pending.pop()
                        if i in seen:
                            continue
                        seen.add(i)
                        n = graph[i]
                        if n['op'] == 'StoreRegister' and n['operand'] == [row['role']]:
                            definitions.add(i)
                        else:
                            if i == 0:
                                definitions.add(-1)
                            pending.extend(predecessors[i])
                    self.assertEqual(sorted(definitions), read['definitions'])

    def test_bypassing_each_real_store_exposes_added_initialization(self):
        for role, store, initializer in [('_loc2_', 26, 9), ('_loc4_', 33, 12)]:
            graph = copy.deepcopy(self.audit['graphs']['s275_archive'])
            graph[store - 1]['edges'] = [store + 1]
            reads = analysis.reaching_reads(graph, role)
            self.assertTrue(reads)
            self.assertTrue(all(initializer in r['definitions'] for r in reads))

    def test_removed_original_store_exposes_unknown_entry(self):
        for role, store in [('_loc2_', 20), ('_loc4_', 27)]:
            graph = copy.deepcopy(self.audit['graphs']['original'])
            graph[store]['op'] = 'Pop'
            self.assertTrue(all(-1 in r['definitions'] for r in analysis.reaching_reads(graph, role)))

    def test_synthetic_loop_and_unreachable_store(self):
        # Algorithm tests only; these graphs are not Flash evidence.
        graph = [{'id': 0, 'offset': 0, 'op': 'Push', 'operand': ['register', 'x'], 'edges': [1]},
                 {'id': 1, 'offset': 1, 'op': 'StoreRegister', 'operand': ['x'], 'edges': [0]}]
        self.assertEqual(analysis.reaching_reads(graph, 'x')[0]['definitions'], [-1, 1])
        graph[0]['edges'] = []
        self.assertEqual(analysis.reaching_reads(graph, 'x')[0]['definitions'], [-1])

    def test_invalid_raw_identity_or_branch_rejected(self):
        nodes = copy.deepcopy(self.locked['getHitObj_audit']['original'])
        nodes[0]['id'] = 99
        with self.assertRaisesRegex(ValueError, 'identity'):
            analysis.raw_graph(nodes)
        nodes = copy.deepcopy(self.locked['getHitObj_audit']['original'])
        next(n for n in nodes if n['op'] == 'If')['target'] = 9999
        with self.assertRaisesRegex(ValueError, 'edge'):
            analysis.raw_graph(nodes)

    def test_changed_projection_rejected(self):
        locked = copy.deepcopy(self.locked)
        locked['getHitObj_audit']['archived_projection']['rewrites'][0]['activation_visible_erasure_proved'] = True
        with self.assertRaisesRegex(ValueError, 'projection changed'):
            analysis.audit(locked)

    def test_changed_locked_replay_rejected(self):
        prior = analysis.load_prior()
        changed = copy.deepcopy(self.locked)
        changed['observations']['invented'] = True
        with patch.object(prior, 'diagnose', return_value=changed), patch.object(analysis, 'load_prior', return_value=prior):
            with self.assertRaisesRegex(ValueError, 'locked s302 diagnosis changed'):
                analysis.diagnose()

    def test_hash_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            pins = Path(directory) / 'pins.json'
            pins.write_text(json.dumps({'evidence/sampling-upgrade/s302/diagnosis.json': '0' * 64}))
            with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                analysis.verify_pins(pins)


if __name__ == '__main__':
    unittest.main()
