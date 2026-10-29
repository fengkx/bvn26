import json
from pathlib import Path
import tempfile
import unittest

from tools.probes import yulong_k1atm_observer as observer

ROOT = Path(__file__).resolve().parents[2]


class YulongK1ObserverTests(unittest.TestCase):
    def setUp(self):
        bundle = json.loads((ROOT / 'scripts/fighter/yulong.json').read_text())
        self.source = next(s['source'] for s in bundle['scripts'] if s['path'] == observer.SOURCE_PATH)

    def test_original_initializer_is_unchanged(self):
        result = observer.instrument_source(self.source, self.source, 'fighter/yulong', observer.SOURCE_PATH)
        self.assertTrue(result.startswith(self.source))
        self.assertNotIn('__aiGeoId =', result[len(self.source):])
        self.assertNotIn('.pn =', result[len(self.source):])

    def test_changed_source_rejects(self):
        source = self.source.replace('"atm1"', '"other"')
        with self.assertRaises(ValueError):
            observer.instrument_source(source, source, 'fighter/yulong', observer.SOURCE_PATH)

    def test_original_geometry_predicate_is_unchanged(self):
        source = (ROOT / 'tools/probes/as2/ai_reference/sampling_geometry.as').read_text()
        added = '\n      if(path == "' + observer.TARGET + '") _root.aiK1Observe("source_list_check",mc,target);'
        self.assertEqual(observer.instrument_geometry(source).replace(added, ''), source)
        with self.assertRaises(ValueError):
            observer.instrument_geometry(source.replace('mc._parent.pn', 'mc._parent._parent.pn'))

    def test_other_source_untouched(self):
        self.assertEqual(observer.instrument_source('x', 'y', 'fighter/yihu', observer.SOURCE_PATH), 'y')

    def test_only_unchanged_case(self):
        path = ROOT / 'evidence/sampling-upgrade/s239/yulong__attack__neutral__ground__near.json'
        observer.validate_case(path)
        case = json.loads(path.read_text()); case['inputs'][0]['start'] = 11
        with tempfile.TemporaryDirectory() as temp:
            changed = Path(temp) / 'case.json'; changed.write_text(json.dumps(case))
            with self.assertRaises(ValueError):
                observer.validate_case(changed)
        with self.assertRaises(ValueError):
            observer.validate_case(None)


class YulongK1EvidenceTests(unittest.TestCase):
    def setUp(self):
        import gzip
        self.lines = gzip.open(ROOT / 'evidence/sampling-upgrade/s247/native-capture.log.gz', 'rt').read().splitlines()

    def test_recorded_failure_is_target_only(self):
        from tools.sampling_k1atm_provenance import collect_provenance
        report = collect_provenance(self.lines)
        self.assertTrue(report['observation_complete'])
        self.assertFalse(report['source_list_checks_complete'])
        self.assertEqual(report['source_list_failures'], [
            {'tick': tick, 'failed_predicates': ['target == undefined']} for tick in (16, 17, 18)])

    def test_missing_observation_rejects(self):
        from tools.sampling_k1atm_provenance import collect_provenance
        for phase in ('root_sample', 'source_after_stamp', 'source_list_check'):
            row = next(l for l in self.lines if '|k1atm_provenance|' + phase + ',' in l)
            with self.subTest(phase=phase), self.assertRaises(ValueError):
                collect_provenance([l for l in self.lines if l != row])

    def test_changed_source_rejects(self):
        from tools.sampling_k1atm_provenance import collect_provenance
        with self.assertRaises(ValueError):
            collect_provenance([l.replace('yulong', 'yihu') if '|k1atm_provenance|' in l else l for l in self.lines])

    def test_changed_list_length_rejects(self):
        from tools.sampling_k1atm_provenance import collect_provenance
        with self.assertRaises(ValueError):
            collect_provenance([l.replace(',true,96,', ',true,95,') if '|k1atm_provenance|' in l else l for l in self.lines])


if __name__ == '__main__':
    unittest.main()
