"""Reject unsupported execution claims for the bounded s273 external callsite."""
import copy
import gzip
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('s273', ROOT / 'evidence/sampling-upgrade/s273/diagnose.py')
s273 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(s273)


class ExternalCollisionCallsiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = s273.diagnose()
        cls.prior = json.loads((s273.LOCKED / 'diagnosis.json').read_text())
        cls.raw = gzip.decompress((s273.LOCKED / 'native-capture.log.gz').read_bytes()).decode()
        scripts = json.loads((ROOT / 'scripts/fighter/yihu.json').read_text())['scripts']
        cls.source = next(s['source'] for s in scripts if s['path'] == s273.BODY)

    def test_replay_retains_unknown_execution(self):
        self.assertEqual(self.report['observed']['events'], 5437)
        self.assertEqual(self.report['observed']['post_init_query_rows'], 12)
        self.assertIsNone(self.report['site']['execution_observed'])
        for key in ('production_admitted', 'native_parity_proven', 'eligibility_fix_proved',
                    'external_callsite_execution_proved', 'all_collision_paths_observed'):
            self.assertFalse(self.report[key])

    def test_source_separates_receiver_and_target(self):
        site = self.report['site']
        self.assertEqual(site['receiver_expression'], 'bdmn')
        self.assertEqual(site['target_expression'], '_root.game["p" + pn].mc.bdmn')
        self.assertTrue(site['archived_function_identical'])
        self.assertFalse(site['callsite_instrumented'])

    def test_archived_observer_insertion_is_not_silently_accepted(self):
        changed = self.source.replace(s273.SITE, 'observe() || ' + s273.SITE)
        with self.assertRaisesRegex(ValueError, 'archived callback'):
            s273.audit_site(self.source, changed)

    def test_wrong_operand_or_removed_guard_rejected(self):
        for changed in (self.source.replace(s273.SITE, 'bdmn.hitTest(_parent)'),
                        self.source.replace('_loc3_ >= 0 && ', ''),
                        self.source.replace(s273.GUARD, 'if(true)')):
            with self.subTest(source=changed[:30]):
                with self.assertRaisesRegex(ValueError, 'operands or short-circuit'):
                    s273.audit_site(changed, changed)

    def test_ambiguous_function_rejected(self):
        with self.assertRaisesRegex(ValueError, 'ambiguous'):
            s273.function_source(self.source + self.source)

    def test_missing_boundary_event_rejected(self):
        raw = '\n'.join(line for line in self.raw.splitlines() if '|4057|' not in line)
        with self.assertRaisesRegex(ValueError, 'incomplete boundary'):
            s273.observe(raw, self.prior)

    def test_other_frame_or_interval_cannot_substitute(self):
        raw = self.raw.replace('|state|p2,5,', '|state|p2,8,')
        with self.assertRaisesRegex(ValueError, 'P2 sampled frames'):
            s273.observe(raw, self.prior)
        prior = copy.deepcopy(self.prior)
        prior['unready_interval']['initialized_sequence'] += 1
        with self.assertRaisesRegex(ValueError, 'initialization boundary'):
            s273.observe(self.raw, prior)

    def test_hash_mutation_rejects(self):
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            s273.check_hash(b'wrong-resource', '0' * 64)


if __name__ == '__main__':
    unittest.main()
