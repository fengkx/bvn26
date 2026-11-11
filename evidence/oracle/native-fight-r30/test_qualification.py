"""Negative regressions for the reviewed initialization scope, not player tests."""
import unittest
import analyze


class InitializationReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = analyze.r29.read_sources()[analyze.PLAYER]

    def test_unknown_send_requires_review(self):
        changed = self.source.replace('sendStopWarning();', 'sendNewOption();\n sendStopWarning();', 1)
        with self.assertRaises(ValueError):
            analyze.audit_initialization(changed)

    def test_changed_option_requires_review(self):
        with self.assertRaises(ValueError):
            analyze.audit_initialization(self.source.replace('"invoke_setters"', '"different_option"'))

    def test_missing_timeout_requires_review(self):
        with self.assertRaises(ValueError):
            analyze.audit_initialization(self.source.replace('sendGetterTimeout();', '', 1))

    def test_disconnect_restoration_not_invented(self):
        report = analyze.audit_initialization(self.source)
        self.assertFalse(report['prior_option_restoration_in_reviewed_unbind'])
        self.assertEqual(report['player_reset_on_disconnect'], 'unproved')

    def test_decoded_id_cannot_change_silently(self):
        sources = analyze.r29.read_sources()
        key = analyze.PLAYER.replace('PlayerSession.java', 'DManager.java')
        sources[key] = sources[key].replace('value = new Long(oid);', 'value = new Long(0);')
        with self.assertRaises(ValueError):
            analyze.audit_id_chain(sources, analyze.read_new_sources())

    def test_value_id_forward_cannot_change_silently(self):
        new = analyze.read_new_sources()
        new['DValue.java'] = new['DValue.java'].replace('return ((Long)m_value).longValue();', 'return 0;')
        with self.assertRaises(ValueError):
            analyze.audit_id_chain(analyze.r29.read_sources(), new)

    def test_no_promotion_from_static_review(self):
        report = analyze.analyze()
        for flag in analyze.r29.FLAGS:
            self.assertIs(report[flag], False)
        self.assertIsNone(report['native_boundary'])
        self.assertFalse(report['exact_player_producer_qualified'])
        self.assertFalse(report['placement_remove_value_namespace_equivalence_proven'])
        self.assertEqual(report['historical_structural_refusal'], 'Incomplete actor state at clock boundary')


if __name__ == '__main__':
    unittest.main()
