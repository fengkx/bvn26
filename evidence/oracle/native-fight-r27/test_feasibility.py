"""Capability availability must not be promoted to semantic witness qualification."""
import unittest
from analyze import FLAGS, replay, source_inventory, assess

class FeasibilityTests(unittest.TestCase):
    def test_locked_source_scope(self):
        result = replay()
        for inventory in result['source_inventories'].values():
            self.assertEqual(inventory['unload_callbacks'], [])
        calls = result['source_inventories']['scripts/fighter/yihu.json']['explicit_calls']
        self.assertEqual(len(calls), 4)
        self.assertFalse(any(c['path'].startswith('DefineSprite_16/') for c in calls))

    def test_handler_detection_is_distinct_from_explicit_call(self):
        x = source_inventory({'scripts': [dict(path='example', source='this.unloadMovie();')]})
        self.assertEqual(x['unload_callbacks'], [])
        x = source_inventory({'scripts': [dict(path='example', source='onUnload = function() {};')]})
        self.assertEqual(x['unload_callbacks'], ['example'])

    def test_historical_success_is_not_current_witness(self):
        result = replay(); caps = result['historical_capabilities']
        self.assertTrue(caps['owned_attach_registers_detach'])
        self.assertTrue(caps['generic_hardware_entry'])
        self.assertEqual(caps['historical_task_for_pid_return'], 5)
        self.assertFalse(caps['independent_guest_read'])
        self.assertFalse(caps['per_instance_dispatch_binding_proven'])
        self.assertEqual(caps['current_permission_state'], 'not tested')

    def test_even_synthetic_all_capabilities_do_not_admit(self):
        result = assess({'synthetic': {'unload_callbacks': ['a']}},
                        {'debugger': {'attached': True, 'registers_available': True, 'detached': True}},
                        {'hardware_entry_verified': True},
                        {'guest_entry_before': {'guest_virtual_read_verified': True, 'task_for_pid_return': 0}})
        self.assertFalse(any(c['ready'] for c in result['candidates']))
        for flag in FLAGS:
            self.assertIs(result[flag], False)
        self.assertFalse(result['global_impossibility_proven'])

    def test_structural_refusal_and_no_new_live(self):
        result = replay()
        self.assertEqual(result['structural_refusal'], 'Incomplete actor state at clock boundary')
        self.assertFalse(result['new_live'])
        self.assertFalse(result['new_observer'])
        self.assertFalse(result['native_return_proven'])
        self.assertFalse(result['removal_edge_proven'])
        self.assertEqual(result['r25_identity_refusal'][0]['classification'], 'body-target-observed-dispatch-identity-unjoined')
