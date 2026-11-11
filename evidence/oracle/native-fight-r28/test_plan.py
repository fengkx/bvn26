"""Reject converting a requirements document or generic opcode into proof."""
import copy
import json
import unittest
from analyze import HERE, FLAGS, call_interval, check_plan, replay

class PlanTests(unittest.TestCase):
    def setUp(self):
        self.schema = json.loads((HERE / 'identity-requirements.json').read_text())
        self.plan = json.loads((HERE / 'preservation-plan.json').read_text())

    def test_current_bounds_remain_unqualified(self):
        r = replay()
        self.assertIsNone(r['qualified_native_boundary'])
        self.assertFalse(any(c['applicable'] for c in r['candidates']))
        self.assertFalse(r['candidates'][2]['reachable_instruction_boundary'])
        self.assertEqual(r['structural_refusal'], 'Incomplete actor state at clock boundary')
        for flag in FLAGS:
            self.assertIs(r[flag], False)
        self.assertFalse(r['native_return_proven'])

    def test_offset_or_type_name_cannot_fill_schema(self):
        for key, value in [('native_location', '[rax+0x40]'), ('verified_type', 'owner'),
                           ('independent_witness', 'same timestamp')]:
            schema = copy.deepcopy(self.schema)
            schema['fields'][1][key] = value
            with self.assertRaisesRegex(ValueError, 'No qualified native field'):
                check_plan(schema, self.plan)

    def test_missing_or_duplicate_identity_requirement_refused(self):
        for fields in [self.schema['fields'][:-1], self.schema['fields'] + [self.schema['fields'][0]]]:
            schema = copy.deepcopy(self.schema); schema['fields'] = fields
            with self.assertRaisesRegex(ValueError, 'missing/duplicated'):
                check_plan(schema, self.plan)

    def test_unexecuted_controls_cannot_be_marked_passed(self):
        plan = copy.deepcopy(self.plan); plan['qualified'] = True
        with self.assertRaises(ValueError): check_plan(self.schema, plan)
        plan = copy.deepcopy(self.plan); plan['stages'][0]['performed'] = True
        with self.assertRaises(ValueError): check_plan(self.schema, plan)
        schema = copy.deepcopy(self.schema); schema['schema_verified'] = True
        with self.assertRaises(ValueError): check_plan(schema, self.plan)

    def test_retained_interval_is_inner_call_not_return(self):
        r = replay(); text = r['source_call_interval']; tag = 'm002-r25-live-20261112-f19d'
        self.assertEqual(call_interval(text, tag), text)
        self.assertEqual(text.count('CallMethod'), 1)
        with self.assertRaises(ValueError): call_interval(text.replace('Pop', 'Return'), tag)
        with self.assertRaises(ValueError): call_interval(text.replace('gotoAndPlay', 'unloadMovie'), tag)
        with self.assertRaises(ValueError): call_interval(text + text, tag)
