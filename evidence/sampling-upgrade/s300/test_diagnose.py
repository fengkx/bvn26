"""Protect source-bound dataflow and the distinction from runtime proof."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('s300_diagnose', HERE / 'diagnose.py')
analysis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analysis)


class DefinitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graphs = json.loads((HERE.parent / 's283/diagnosis.json').read_text())
        cls.structural = json.loads((HERE.parent / 's291/diagnosis.json').read_text())['audit']
        cls.result = analysis.diagnose()

    def test_historical_replay_does_not_promote_runtime(self):
        self.assertEqual(self.result['historical_events_revalidated'], 5437)
        self.assertIsNone(self.result['historical_execution_observed'])
        for key in ('production_admitted', 'native_parity_proven',
                    'activation_preservation_proved', 'observer_qualified',
                    'external_callsite_execution_proved'):
            self.assertIs(self.result[key], False)
        self.assertEqual(self.result['new_captures'], 0)
        self.assertEqual(len(self.result['audit']['remaining_obligations']), 5)

    def test_all_four_initializations_and_eight_reads_are_accounted(self):
        rows = self.result['audit']['rows']
        self.assertEqual([r['candidate_register'] for r in rows], [7, 8, 9, 12])
        self.assertEqual([r['original_register'] for r in rows], [8, 5, 11, 9])
        self.assertEqual(sum(len(r['candidate_reads']) for r in rows), 8)
        self.assertTrue(self.result['audit']['static_overwrite_property'])
        self.assertNotEqual(*self.result['audit']['headers_preserved_verbatim'].values())

    def test_each_witness_is_an_actual_archived_path_with_last_store(self):
        for row in self.result['audit']['rows']:
            for side in ('candidate', 'original'):
                nodes = self.graphs[side + '_projection']['nodes']
                register = row[side + '_register']
                for read in row[side + '_reads']:
                    for witness in read['witness_paths']:
                        path = witness['node_indices']
                        self.assertEqual(path[0], 0)
                        self.assertEqual(path[-1], read['read_index'])
                        for a, b in zip(path, path[1:]):
                            self.assertIn(b, nodes[a]['successors'])
                        stores = [i for i in path[:-1] if nodes[i]['instruction'] == f'StoreRegister {register}']
                        self.assertEqual(stores[-1] if stores else -1, witness['definition_index'])

    def test_independent_backward_walk_confirms_every_reaching_definition(self):
        for row in self.result['audit']['rows']:
            for side in ('candidate', 'original'):
                nodes = self.graphs[side + '_projection']['nodes']
                predecessors = {i: [] for i in range(len(nodes) + 1)}
                for node in nodes:
                    for successor in node['successors']:
                        predecessors[successor].append(node['index'])
                for read in row[side + '_reads']:
                    pending = list(predecessors[read['read_index']])
                    visited, definitions = set(), set()
                    while pending:
                        i = pending.pop()
                        if i in visited:
                            continue
                        visited.add(i)
                        if nodes[i]['instruction'] == f"StoreRegister {row[side + '_register']}":
                            definitions.add(i)
                        else:
                            if i == 0:
                                definitions.add(-1)
                            pending.extend(predecessors[i])
                    self.assertEqual(sorted(definitions), read['reaching_definitions'])

    def test_bypass_of_real_store_exposes_initial_value(self):
        graph = copy.deepcopy(self.graphs['candidate_projection'])
        # Deliberately corrupt a real edge to bypass the final register12 store.
        graph['nodes'][433]['successors'] = [447]
        read = next(r for r in analysis.reaching_reads(graph, 12) if r['read_index'] == 447)
        self.assertIn(432, read['reaching_definitions'])
        with self.assertRaises(ValueError):
            analysis.audit(self.graphs['original_projection'], graph, self.structural)

    def test_removed_real_store_exposes_entry_value(self):
        graph = copy.deepcopy(self.graphs['original_projection'])
        graph['nodes'][386]['instruction'] = 'Pop'
        reads = analysis.reaching_reads(graph, 9)
        self.assertTrue(all(-1 in r['reaching_definitions'] for r in reads))

    def test_loop_keeps_both_initial_and_backedge_definitions(self):
        # Synthetic graph tests the algorithm, not a Flash schedule or outcome.
        graph = {'nodes': [
            {'index': 0, 'instruction': 'Push register7', 'successors': [1]},
            {'index': 1, 'instruction': 'StoreRegister 7', 'successors': [0, 2]},
        ]}
        self.assertEqual(analysis.reaching_reads(graph, 7)[0]['reaching_definitions'], [-1, 1])

    def test_unreachable_store_does_not_supply_definition(self):
        graph = {'nodes': [
            {'index': 0, 'instruction': 'Push register7', 'successors': [2]},
            {'index': 1, 'instruction': 'StoreRegister 7', 'successors': [0]},
        ]}
        self.assertEqual(analysis.reaching_reads(graph, 7)[0]['reaching_definitions'], [-1])

    def test_invalid_edges_and_indices_rejected(self):
        for field, value in [('successors', [9999]), ('index', 9999)]:
            graph = copy.deepcopy(self.graphs['candidate_projection'])
            graph['nodes'][0][field] = value
            with self.assertRaises(ValueError):
                analysis.reaching_reads(graph, 7)

    def test_header_or_erasure_metadata_changes_rejected(self):
        for key in ('original_header', 'candidate_erasure'):
            changed = copy.deepcopy(self.structural)
            changed[key] = '' if key == 'original_header' else []
            with self.assertRaisesRegex(ValueError, 'correspondence changed'):
                analysis.audit(self.graphs['original_projection'], self.graphs['candidate_projection'], changed)

    def test_read_remapping_rejected(self):
        graph = copy.deepcopy(self.graphs['candidate_projection'])
        graph['nodes'][396]['instruction'] = 'Push register8'
        with self.assertRaises(ValueError):
            analysis.audit(self.graphs['original_projection'], graph, self.structural)

    def test_hash_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'pins.json'
            path.write_text(json.dumps({'evidence/sampling-upgrade/s291/diagnosis.json': '0' * 64}))
            with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                analysis.verify_pins(path)


if __name__ == '__main__':
    unittest.main()
