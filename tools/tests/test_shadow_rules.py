import unittest
from tools.importer.build_shadow_rules import build, checked_function


class ShadowRulesTest(unittest.TestCase):
    def test_all_fighter_wrappers_share_the_audited_service(self):
        spec = build()
        self.assertEqual(len(spec['sources']), 36)
        self.assertEqual(spec['counter_skip_above'], 1)
        self.assertEqual((spec['alpha_start'], spec['alpha_lose']), (100, 10))
        self.assertEqual(spec['layer_depth'], 5)

    def test_changed_fade_or_pause_condition_is_rejected(self):
        source = build()['sources'][0]['function']
        for changed in [source.replace('this._alpha -=', 'this._alpha +='),
                        source.replace('this._alpha -=', 'if(_root.zhanting) return; this._alpha -=')]:
            with self.assertRaises(ValueError):
                checked_function(changed, 'shadowEffect')

    def test_changed_call_cadence_is_rejected(self):
        source = build()['sources'][1]['function']
        with self.assertRaises(ValueError):
            checked_function(source.replace('++_si > 1', '++_si > 2'), 'showdow')
