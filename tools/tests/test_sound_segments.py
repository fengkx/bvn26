"""Source sample positions and left/right envelopes must survive conversion."""
from array import array
import json
from pathlib import Path
import sys
import unittest
import wave

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/importer'))
from build_sound_segments import segment


class SoundSegmentTests(unittest.TestCase):
    def test_sample_boundaries_and_independent_channel_levels(self):
        pcm = array('h', [100, 200, 300, 400, 500])
        result, start, end = segment(pcm, 1, {'in_point': 1, 'out_point': 4,
            'envelope': [{'pos44': 0, 'left_level': 32768, 'right_level': 16384}]})
        self.assertEqual((start, end), (1, 4))
        self.assertEqual(list(result), [200, 100, 300, 150, 400, 200])

    def test_dynamic_envelope_interpolates_each_channel(self):
        pcm = array('h', [100] * 5)
        result, start, end = segment(pcm, 1, {
            'envelope': [
                {'pos44': 0, 'left_level': 0, 'right_level': 32768},
                {'pos44': 4, 'left_level': 32768, 'right_level': 0},
            ],
            'in_point': 0,
            'out_point': 5,
        })
        self.assertEqual((start, end), (0, 5))
        self.assertEqual(list(result), [0, 100, 25, 75, 50, 50, 75, 25, 100, 0])

    def test_dynamic_envelope_holds_first_and_last_levels_outside_points(self):
        pcm = array('h', [100] * 5)
        result, _, _ = segment(pcm, 1, {
            'envelope': [
                {'pos44': 2, 'left_level': 16384, 'right_level': 8192},
                {'pos44': 4, 'left_level': 32768, 'right_level': 16384},
            ],
            'in_point': 0,
            'out_point': 5,
        })
        self.assertEqual(list(result), [50, 25, 50, 25, 50, 25, 75, 38, 100, 50])

    def test_duplicate_envelope_positions_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'positions must be unique'):
            segment(array('h', [100]), 1, {'envelope': [
                {'pos44': 0, 'left_level': 1, 'right_level': 1},
                {'pos44': 0, 'left_level': 2, 'right_level': 2},
            ]})

    def test_original_renji_frame_21_sound_38_dynamic_envelope(self):
        timeline = json.loads(
            (ROOT / 'godot/generated/fighters/renji/timeline.json').read_text())
        event = next(event for frame in timeline['frames'] if frame['frame'] == 21
                     for event in frame.get('events', [])
                     if event.get('type') == 'start_sound' and event['sound_id'] == 38)
        self.assertEqual(event['envelope'], [
            {'pos44': 0, 'left_level': 16532, 'right_level': 15646},
            {'pos44': 33366, 'left_level': 0, 'right_level': 0},
        ])
        result, start, end = segment(array('h', [1000]) * 33367, 1, event)
        self.assertEqual((start, end), (0, 33367))
        self.assertEqual(list(result[:2]), [505, 477])
        self.assertEqual(list(result[-2:]), [0, 0])

    def test_dynamic_envelope_and_nonzero_in_point_use_same_source_index(self):
        timeline = json.loads(
            (ROOT / 'godot/generated/fighters/renji/timeline.json').read_text())
        source_event = next(event for frame in timeline['frames'] if frame['frame'] == 21
                            for event in frame.get('events', [])
                            if event.get('type') == 'start_sound' and event['sound_id'] == 38)
        event = dict(source_event, in_point=10, out_point=33367)
        result, start, end = segment(array('h', [1000]) * 33367, 1, event)
        self.assertEqual((start, end), (10, 33367))
        self.assertEqual(len(result), (33367 - 10) * 2)
        self.assertEqual(list(result[:2]), [504, 477])

    def test_original_nonzero_in_point_is_applied_before_envelope(self):
        timeline = json.loads(
            (ROOT / 'godot/generated/fighters/rifagu/timeline.json').read_text())
        event = next(event for frame in timeline['frames'] if frame['frame'] == 253
                     for event in frame.get('events', [])
                     if event.get('type') == 'start_sound' and event['sound_id'] == 150)
        result, start, end = segment(array('h', [1000]) * 36864, 1, event)
        self.assertEqual((start, end), (4400, 36864))
        self.assertEqual(len(result), (36864 - 4400) * 2)
        self.assertEqual(list(result[:2]), [488, 498])

    def test_finite_loop_uses_the_authored_crop_for_each_play(self):
        pcm = array('h', range(8064))
        result, start, end = segment(pcm, 1, {
            'in_point': 1100, 'out_point': 5400, 'loop_count': 20, 'envelope': [],
        })
        self.assertEqual((start, end), (1100, 5400))
        self.assertEqual(len(result) // 2, 86000)
        self.assertEqual(result[0:4], array('h', [1100, 1100, 1101, 1101]))
        self.assertEqual(result[2 * 4300:2 * 4300 + 4],
                         array('h', [1100, 1100, 1101, 1101]))
        self.assertAlmostEqual((len(result) // 2) / 44100, 1.9501133787)

    def test_missing_loop_count_means_one_play_but_explicit_nonpositive_fails(self):
        result, _, _ = segment(array('h', [100] * 4), 1, {})
        self.assertEqual(len(result), 8)
        for loop_count in (0, -1):
            with self.subTest(loop_count=loop_count):
                with self.assertRaisesRegex(ValueError, 'must be positive'):
                    segment(array('h', [100] * 4), 1, {'loop_count': loop_count})

    def test_looped_sound_with_envelope_fails_closed(self):
        with self.assertRaisesRegex(ValueError, 'playback-wide envelope evidence'):
            segment(array('h', [100] * 8), 1, {
                'loop_count': 2,
                'envelope': [{'pos44': 0, 'left_level': 32768, 'right_level': 32768}],
            })

    def test_original_sakura_frame_727_loop_source_has_no_envelope(self):
        timeline = json.loads(
            (ROOT / 'godot/generated/fighters/sakura/timeline.json').read_text())
        event = next(event for frame in timeline['frames'] if frame['frame'] == 727
                     for event in frame.get('events', [])
                     if event.get('type') == 'start_sound' and event['sound_id'] == 49)
        self.assertEqual((event['in_point'], event['out_point'], event['loop_count']),
                         (1100, 5400, 20))
        self.assertNotIn('envelope', event)

    def test_original_rifagu_sound_150_has_exact_authored_length(self):
        directory = ROOT / 'godot/generated/fighters/rifagu'
        manifest = json.loads((directory / 'sound_segments.json').read_text())
        record = manifest['frames']['253'][0]
        self.assertEqual(record['source_event']['sound_id'], 150)
        self.assertEqual((record['start_sample'], record['end_sample']), (4400, 36864))
        with wave.open(str(directory / record['stream'])) as sound:
            self.assertEqual((sound.getframerate(), sound.getnframes(), sound.getnchannels()),
                             (44100, 32464, 2))


if __name__ == '__main__':
    unittest.main()
