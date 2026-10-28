import unittest
import json
from pathlib import Path
from tools.probes.callsite_observer import SWF, PATH, SOURCE, specification, instrument
from tools.probes.doaction_observer import inventory
from tools.sampling_callsite import collect_calls


class CallSiteTests(unittest.TestCase):
    def spec(self):
        return specification(inventory({'game_file': SWF, 'swf_sha256': 'locked',
            'scripts': [{'path': PATH, 'source': SOURCE}]}, include_clip=True))

    def test_chad_locked_handler_and_ambiguous_selection(self):
        root = Path(__file__).resolve().parents[2]
        bundle = json.loads((root / 'scripts/fighter/chad.json').read_text())
        records = inventory(bundle, include_clip=True)
        spec = specification(records)
        source = next(s['source'] for s in bundle['scripts'] if s['path'] == spec['source']['path'])
        self.assertEqual(spec['source']['sprite'], 607)
        result = instrument(source, spec['source'])
        self.assertEqual(result.count('if(gameRunning())'), 1)
        self.assertEqual(result.count('doAllAction();'), 1)
        with self.assertRaisesRegex(ValueError, 'changed/unsupported'):
            instrument(source.replace('doAllAction();', 'unknown(speed*18);'), spec['source'])
        with self.assertRaisesRegex(ValueError, 'unique'):
            specification(records + [self.spec()['source']])

    def test_renji_locked_handler_binding(self):
        root = Path(__file__).resolve().parents[2]
        bundle = json.loads((root / 'scripts/fighter/Renji.json').read_text())
        records = inventory(bundle, include_clip=True)
        spec = specification(records)
        source = next(s['source'] for s in bundle['scripts'] if s['path'] == spec['source']['path'])
        self.assertEqual(spec['source']['sprite'], 717)
        self.assertEqual(spec['source']['placement_path'], 'PlaceObject2_16_29')
        self.assertEqual(instrument(source, spec['source']).count('doAllAction();'), 1)
        with self.assertRaisesRegex(ValueError, 'changed/unsupported'):
            instrument(source.replace('doAllAction();', 'unknown(speed*18);'), spec['source'])
        with self.assertRaisesRegex(ValueError, 'unique'):
            specification(records + [self.spec()['source']])

    def test_lee_locked_handler_binding(self):
        root = Path(__file__).resolve().parents[2]
        bundle = json.loads((root / 'scripts/fighter/lee.json').read_text())
        records = inventory(bundle, include_clip=True)
        spec = specification(records)
        source = next(s['source'] for s in bundle['scripts'] if s['path'] == spec['source']['path'])
        self.assertEqual(spec['source']['sprite'], 518)
        self.assertEqual(spec['source']['placement_path'], 'PlaceObject2_18_31')
        self.assertEqual(instrument(source, spec['source']).count('doAllAction();'), 1)
        with self.assertRaisesRegex(ValueError, 'changed/unsupported'):
            instrument(source.replace('doAllAction();', 'unknown(speed*18);'), spec['source'])
        with self.assertRaisesRegex(ValueError, 'unique'):
            specification(records + [self.spec()['source']])

    def test_neji_locked_handler_binding(self):
        root = Path(__file__).resolve().parents[2]
        bundle = json.loads((root / 'scripts/fighter/neji.json').read_text())
        records = inventory(bundle, include_clip=True)
        spec = specification(records)
        source = next(s['source'] for s in bundle['scripts'] if s['path'] == spec['source']['path'])
        self.assertEqual(spec['source']['sprite'], 535)
        self.assertEqual(spec['source']['placement_path'], 'PlaceObject2_20_31')
        self.assertEqual(instrument(source, spec['source']).count('doAllAction();'), 1)
        with self.assertRaisesRegex(ValueError, 'changed/unsupported'):
            instrument(source.replace('doAllAction();', 'unknown(speed*18);'), spec['source'])
        with self.assertRaisesRegex(ValueError, 'unique'):
            specification(records + [self.spec()['source']])

    def test_sakura_locked_handler_binding(self):
        root = Path(__file__).resolve().parents[2]
        bundle = json.loads((root / 'scripts/fighter/Sakura.json').read_text())
        records = inventory(bundle, include_clip=True)
        spec = specification(records)
        source = next(s['source'] for s in bundle['scripts'] if s['path'] == spec['source']['path'])
        self.assertEqual(spec['source']['sprite'], 630)
        self.assertEqual(spec['source']['placement_path'], 'PlaceObject2_11_31')
        self.assertEqual(instrument(source, spec['source']).count('doAllAction();'), 1)
        with self.assertRaisesRegex(ValueError, 'changed/unsupported'):
            instrument(source.replace('doAllAction();', 'unknown(speed*18);'), spec['source'])
        with self.assertRaisesRegex(ValueError, 'unique'):
            specification(records + [self.spec()['source']])

    def test_yin_locked_handler_binding(self):
        root = Path(__file__).resolve().parents[2]
        bundle = json.loads((root / 'scripts/fighter/yin.json').read_text())
        records = inventory(bundle, include_clip=True)
        spec = specification(records)
        source = next(s['source'] for s in bundle['scripts'] if s['path'] == spec['source']['path'])
        self.assertEqual(spec['source']['sprite'], 435)
        self.assertEqual(spec['source']['placement_path'], 'PlaceObject2_16_31')
        self.assertEqual(instrument(source, spec['source']).count('doAllAction();'), 1)
        with self.assertRaisesRegex(ValueError, 'changed/unsupported'):
            instrument(source.replace('doAllAction();', 'unknown(speed*18);'), spec['source'])
        with self.assertRaisesRegex(ValueError, 'unique'):
            specification(records + [self.spec()['source']])

    def test_jianba_locked_handler_binding(self):
        root = Path(__file__).resolve().parents[2]
        bundle = json.loads((root / 'scripts/fighter/jianba.json').read_text())
        records = inventory(bundle, include_clip=True)
        spec = specification(records)
        source = next(s['source'] for s in bundle['scripts'] if s['path'] == spec['source']['path'])
        self.assertEqual(spec['source']['sprite'], 514)
        self.assertEqual(spec['source']['placement_path'], 'PlaceObject2_13_31')
        self.assertEqual(instrument(source, spec['source']).count('doAllAction();'), 1)
        with self.assertRaisesRegex(ValueError, 'changed/unsupported'):
            instrument(source.replace('doAllAction();', 'unknown(speed*18);'), spec['source'])
        with self.assertRaisesRegex(ValueError, 'unique'):
            specification(records + [self.spec()['source']])

    def test_juggo_locked_handler_binding(self):
        root = Path(__file__).resolve().parents[2]
        bundle = json.loads((root / 'scripts/fighter/juggo.json').read_text())
        records = inventory(bundle, include_clip=True)
        spec = specification(records)
        source = next(s['source'] for s in bundle['scripts'] if s['path'] == spec['source']['path'])
        self.assertEqual(spec['source']['sprite'], 517)
        self.assertEqual(spec['source']['placement_path'], 'PlaceObject2_16_31')
        self.assertEqual(instrument(source, spec['source']).count('doAllAction();'), 1)
        with self.assertRaisesRegex(ValueError, 'changed/unsupported'):
            instrument(source.replace('doAllAction();', 'unknown(speed*18);'), spec['source'])
        with self.assertRaisesRegex(ValueError, 'unique'):
            specification(records + [self.spec()['source']])

    def test_konan_locked_handler_binding(self):
        root = Path(__file__).resolve().parents[2]
        bundle = json.loads((root / 'scripts/fighter/konan.json').read_text())
        records = inventory(bundle, include_clip=True)
        spec = specification(records)
        source = next(s['source'] for s in bundle['scripts'] if s['path'] == spec['source']['path'])
        self.assertEqual(spec['source']['sprite'], 563)
        self.assertEqual(spec['source']['placement_path'], 'PlaceObject2_16_32')
        self.assertEqual(instrument(source, spec['source']).count('doAllAction();'), 1)
        with self.assertRaisesRegex(ValueError, 'changed/unsupported'):
            instrument(source.replace('doAllAction();', 'unknown(speed*18);'), spec['source'])
        with self.assertRaisesRegex(ValueError, 'unique'):
            specification(records + [self.spec()['source']])

    def test_byakuya_locked_handler_binding(self):
        root = Path(__file__).resolve().parents[2]
        bundle = json.loads((root / 'scripts/fighter/Byakuya.json').read_text())
        records = inventory(bundle, include_clip=True)
        spec = specification(records)
        source = next(s['source'] for s in bundle['scripts'] if s['path'] == spec['source']['path'])
        self.assertEqual(spec['source']['sprite'], 631)
        self.assertEqual(spec['source']['placement_path'], 'PlaceObject2_16_31')
        self.assertEqual(instrument(source, spec['source']).count('doAllAction();'), 1)
        with self.assertRaisesRegex(ValueError, 'changed/unsupported'):
            instrument(source.replace('doAllAction();', 'unknown(speed*18);'), spec['source'])
        with self.assertRaisesRegex(ValueError, 'unique'):
            specification(records + [self.spec()['source']])

    def test_daitu_locked_handler_binding(self):
        root = Path(__file__).resolve().parents[2]
        bundle = json.loads((root / 'scripts/fighter/daitu.json').read_text())
        records = inventory(bundle, include_clip=True)
        spec = specification(records)
        source = next(s['source'] for s in bundle['scripts'] if s['path'] == spec['source']['path'])
        self.assertEqual(spec['source']['sprite'], 458)
        self.assertEqual(spec['source']['placement_path'], 'PlaceObject2_21_31')
        self.assertEqual(instrument(source, spec['source']).count('doAllAction();'), 1)
        with self.assertRaisesRegex(ValueError, 'changed/unsupported'):
            instrument(source.replace('doAllAction();', 'unknown(speed*18);'), spec['source'])
        with self.assertRaisesRegex(ValueError, 'unique'):
            specification(records + [self.spec()['source']])

    def test_gaara_locked_handler_binding(self):
        root = Path(__file__).resolve().parents[2]
        bundle = json.loads((root / 'scripts/fighter/gaara.json').read_text())
        records = inventory(bundle, include_clip=True)
        spec = specification(records)
        source = next(s['source'] for s in bundle['scripts'] if s['path'] == spec['source']['path'])
        self.assertEqual(spec['source']['sprite'], 673)
        self.assertEqual(spec['source']['placement_path'], 'PlaceObject2_20_31')
        self.assertEqual(instrument(source, spec['source']).count('doAllAction();'), 1)
        with self.assertRaisesRegex(ValueError, 'changed/unsupported'):
            instrument(source.replace('doAllAction();', 'unknown(speed*18);'), spec['source'])
        with self.assertRaisesRegex(ValueError, 'unique'):
            specification(records + [self.spec()['source']])

    def test_itachi_locked_handler_binding(self):
        root = Path(__file__).resolve().parents[2]
        bundle = json.loads((root / 'scripts/fighter/itachi.json').read_text())
        records = inventory(bundle, include_clip=True)
        spec = specification(records)
        source = next(s['source'] for s in bundle['scripts'] if s['path'] == spec['source']['path'])
        self.assertEqual(spec['source']['sprite'], 294)
        self.assertEqual(spec['source']['placement_path'], 'PlaceObject2_11_33')
        self.assertEqual(instrument(source, spec['source']).count('doAllAction();'), 1)
        with self.assertRaisesRegex(ValueError, 'changed/unsupported'):
            instrument(source.replace('doAllAction();', 'unknown(speed*18);'), spec['source'])
        with self.assertRaisesRegex(ValueError, 'unique'):
            specification(records + [self.spec()['source']])

    def test_kakashi_locked_handler_binding(self):
        root = Path(__file__).resolve().parents[2]
        bundle = json.loads((root / 'scripts/fighter/Kakashi.json').read_text())
        records = inventory(bundle, include_clip=True)
        spec = specification(records)
        source = next(s['source'] for s in bundle['scripts'] if s['path'] == spec['source']['path'])
        self.assertEqual(spec['source']['sprite'], 710)
        self.assertEqual(spec['source']['placement_path'], 'PlaceObject2_9_31')
        self.assertEqual(instrument(source, spec['source']).count('doAllAction();'), 1)
        with self.assertRaisesRegex(ValueError, 'changed/unsupported'):
            instrument(source.replace('doAllAction();', 'unknown(speed*18);'), spec['source'])
        with self.assertRaisesRegex(ValueError, 'unique'):
            specification(records + [self.spec()['source']])

    def test_lanran_locked_handler_binding(self):
        root = Path(__file__).resolve().parents[2]
        bundle = json.loads((root / 'scripts/fighter/lanran.json').read_text())
        records = inventory(bundle, include_clip=True)
        spec = specification(records)
        source = next(s['source'] for s in bundle['scripts'] if s['path'] == spec['source']['path'])
        self.assertEqual(spec['source']['sprite'], 640)
        self.assertEqual(spec['source']['placement_path'], 'PlaceObject2_15_33')
        self.assertEqual(instrument(source, spec['source']).count('doAllAction();'), 1)
        with self.assertRaisesRegex(ValueError, 'changed/unsupported'):
            instrument(source.replace('doAllAction();', 'unknown(speed*18);'), spec['source'])
        with self.assertRaisesRegex(ValueError, 'unique'):
            specification(records + [self.spec()['source']])

    def test_minren_locked_handler_binding(self):
        root = Path(__file__).resolve().parents[2]
        bundle = json.loads((root / 'scripts/fighter/minren.json').read_text())
        records = inventory(bundle, include_clip=True)
        spec = specification(records)
        source = next(s['source'] for s in bundle['scripts'] if s['path'] == spec['source']['path'])
        self.assertEqual(spec['source']['sprite'], 764)
        self.assertEqual(spec['source']['placement_path'], 'PlaceObject2_16_31')
        self.assertEqual(instrument(source, spec['source']).count('doAllAction();'), 1)
        with self.assertRaisesRegex(ValueError, 'changed/unsupported'):
            instrument(source.replace('doAllAction();', 'unknown(speed*18);'), spec['source'])
        with self.assertRaisesRegex(ValueError, 'unique'):
            specification(records + [self.spec()['source']])

    def test_orochimaru_locked_handler_binding(self):
        root = Path(__file__).resolve().parents[2]
        bundle = json.loads((root / 'scripts/fighter/orochimaru.json').read_text())
        records = inventory(bundle, include_clip=True)
        spec = specification(records)
        source = next(s['source'] for s in bundle['scripts'] if s['path'] == spec['source']['path'])
        self.assertEqual(spec['source']['sprite'], 541)
        self.assertEqual(spec['source']['placement_path'], 'PlaceObject2_16_31')
        self.assertEqual(instrument(source, spec['source']).count('doAllAction();'), 1)
        with self.assertRaisesRegex(ValueError, 'changed/unsupported'):
            instrument(source.replace('doAllAction();', 'unknown(speed*18);'), spec['source'])
        with self.assertRaisesRegex(ValueError, 'unique'):
            specification(records + [self.spec()['source']])

    def test_jiraiya_locked_handler_binding(self):
        root = Path(__file__).resolve().parents[2]
        bundle = json.loads((root / 'scripts/fighter/jiraiya.json').read_text())
        records = inventory(bundle, include_clip=True)
        spec = specification(records)
        source = next(s['source'] for s in bundle['scripts'] if s['path'] == spec['source']['path'])
        self.assertEqual(spec['source']['sprite'], 342)
        self.assertEqual(spec['source']['placement_path'], 'PlaceObject2_11_33')
        self.assertEqual(instrument(source, spec['source']).count('doAllAction();'), 1)
        with self.assertRaisesRegex(ValueError, 'changed/unsupported'):
            instrument(source.replace('doAllAction();', 'unknown(speed*18);'), spec['source'])
        with self.assertRaisesRegex(ValueError, 'unique'):
            specification(records + [self.spec()['source']])

    def rows(self, taken=True):
        identity = self.spec()['handler_id']
        phases = ['predicate_before', 'true', 'call_before', 'call_after', 'end'] if taken else ['predicate_before', 'false', 'end']
        return [f'AIREF|test|1|0|1|0|clipaction_entry|{identity},_level0.game.p1.mc.AImain,1'] + [
            f'AIREF|test|{i+2}|0|1|0|callsite|{identity},{phase},_level0.game.p1.mc.AImain'
            for i,phase in enumerate(phases)]

    def test_both_branch_paths_and_call_pairs(self):
        spec = self.spec()
        for taken in (True, False):
            result = collect_calls(self.rows(taken), spec)
            self.assertEqual(result['paired_call_count'], int(taken))
            self.assertFalse(result['callee_body_ownership_proven'])

    def test_every_missing_marker_rejects(self):
        rows = self.rows()
        for index in range(len(rows)):
            with self.subTest(index=index), self.assertRaises(ValueError):
                collect_calls(rows[:index]+rows[index+1:], self.spec())

    def test_wrong_branch_duplicate_and_foreign_source_reject(self):
        rows = self.rows()
        for bad in [rows[:3]+[rows[2]]+rows[3:], [x.replace(',true,', ',false,') for x in rows],
                    [x.replace(self.spec()['handler_id'], 'foreign') for x in rows]]:
            with self.assertRaises(ValueError): collect_calls(bad, self.spec())

    def test_reentrant_or_missing_invocation_rejects(self):
        rows = self.rows()
        with self.assertRaises(ValueError): collect_calls(rows[:2]+rows, self.spec())
        with self.assertRaises(ValueError): collect_calls([], self.spec())
        with self.assertRaises(ValueError): specification([])

    def test_diagnostic_retains_incomplete_without_admission(self):
        rows = self.rows()
        result = collect_calls(rows[:4]+rows, self.spec(), retain_incomplete=True)
        self.assertFalse(result['invocation_observations_complete'])
        self.assertEqual(len(result['incomplete_invocations']), 1)
        self.assertEqual(result['paired_call_count'], 1)
        with self.assertRaises(ValueError):
            collect_calls(rows[:4]+rows, self.spec())

    def test_condition_evaluated_once_original_call_preserved(self):
        record = self.spec()['source']
        result = instrument(SOURCE, record)
        self.assertEqual(result.count('if(gameRunning())'), 1)
        self.assertEqual(result.count('doAllAction();'), 1)
        self.assertIn('else', result)
        for changed in [SOURCE.replace('doAllAction();', ''), SOURCE.replace('gameRunning()', 'unknown(speed*18)')]:
            with self.assertRaisesRegex(ValueError, 'changed/unsupported'):
                instrument(changed, record)


if __name__ == '__main__':
    unittest.main()
