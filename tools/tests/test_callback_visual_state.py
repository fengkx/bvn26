"""The s262 extension rejects incomplete joins without admitting visual parity."""
import copy
import gzip
import importlib.util
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'evidence/sampling-upgrade/s262'


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


diagnosis = module('s262_diagnosis', 'diagnose.py')
builder = module('s262_builder', 'build_probe.py')
scene = module('s262_scene', 'build_scene.py')


class CallbackVisualStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.events = diagnosis.s258.s253.events_from(gzip.decompress((HERE / 'native-capture.log.gz').read_bytes()).decode().splitlines())
        cls.tape = diagnosis.s258.replay(cls.events)

    def test_retained_contract(self):
        actual = diagnosis.diagnose()
        self.assertEqual(actual, json.loads((HERE / 'diagnosis.json').read_text()))
        self.assertEqual(actual['actor_rows_equal_s258'], 122)
        self.assertEqual(len(actual['snapshots']), 61)
        for flag in ('production_admitted', 'native_parity_proven', 'lifetime_proved', 'common_visual_phase_proved'):
            self.assertFalse(actual[flag])

    def mutate_node(self, field, value):
        events = copy.deepcopy(self.events)
        event = next(e for e in events if e['kind'] == 's262_visual' and e['value'].startswith('timer/个,'))
        parts = event['value'].split(',')
        parts[diagnosis.FIELDS.index(field)] = value
        event['value'] = ','.join(parts)
        return events

    def test_wrong_digit_frame_rejects(self):
        with self.assertRaisesRegex(ValueError, 'frame join'):
            diagnosis.visual_snapshots(self.mutate_node('frame', '9'), self.tape)

    def test_wrong_init_serial_rejects(self):
        with self.assertRaisesRegex(ValueError, 'initialization'):
            diagnosis.visual_snapshots(self.mutate_node('init_serial', '999'), self.tape)

    def test_missing_camera_rejects(self):
        events = [e for e in self.events if not (e['kind'] == 's262_visual' and e['value'].startswith('camera,'))]
        with self.assertRaisesRegex(ValueError, 'missing visual role'):
            diagnosis.visual_snapshots(events, self.tape)

    def test_missing_initialization_rejects(self):
        events = [e for e in self.events if e['kind'] != 's262_init']
        with self.assertRaisesRegex(ValueError, 'initialization'):
            diagnosis.visual_snapshots(events, self.tape)

    def test_wrong_boundary_ordinal_rejects(self):
        events = copy.deepcopy(self.events)
        next(e for e in events if e['kind'] == 's262_end')['value'] = '999'
        with self.assertRaisesRegex(ValueError, 'visual end'):
            diagnosis.visual_snapshots(events, self.tape)

    def test_missing_snapshot_rejects(self):
        events = [e for e in self.events if not (e['tick'] == 60 and e['kind'] in ('s262_begin', 's262_visual', 's262_end'))]
        with self.assertRaisesRegex(ValueError, 'missing visual snapshot'):
            diagnosis.visual_snapshots(events, self.tape)

    def test_frame1_reentry_cannot_be_counted_as_birth(self):
        init = [e for e in self.events if e['kind'] == 's262_init']
        repeated = [e for e in init if e['value'].split(',')[0].endswith('.个')]
        self.assertGreater(len(repeated), 1)
        for event in repeated[1:]:
            index = event['sequence'] - 1
            # Native evidence places frame1 execution after the full bitmap,
            # not inside the callback that selected digit frame1.
            self.assertEqual(self.events[index - 1]['kind'], 'bitmap_end')
            previous = next(e for e in reversed(self.events[:index]) if e['kind'] == 's258_countdown')
            self.assertTrue(previous['value'].startswith('snapshot_after,'))
            self.assertEqual(diagnosis.s258.observed(previous)['ones'], 1)
        self.assertFalse(json.loads((HERE / 'diagnosis.json').read_text())['lifetime_proved'])

    def test_original_timer_and_draw_preserved(self):
        source = json.loads((ROOT / 'godot/generated/main/timeout/timer.json').read_text())['source_text'].replace('\r\n', '\n')
        self.assertEqual(builder.patch_init(source, 1813).split('\n', 1)[1], source)
        root = '   _root.s258Observe("snapshot_before", _root.s258Timer);\n   image.draw(_root);\n   _root.s258Observe("snapshot_after", _root.s258Timer);'
        patched = builder.patch_root(root)
        self.assertIn(root, patched)
        self.assertEqual(patched.count('image.draw(_root)'), 1)

    def test_authored_hud_moves_do_not_recreate_timer(self):
        contract = json.loads((HERE / 'source-contract.json').read_text())
        wrapper = contract['symbols']['1815']
        changes = [(c['frame'], ET.fromstring(c['tag'])) for c in wrapper['changes']]
        for frame, tag in changes:
            if tag.get('type') == 'PlaceObject2Tag' and frame > 1:
                self.assertEqual(tag.get('placeFlagMove'), 'true')
                self.assertEqual(tag.get('placeFlagHasCharacter'), 'false')
        timer = contract['symbols']['1813']
        self.assertEqual([c['frame'] for c in timer['changes'] if 'RemoveObject' in c['tag']], [10, 10])
        self.assertTrue(all(s['nodes']['timer']['frame'] == '1' for s in json.loads((HERE / 'diagnosis.json').read_text())['snapshots']))

    def test_scene_runner_stays_analysis_only(self):
        source = (ROOT / 'godot/tests/move_case_reference.gd').read_text()
        output = scene.build(source)
        self.assertIn('game.ko_recorded_timers = true', output)
        self.assertNotIn('if args[0] == "--bitmap-sequence":', output)
        self.assertNotIn('game.health_hud.reset()', output)
        with self.assertRaisesRegex(ValueError, 'boundary changed'):
            scene.build(source.replace('_capture_geometry(tick)', '_capture_geometry_changed(tick)'))


if __name__ == '__main__':
    unittest.main()
