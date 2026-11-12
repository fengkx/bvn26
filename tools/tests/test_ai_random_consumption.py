"""Random replay integrity tests; synthetic streams are never native proof."""
import copy
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest

from tools.probes.validate_ai_continuous_replay import (
    random_consumption_matches, source_random_window,
)

ROOT = Path(__file__).resolve().parents[2]


def stream():
    return [
        {"sequence": 1, "kind": "random", "value": "1,music,0.5"},
        {"sequence": 2, "kind": "intro_poll_state", "value": "0,true,0,0,1,1"},
        {"sequence": 3, "kind": "random", "value": "2,ai,0.75"},
        {"sequence": 4, "kind": "ready", "value": ""},
        {"sequence": 5, "kind": "random", "value": "3,ai,0.25"},
    ]


class RandomConsumptionTests(unittest.TestCase):
    def test_pre_intro_draws_are_counted_not_replayed(self):
        result = source_random_window(stream(), 4)
        self.assertEqual(result['local_cursor_offset'], 1)
        self.assertEqual(result['expected_local_cursor_at_ready'], 1)
        self.assertEqual([r['index'] for r in result['records']], [2, 3])
        self.assertTrue(random_consumption_matches(result['records'], {
            'random_original_indices': [2, 3],
            'random_consumed': [{'site': 'ai', 'value': 0.75}, {'site': 'ai', 'value': 0.25}],
        }))

    def test_missing_or_late_loaded_poll_refused(self):
        for replacement in ['0,false,0,0,1,1', 'missing']:
            events = stream()
            events[1]['value'] = replacement
            with self.assertRaisesRegex(ValueError, 'loaded intro poll'):
                source_random_window(events, 4)
        with self.assertRaisesRegex(ValueError, 'loaded intro poll'):
            source_random_window(stream(), 1)

    def test_missing_duplicate_and_reordered_events_refused(self):
        original = stream()
        for events in [original[:2] + original[3:], original + [original[-1]],
                       [original[1], original[0]] + original[2:]]:
            with self.assertRaisesRegex(ValueError, 'event sequence'):
                source_random_window(events, 4)

    def test_gap_reset_and_noncanonical_draw_index_refused(self):
        for index in ['4', '2', '03', 'true']:
            events = stream()
            events[-1]['value'] = index + ',ai,0.25'
            with self.assertRaises(ValueError):
                source_random_window(events, 4)

    def test_invalid_math_random_values_refused(self):
        for value in ['NaN', 'Infinity', '-0.1', '1', '1.5', 'f:0:0:67108864:0',
                      'f:1:0:1:0', 'f:1:1024:67108864:0']:
            events = stream()
            events[-1]['value'] = '3,ai,' + value
            with self.assertRaises(ValueError, msg=value):
                source_random_window(events, 4)

    def test_exact_vector_not_prefix_or_coerced_values(self):
        expected = source_random_window(stream(), 4)['records']
        valid = {'random_original_indices': [2, 3],
                 'random_consumed': [{'site': 'ai', 'value': .75}, {'site': 'ai', 'value': .25}]}
        variants = []
        for indices in [[2], [2, 3, 4], ['2', 3], [True, 3], [3, 2]]:
            variants.append(dict(valid, random_original_indices=indices))
        for records in [valid['random_consumed'][:1], valid['random_consumed'] * 2, None]:
            variants.append(dict(valid, random_consumed=records))
        for field, value in [('site', 'other'), ('value', '0.75'), ('value', True),
                             ('value', float('nan')), ('value', .7500000000000001)]:
            changed = copy.deepcopy(valid)
            changed['random_consumed'][0][field] = value
            variants.append(changed)
        for report in variants:
            self.assertFalse(random_consumption_matches(expected, report), report)

    def test_zero_draw_window_has_explicit_cursor(self):
        events = [dict(sequence=1, kind='intro_poll_state', value='0,true,0,0,1,1'),
                  dict(sequence=2, kind='ready', value='')]
        result = source_random_window(events, 2)
        self.assertEqual(result['expected_local_cursor_at_ready'], 0)
        self.assertTrue(random_consumption_matches([], {'random_original_indices': [], 'random_consumed': []}))

    def test_site_text_with_comma_is_not_split_or_normalized(self):
        events = stream()
        events[-1]['value'] = '3,source,with-comma,0.25'
        self.assertEqual(source_random_window(events, 4)['records'][-1]['site'], 'source,with-comma')

    def test_cli_retains_structured_rejection(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            (folder / 'source.jsonl').write_text('')
            (folder / 'replay.json').write_text('{}')
            (folder / 'build.json').write_text('{}')
            output = folder / 'result.json'
            result = subprocess.run([sys.executable, str(ROOT / 'tools/probes/validate_ai_continuous_replay.py'),
                                     str(folder / 'source.jsonl'), str(folder / 'replay.json'),
                                     '--source-build', str(folder / 'build.json'), '--output', str(output)],
                                    text=True, capture_output=True,
                                    env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
            self.assertEqual(result.returncode, 1)
            self.assertEqual(json.loads(output.read_text())['first_reason'], 'invalid_capture_or_replay_evidence')
            self.assertNotIn('Traceback', result.stderr)

    def test_retained_capture_matches_its_recorded_tape(self):
        # Historical selected-bundle capture, not a new run or whole-game RNG proof.
        folder = ROOT / 'evidence/ai/input-alias-r12'
        events = [json.loads(line) for line in (folder / 'events.jsonl').read_text().splitlines()]
        ready = next(e['sequence'] for e in events if e['kind'] == 'ready')
        result = source_random_window(events, ready)
        tape = json.loads((folder / 'random-tape.json').read_text())
        selected = [r for r in tape if r['sequence'] > result['replay_start_sequence']]
        self.assertEqual(result['records'], [{k: r[k] for k in ['index', 'site', 'value', 'sequence']} for r in selected])
        changed = copy.deepcopy(events)
        draw = next(e for e in changed if e['kind'] == 'random' and e['value'].startswith('2,'))
        draw['value'] = draw['value'].replace('2,', '3,', 1)
        with self.assertRaisesRegex(ValueError, 'random indices'):
            source_random_window(changed, ready)


if __name__ == '__main__':
    unittest.main()
