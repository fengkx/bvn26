"""Protect source-bound frontier results and missing-evidence boundaries."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('s318_diagnose', HERE / 'diagnose.py')
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)


class FrontierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = d.diagnose()
        cls.prior = json.loads((HERE.parent / 's309/diagnosis.json').read_text())
        cls.structural = json.loads((HERE.parent / 's302/diagnosis.json').read_text())

    def test_retained_result(self):
        self.assertEqual(self.report, json.loads((HERE / 'diagnosis.json').read_text()))
        self.assertEqual(self.report['retained_events'], 5214)

    def test_source_bound_frontiers(self):
        for row, overwrite in zip(self.report['audit']['rows'], (26, 33)):
            self.assertEqual(row['s275_archive']['overwrites'], [overwrite])
            self.assertEqual(row['s275_archive']['returns_before_overwrite'], [90])
            self.assertEqual(row['original']['returns_before_overwrite'], [86])
            self.assertEqual(row['s275_archive']['explicit_calls_before_overwrite'], [])
            self.assertIsNone(row['activation_visible_effect'])

    def test_all_witness_edges_and_no_early_store(self):
        for row in self.report['audit']['rows']:
            for side in ('original', 's275_archive'):
                graph = self.prior['audit']['graphs'][side]
                for witness in row[side]['rows']:
                    path = witness['witness_path']
                    self.assertEqual(path[0], row[side]['start'])
                    self.assertEqual(path[-1], witness['node']['id'])
                    for a, b in zip(path, path[1:]):
                        self.assertIn(b, graph[a]['edges'])
                        self.assertFalse(graph[a]['op'] == 'StoreRegister' and graph[a]['operand'] == [row['role']])

    def test_independent_reverse_reachability(self):
        # Backward search from every node independently validates membership.
        for row in self.report['audit']['rows']:
            for side in ('original', 's275_archive'):
                graph = self.prior['audit']['graphs'][side]
                incoming = {i: [] for i in range(len(graph))}
                for node in graph:
                    if node['op'] == 'StoreRegister' and node['operand'] == [row['role']]:
                        continue
                    for edge in node['edges']:
                        incoming[edge].append(node['id'])
                reachable = set()
                for target in incoming:
                    pending, seen = [target], set()
                    while pending:
                        node = pending.pop()
                        if node in seen:
                            continue
                        seen.add(node)
                        pending.extend(incoming[node])
                    if row[side]['start'] in seen:
                        reachable.add(target)
                self.assertEqual(reachable, {r['node']['id'] for r in row[side]['rows']})

    def test_removing_real_store_exposes_call(self):
        for role, start, store in (('_loc2_', 10, 26), ('_loc4_', 13, 33)):
            graph = copy.deepcopy(self.prior['audit']['graphs']['s275_archive'])
            graph[store]['operand'] = ['different_role']
            result = d.frontier(graph, start, role)
            self.assertEqual(result['explicit_calls_before_overwrite'], [42])
            self.assertEqual(result['returns_before_overwrite'], [87, 90])

    def test_removing_null_exit_does_not_invent_return(self):
        graph = copy.deepcopy(self.prior['audit']['graphs']['s275_archive'])
        graph[19]['edges'] = [20]
        result = d.frontier(graph, 10, '_loc2_')
        self.assertEqual(result['returns_before_overwrite'], [])
        self.assertEqual(result['overwrites'], [26])

    def test_cycle_terminates_and_unreachable_nodes_stay_out(self):
        graph = [dict(id=0, op='If', operand=[], edges=[0, 1]),
                 dict(id=1, op='Return', operand=[], edges=[]),
                 dict(id=2, op='CallMethod', operand=[], edges=[1])]
        result = d.frontier(graph, 0, 'slot')
        self.assertEqual([r['node']['id'] for r in result['rows']], [0, 1])
        self.assertEqual(result['explicit_calls_before_overwrite'], [])

    def test_bad_edges_and_silent_terminal_rejected(self):
        for edges in ([999], []):
            graph = copy.deepcopy(self.prior['audit']['graphs']['s275_archive'])
            graph[15]['edges'] = edges
            with self.assertRaises(ValueError):
                d.frontier(graph, 10, '_loc2_')

    def test_full_graph_mutation_outside_cut_rejected(self):
        prior = copy.deepcopy(self.prior)
        prior['audit']['graphs']['original'][80]['op'] = 'Pop'
        with self.assertRaisesRegex(ValueError, 'Full graph'):
            d.audit(prior, self.structural)

    def test_correspondence_mutation_rejected(self):
        structural = copy.deepcopy(self.structural)
        structural['getHitObj_audit']['node_pairs'][0]['original'] = 999
        with self.assertRaises(ValueError):
            d.audit(self.prior, structural)

    def test_wrong_pin_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'pins.json'
            path.write_text(json.dumps({'evidence/sampling-upgrade/s309/diagnosis.json': '0' * 64}))
            with self.assertRaisesRegex(ValueError, 'Locked input changed'):
                d.verify_pins(path)

    def test_no_runtime_admission_from_static_success(self):
        for field in ('production_admitted', 'native_parity_proven'):
            self.assertIs(self.report[field], False)
        self.assertEqual(self.report['m0_02_status'], 'pending')
        self.assertEqual(self.report['other_ranks_executed'], [])
        self.assertTrue(all(g['proved'] is False for g in self.report['gates'].values()))
        self.assertEqual(self.report['observations'], self.prior['observations'])


if __name__ == '__main__':
    unittest.main()
