"""Reject source drift and keep observation distinct from runtime admission."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('s275_build', ROOT / 'evidence/sampling-upgrade/s275/build_probe.py')
probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe)


class YulongOperandBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        scripts = json.loads((ROOT / 'scripts/fighter/yulong.json').read_text())['scripts']
        cls.source = next(s['source'].replace('\r\n', '\n') for s in scripts if s['path'] == probe.ENTER)

    def test_original_sites_once_and_authored_or_retained(self):
        result = probe.instrument(self.source, probe.sha_text(self.source))
        self.assertEqual(result.count('.hitTest('), 5)
        self.assertEqual(result.count(' or '), 4)
        self.assertEqual(result.count('hitmc.mian'), 1)
        for name in ('bdmn', 'zh1atm', 'zh2atm', 'zh3atm', 'abcd'):
            self.assertEqual(result.count('_parent.pn].mc.' + name), 1)
        self.assertNotIn('_parent._parent.pn', result)
        self.assertNotIn('var ', result)
        self.assertEqual(result.count('gotoAndPlay(5);'), 1)

    def test_changed_operand_and_guard_reject(self):
        for old, new in [('hitmc.mian', 'mian'), ('_parent.pn', '_parent._parent.pn'), ('played == 0', 'played != 0'), ('zhanting == false', 'zhanting == true')]:
            with self.subTest(old=old), self.assertRaises(ValueError):
                probe.instrument(self.source.replace(old, new), probe.sha_text(self.source))

    def test_observer_returns_same_value_and_never_calls_hit_test(self):
        source = (probe.HERE / 'observer.as').read_text()
        self.assertIn('return value;', source)
        self.assertNotIn('hitTest(', source)
        self.assertNotIn('.pn =', source)
        self.assertNotIn('gotoAnd', source)
        self.assertNotIn('removeMovieClip', source)
        self.assertIn('_root.aiFight < 15 || _root.aiFight > 22', source)


class YulongOperandEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import gzip
        spec = importlib.util.spec_from_file_location('s275_diagnose', probe.HERE / 'diagnose.py')
        cls.audit = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.audit)
        cls.lines = gzip.decompress((probe.HERE / 'native-capture.log.gz').read_bytes()).decode().splitlines()

    def test_projected_opcode_graph_and_eager_or(self):
        original = (probe.HERE / 'original.pcode').read_text()
        observed = (probe.HERE / 'observed.pcode').read_text()
        self.assertEqual(self.audit.pcode_projection(original), self.audit.pcode_projection(observed, True))
        self.assertEqual(original.splitlines().count('Or'), 4)
        self.assertNotEqual(self.audit.pcode_projection(original), self.audit.pcode_projection(observed.replace('Or', 'And', 1), True))
        self.assertNotEqual(self.audit.pcode_projection(original), self.audit.pcode_projection(observed.replace('Push "hitmc"', 'Push "mian"'), True))

    def test_complete_replay_is_not_binding_admission(self):
        report = self.audit.diagnose()
        self.assertEqual(report['actor_rows_equal_s247'], 122)
        self.assertFalse(report['runtime_binding_proved'])
        self.assertFalse(report['production_admitted'])
        self.assertFalse(report['native_parity_proven'])
        self.assertEqual(report['geometry_exit_code'], 1)

    def test_missing_operand_and_lifecycle_rows_reject(self):
        for marker in ('|s275_value|receiver4,', '|s275_boundary|after_goto,', '|s275_boundary|before_rename,', '|22|s275_boundary|root_slot,'):
            changed = [line for line in self.lines if marker not in line]
            with self.subTest(marker=marker), self.assertRaises(ValueError):
                self.audit.observations(changed)

    def test_true_first_result_does_not_skip_other_authored_sites(self):
        rows = self.audit.observations(self.lines)['values']
        tick18 = {r['fields'][0]:r['fields'] for r in rows if r['tick'] == 18}
        self.assertEqual(tick18['result1'][2], 'true')
        self.assertEqual(tick18['receiver4'][1:3], ['undefined', 'undefined'])
        self.assertEqual(tick18['result5'][2], 'false')


if __name__ == '__main__':
    unittest.main()
