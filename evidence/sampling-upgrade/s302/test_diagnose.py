"""Protect complete byte coverage and the conditional/unproved distinction."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('s302', HERE / 'diagnose.py')
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


class CorrespondenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = audit.diagnose()
        cls.functions = json.loads((HERE.parent / 's294/diagnosis.json').read_text())['compiled_nested_functions']
        cls.original = cls.functions['original']['functions'][4]
        cls.archived = cls.functions['s275_archive']['functions'][4]

    def test_replay_and_unknowns(self):
        self.assertTrue(self.result['locked_s294_reproduced'])
        self.assertEqual(self.result['retained_events'], 5214)
        for field in ('production_admitted', 'native_parity_proven', 'complete_correspondence_proved',
                      'observer_qualified', 'direct_removal_dispatch_proved', 'nested_entry_proved'):
            self.assertIs(self.result[field], False)
        self.assertTrue(all(x is None for x in self.result['observations'].values()))
        self.assertEqual(self.result['paired_controls'], 0)
        self.assertIsNone(self.result['observer_effects']['perturbation_bound'])

    def test_all_bytes_and_nodes_accounted_for(self):
        result = self.result['getHitObj_audit']
        self.assertEqual(len(result['node_pairs']), 80)
        for side, function in [('original', self.original), ('s275_archive', self.archived)]:
            nodes = result[side]
            rows = {n['offset']: n['raw_hex'] for n in nodes}
            self.assertEqual(''.join(rows.values()), function['body_hex'])
            self.assertEqual(len(rows), len(function['instructions']))
        self.assertTrue(result['conditional_graph_equal'])
        self.assertFalse(result['complete_correspondence_proved'])

    def test_added_initializations_are_explicit_not_proved_erasure(self):
        rows = self.result['getHitObj_audit']['archived_projection']['rewrites']
        erased = [x for x in rows if x['kind'] == 'conditional_initializer_erasure']
        self.assertEqual([x['role'] for x in erased], ['_loc2_', '_loc4_'])
        self.assertTrue(all(x['activation_visible_erasure_proved'] is False for x in erased))
        nodes = audit.decode(self.archived, audit.ROLES['s275_archive'])
        self.assertEqual(len(audit.graph(nodes)['nodes']), 86)
        self.assertEqual(len(audit.graph(nodes, True)['nodes']), 80)

    def test_parameter_register_roles(self):
        for side, function in [('original', self.original), ('s275_archive', self.archived)]:
            self.assertEqual([audit.ROLES[side][p['register']] for p in function['parameters']],
                             ['array', 'player', 'afterFix', 'ppw'])
        self.assertEqual(self.original['register_count'], 15)
        self.assertEqual(self.archived['register_count'], 9)

    def test_changed_constant_operand_rejected(self):
        function = copy.deepcopy(self.archived)
        pool = function['constant_pool']
        pool[pool.index('hitTest')] = 'synthetic_call'
        with self.assertRaisesRegex(ValueError, 'correspondence'):
            audit.correspondence(self.original, function)

    def test_missing_instruction_rejected(self):
        function = copy.deepcopy(self.original)
        del function['instructions'][10]
        with self.assertRaisesRegex(ValueError, 'coverage'):
            audit.decode(function, audit.ROLES['original'])

    def test_changed_body_hash_rejected(self):
        function = copy.deepcopy(self.archived)
        function['body_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'custody'):
            audit.decode(function, audit.ROLES['s275_archive'])

    def test_unmapped_register_rejected(self):
        roles = dict(audit.ROLES['original'])
        del roles[12]
        with self.assertRaisesRegex(ValueError, 'unmapped'):
            audit.decode(self.original, roles)

    def test_changed_branch_target_metadata_rejected(self):
        function = copy.deepcopy(self.archived)
        branch = next(r for r in function['instructions'] if 'branch_target' in r)
        branch['branch_target'] += 1
        with self.assertRaisesRegex(ValueError, 'branch bytes'):
            audit.decode(function, audit.ROLES['s275_archive'])

    def test_wrong_branch_bytes_rejected_by_correspondence(self):
        function = copy.deepcopy(self.archived)
        branch = next(r for r in function['instructions'] if 'branch_target' in r)
        raw = bytes.fromhex(branch['hex'])[:3] + b'\0\0'
        branch['hex'] = raw.hex()
        branch['branch_target'] = branch['end']
        body = b''.join(bytes.fromhex(r['hex']) for r in function['instructions'])
        function['body_hex'], function['body_sha256'] = body.hex(), audit.sha(body)
        with self.assertRaisesRegex(ValueError, 'mapping|correspondence|uncovered'):
            audit.correspondence(self.original, function)

    def test_call_operands_keep_target_before_this(self):
        nodes = self.result['getHitObj_audit']['original']
        call = next(n['id'] for n in nodes if n['op'] == 'CallMethod')
        self.assertEqual([n['operand'] for n in nodes[call-4:call]],
                         [['register', '_loc4_'], ['integer', 1], ['register', 'this'], ['string', 'hitTest']])
        self.assertEqual(sum(n['op'] == 'CallMethod' for n in nodes), 1)
        self.assertEqual(sum(n['op'] == 'Return' for n in nodes), 2)

    def test_observer_writes_and_ancestor_read_are_disclosed(self):
        effects = self.result['observer_effects']
        stamp = effects['sources']['aiGeoStamp']['source']
        self.assertIn('++_root.aiGeoSerial', stamp)
        self.assertIn('mc.__aiGeoBirth = _root.aiDisplay', stamp)
        self.assertIn('grandparent.pn', effects['sources']['aiK1Observe']['source'])
        self.assertIn('++aiSeq', effects['sources']['aiEvent']['source'])
        self.assertFalse(effects['complete_compiled_helper_preservation_proved'])
        self.assertIsNone(effects['independent_observer_off_on'])


if __name__ == '__main__':
    unittest.main()
