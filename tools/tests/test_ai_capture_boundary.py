"""Retain same-frame post-quit events without accepting a continued capture."""
import contextlib
import importlib.util
import io
import json
import math
import struct
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('collector', Path(__file__).parents[1] / 'probes/collect_ai_reference.py')
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)


class CaptureBoundaryTests(unittest.TestCase):
    def test_binary_numbers_preserve_native_probe_bits(self):
        path = Path(__file__).parents[2] / 'evidence/probes/schedule/number-encoding/comparison.json'
        for record in json.loads(path.read_text())['records']:
            with self.subTest(label=record['label']):
                self.assertEqual(struct.pack('>d', collector.decode_number(record['encoded'])),
                                 struct.pack('>d', record['expected']))
        self.assertEqual(math.copysign(1, collector.decode_number('f:-1:0:0:0')), -1)
        self.assertEqual(collector.decode_number('f:1:-1074:67108864:0'), math.ulp(0.0))
        self.assertEqual(collector.decode_number('f:1:1023:134217727:67108863'), sys.float_info.max)
        self.assertNotEqual(collector.decode_number('5.33333333333333'), 80 / 15)

    def test_binary_numbers_reject_malformed_records(self):
        for value in ['f:0:0:67108864:0', 'f:1:1024:67108864:0',
                      'f:1:0:1:0', 'f:1:0:0:1', 'f:1:1:0:0',
                      'f:1:0:67108864:67108864', 'f:1:0:67108864', 'f:1:x:67108864:0']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                collector.decode_number(value)

    def test_source_key_reads_follow_event_order(self):
        events = [
            {'kind': 'input_bindings', 'value': 'right=68,attack=74'},
            {'kind': 'key_read', 'value': 'p1.mc,68,false'},
            {'kind': 'input_next_display', 'value': 'right=true,attack=undefined'},
            {'kind': 'key_read', 'value': 'p1.mc,68,true'},
            {'kind': 'key_read', 'value': 'p1.mc,74,false'},
            {'kind': 'input_next_display', 'value': 'right=undefined,attack=undefined'},
            {'kind': 'key_read', 'value': 'p1.mc,68,false'},
        ]
        build = {'input_injection': 'body_kis_alias_with_per_read_trace'}
        report = collector.verify_key_reads(events, build)
        self.assertEqual(report['reads'], 4)
        self.assertEqual(report['pressed_reads'], {'p1.mc:68': 1})
        events[-1]['value'] = 'p1.mc,68,true'
        with self.assertRaisesRegex(ValueError, 'does not match'):
            collector.verify_key_reads(events, build)

    def test_legacy_input_is_not_certified(self):
        self.assertEqual(collector.verify_key_reads([], {})['status'],
                         'unverified_legacy_global_Key_isDown_override')

    def capture(self, trailing_tick=2, duplicate_done=False, retain_tail=False, trailing_fight=1):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            build = root / 'build'
            build.mkdir()
            (build / 'build.json').write_text(json.dumps({'run_id': 'test', 'frames_after_ready': 1}))
            (build / 'instrumentation.diff').write_text('fixture')
            lines = [
                'AIREF|test|1|1|1|-1|sample|fixture',
                'AIREF|test|2|2|1|0|ready|',
                'AIREF|test|3|3|2|1|done|',
                f'AIREF|test|4|4|{trailing_tick}|{trailing_fight}|{"done" if duplicate_done else "intro_body_exit"}|1,1',
            ]
            capture = root / 'capture.log'
            capture.write_text('\n'.join(lines) + '\n')
            output = root / 'output'
            args = ['collect', '--build', str(build), '--capture', str(capture), '--output', str(output)]
            if retain_tail:
                args.append('--retain-post-done-frames')
            with patch.object(sys, 'argv', args), contextlib.redirect_stdout(io.StringIO()):
                collector.main()
            records = [json.loads(line) for line in (output / 'events.jsonl').read_text().splitlines()]
            trailing = [json.loads(line) for line in (output / 'post-done-events.jsonl').read_text().splitlines()]
            self.assertEqual([r['sequence'] for r in records], [1, 2, 3])
            self.assertEqual(trailing[0]['sequence'], 4)
            self.assertEqual(trailing[0]['kind'], 'done' if duplicate_done else 'intro_body_exit')
            self.assertEqual(json.loads((output / 'summary.json').read_text())['post_done_events'], 1)

    def test_retains_same_frame_tail(self):
        self.capture()

    def test_rejects_a_later_display_tick(self):
        with self.assertRaisesRegex(ValueError, 'Display continued'):
            self.capture(trailing_tick=3)

    def test_rejects_duplicate_completion(self):
        with self.assertRaisesRegex(ValueError, 'did not complete'):
            self.capture(duplicate_done=True)

    def test_explicit_async_tail_preserves_later_completion(self):
        self.capture(trailing_tick=3, trailing_fight=2, duplicate_done=True, retain_tail=True)

    def test_async_tail_still_rejects_tick_disagreement(self):
        with self.assertRaisesRegex(ValueError, 'inconsistent'):
            self.capture(trailing_tick=3, retain_tail=True)

    def test_async_tail_still_rejects_same_frame_duplicate(self):
        with self.assertRaisesRegex(ValueError, 'Duplicate completion'):
            self.capture(duplicate_done=True, retain_tail=True)
