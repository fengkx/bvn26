"""A recorded callback is a bounded input, not a wall-clock or visual-phase proof."""
import copy
import gzip
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'evidence/sampling-upgrade/s258'


def module(name, file):
    spec = importlib.util.spec_from_file_location(name, HERE / file)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


diagnosis = module('s258_diagnosis', 'diagnose.py')
builder = module('s258_builder', 'build_probe.py')


class CountdownTapeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.events = diagnosis.s253.events_from(gzip.decompress((HERE / 'native-capture.log.gz').read_bytes()).decode().splitlines())

    def changed(self, phase, field, value):
        events = copy.deepcopy(self.events)
        event = next(e for e in events if e['kind'] == 's258_countdown' and e['value'].startswith(phase + ','))
        values = event['value'].split(',')
        values[diagnosis.FIELDS.index(field)] = value
        event['value'] = ','.join(values)
        return events

    def test_retained_tape_recomputes_without_admission(self):
        actual = diagnosis.diagnose()
        self.assertEqual(actual, json.loads((HERE / 'diagnosis.json').read_text()))
        self.assertFalse(actual['common_visual_phase_proved'])
        self.assertFalse(actual['production_admitted'])
        self.assertFalse(actual['native_parity_proven'])
        self.assertEqual(actual['actor_differences_from_s220'], [])
        self.assertEqual(actual['tape']['firing_count'], 70)
        self.assertEqual(actual['tape']['blocked_firings'], 15)

    def test_first_paused_callback_updates_digits_without_decrement(self):
        first = diagnosis.replay(self.events)['firings'][0]
        self.assertEqual(first['before']['gametime'], first['after']['gametime'])
        self.assertEqual(first['before']['tens'], 1)
        self.assertEqual(first['after']['tens'], 7)

    def test_wall_clock_does_not_supply_firings(self):
        events = copy.deepcopy(self.events)
        for e in events:
            e['time_ms'] = e['sequence'] * 100000
        tape = diagnosis.replay(events)
        self.assertEqual(tape['firing_count'], 70)
        self.assertEqual(tape['snapshots'][13]['replayed']['gametime'], 50)

    def test_missing_registration_rejects(self):
        with self.assertRaisesRegex(ValueError, 'registration'):
            diagnosis.replay([e for e in self.events if not e['value'].startswith('register_before,')])

    def test_missing_callback_rejects(self):
        events = [e for e in self.events if not (e['kind'] == 's258_countdown' and e['value'].split(',')[:2] in (['fire_before', '2'], ['fire_after', '2']))]
        with self.assertRaisesRegex(ValueError, 'firing'):
            diagnosis.replay(events)

    def test_missing_callback_exit_rejects(self):
        with self.assertRaisesRegex(ValueError, 'firing'):
            diagnosis.replay([e for e in self.events if not e['value'].startswith('fire_after,1,')])

    def test_guard_mutation_rejects(self):
        with self.assertRaisesRegex(ValueError, 'replay mismatch'):
            diagnosis.replay(self.changed('fire_before', 'paused', 'false'))

    def test_unknown_guard_rejects(self):
        with self.assertRaisesRegex(ValueError, 'guard type'):
            diagnosis.replay(self.changed('fire_before', 'p1_sw', 'undefined'))

    def test_wrong_digit_rejects(self):
        with self.assertRaisesRegex(ValueError, 'replay mismatch'):
            diagnosis.replay(self.changed('fire_after', 'tens', '8'))

    def test_wrong_snapshot_tick_rejects(self):
        events = copy.deepcopy(self.events)
        event = next(e for e in events if e['value'].startswith('snapshot_after,'))
        event['tick'] += 1
        with self.assertRaisesRegex(ValueError, 'snapshot'):
            diagnosis.replay(events)

    def test_changed_timer_rejects(self):
        with self.assertRaisesRegex(ValueError, 'identity'):
            diagnosis.replay(self.changed('fire_before', 'interval_id', '999'))

    def test_instrumentation_preserves_every_authored_timer_statement(self):
        source = json.loads((ROOT / 'godot/generated/main/timeout/timer.json').read_text())['source_text'].replace('\r\n', '\n')
        patched = builder.patch_timer(source)
        stripped = '\n'.join(line for line in patched.split('\n') if '_root.s258' not in line)
        self.assertEqual(stripped, source)
        self.assertEqual(patched.count('setInterval(time,1000)'), 1)
        with self.assertRaisesRegex(ValueError, 'unique boundary'):
            builder.patch_timer(source.replace('setInterval(time,1000)', 'setInterval(time,999)'))


if __name__ == '__main__':
    unittest.main()
