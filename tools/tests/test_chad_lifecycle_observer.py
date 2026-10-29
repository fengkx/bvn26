import json
from pathlib import Path
import tempfile
import unittest

from tools.probes import chad_lifecycle_observer as observer
from tools.probes.callsite_observer import instrument as instrument_callsite
from tools.probes.doaction_observer import inventory

ROOT = Path(__file__).resolve().parents[2]


class ChadLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.bundle = json.loads((ROOT / 'scripts/fighter/chad.json').read_text())
        self.sources = {s['path']: s['source'] for s in self.bundle['scripts']}

    def test_source_calls_and_goto_remain_unmodified(self):
        source = self.sources[observer.CALLEE]
        result = observer.instrument(source, source, 'fighter/chad', observer.CALLEE)
        for phase in ('callee_enter', 'callee_exit', 'goto_before', 'goto_after'):
            result = result.replace(observer.event(phase), '')
        self.assertEqual(''.join(result.split()), ''.join(source.split()))

    def test_changed_source_rejects(self):
        source = self.sources[observer.CALLEE].replace('砍1', '砍2')
        with self.assertRaisesRegex(ValueError, 'changed Chad'):
            observer.instrument(source, source, 'fighter/chad', observer.CALLEE)

    def test_handler_preserves_original_unqualified_call(self):
        source = self.sources[observer.HANDLER]
        record = next(r for r in inventory(self.bundle, True) if r['path'] == observer.HANDLER)
        instrumented = instrument_callsite(source, record)
        result = observer.instrument(source, instrumented, 'fighter/chad', observer.HANDLER)
        self.assertEqual(result.count('doAllAction();'), 1)
        self.assertIn('call_after', result)
        self.assertIn(observer.event('caller_after'), result)

    def test_other_character_untouched(self):
        self.assertEqual(observer.instrument('x', 'y', 'fighter/Renji', observer.CALLEE), 'y')

    def test_only_original_case_is_allowed(self):
        path = ROOT / 'evidence/sampling-upgrade/s76/chad__attack__neutral__ground__near.json'
        observer.validate_case(path)
        case = json.loads(path.read_text())
        case['inputs'][0]['start'] = 11
        with tempfile.TemporaryDirectory() as temp:
            changed = Path(temp) / 'case.json'
            changed.write_text(json.dumps(case))
            with self.assertRaisesRegex(ValueError, 'unchanged s76'):
                observer.validate_case(changed)
        with self.assertRaises(ValueError):
            observer.validate_case(None)


class ChadLifecycleEvidenceTests(unittest.TestCase):
    def setUp(self):
        import gzip
        self.lines = gzip.open(ROOT / 'evidence/sampling-upgrade/s245/native-capture.log.gz', 'rt').read().splitlines()

    def test_actual_capture_keeps_missing_exits(self):
        from tools.sampling_chad_lifecycle import collect_lifecycle
        report = collect_lifecycle(self.lines)
        self.assertFalse(report['exit_observations_complete'])
        self.assertEqual(report['missing_boundaries'], ['goto_after', 'callee_exit', 'caller_after'])

    def test_missing_actual_observations_reject(self):
        from tools.sampling_chad_lifecycle import collect_lifecycle
        for phase in ('caller_before', 'callee_enter', 'goto_before', 'root_sample'):
            with self.subTest(phase=phase), self.assertRaises(ValueError):
                collect_lifecycle([line for line in self.lines if '|chad_lifecycle|' + phase + ',' not in line])

    def test_duplicate_observation_rejects(self):
        from tools.sampling_chad_lifecycle import collect_lifecycle
        row = next(line for line in self.lines if '|chad_lifecycle|' in line)
        with self.assertRaises(ValueError):
            collect_lifecycle(self.lines + [row])

    def test_changed_identity_rejects(self):
        from tools.sampling_chad_lifecycle import collect_lifecycle
        lines = [line.replace('instance257', 'instance999') if '|chad_lifecycle|root_sample,' in line else line for line in self.lines]
        with self.assertRaises(ValueError):
            collect_lifecycle(lines)


if __name__ == '__main__':
    unittest.main()
