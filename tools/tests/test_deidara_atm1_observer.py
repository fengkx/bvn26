import json
from pathlib import Path
import tempfile
import unittest

from tools.probes import deidara_atm1_observer as observer

ROOT = Path(__file__).resolve().parents[2]


class Atm1ObserverTests(unittest.TestCase):
    def setUp(self):
        bundle = json.loads((ROOT / 'scripts/fighter/fz/woailuo.json').read_text())
        self.source = next(s['source'] for s in bundle['scripts'] if s['path'] == observer.LOAD_PATH)

    def test_load_body_is_preserved(self):
        result = observer.instrument_load(self.source, self.source, 'fighter/fz/woailuo', observer.LOAD_PATH)
        for phase in ('load_before', 'load_after'):
            result = result.replace(f'_root.aiAtm1Observe("{phase}",this,"{observer.LOAD_SOURCE}");', '')
        self.assertEqual(''.join(result.split()), ''.join(self.source.split()))

    def test_changed_load_rejects(self):
        source = self.source.replace('_xscale < 0', '_xscale > 0')
        with self.assertRaisesRegex(ValueError, 'changed Woailuo'):
            observer.instrument_load(source, source, 'fighter/fz/woailuo', observer.LOAD_PATH)

    def test_stamp_assignment_and_fail_loud_body_unchanged(self):
        source = (ROOT / 'tools/probes/as2/ai_reference/sampling_geometry.as').read_text()
        result = observer.instrument_stamp(source)
        for phase in ('stamp_before', 'stamp_after'):
            result = result.replace(f'\n   _root.aiAtm1StampObserve("{phase}",mc,source);', '')
        self.assertEqual(source, result)
        with self.assertRaises(ValueError):
            observer.instrument_stamp(source.replace('function(mc, source)', 'function(mc)'))

    def test_unrelated_source_is_untouched(self):
        self.assertEqual(observer.instrument_load('x', 'y', 'fighter/fz/kon', observer.LOAD_PATH), 'y')

    def test_changed_tape_rejects(self):
        path = ROOT / 'evidence/sampling-upgrade/s64/didala__summon__neutral__ground__near.json'
        observer.validate_case(path)
        case = json.loads(path.read_text()); case['frames'] = 90
        with tempfile.TemporaryDirectory() as temp:
            other = Path(temp) / 'case.json'; other.write_text(json.dumps(case))
            with self.assertRaises(ValueError):
                observer.validate_case(other)
        with self.assertRaises(ValueError):
            observer.validate_case(None)


class Atm1EvidenceTests(unittest.TestCase):
    def setUp(self):
        import gzip
        self.lines = gzip.open(ROOT / 'evidence/sampling-upgrade/s246/native-capture.log.gz', 'rt').read().splitlines()

    def test_retained_observations_do_not_admit_binding(self):
        from tools.sampling_atm1_provenance import collect_provenance
        report = collect_provenance(self.lines)
        self.assertTrue(report['observation_complete'])
        self.assertFalse(report['stamp_binding_complete'])
        self.assertEqual([g['tick'] for g in report['live_candidate_stamp_gaps']], [58, 59, 60])
        for gap in report['live_candidate_stamp_gaps']:
            self.assertEqual(gap['missing_fields'], ['stamp_id', 'stamp_source', 'stamp_birth'])

    def test_missing_observation_rejects(self):
        from tools.sampling_atm1_provenance import collect_provenance
        for phase in ('root_sample', 'load_before', 'load_after', 'stamp_before', 'stamp_after'):
            row = next(l for l in self.lines if '|atm1_provenance|' + phase + ',' in l)
            with self.subTest(phase=phase), self.assertRaises(ValueError):
                collect_provenance([l for l in self.lines if l != row])

    def test_wrong_source_rejects(self):
        from tools.sampling_atm1_provenance import collect_provenance
        with self.assertRaises(ValueError):
            collect_provenance([l.replace('woailuo', 'kon') if '|atm1_provenance|' in l else l for l in self.lines])

    def test_duplicate_observation_rejects(self):
        from tools.sampling_atm1_provenance import collect_provenance
        row = next(l for l in self.lines if '|atm1_provenance|load_after,' in l)
        with self.assertRaises(ValueError):
            collect_provenance(self.lines + [row])


if __name__ == '__main__':
    unittest.main()
