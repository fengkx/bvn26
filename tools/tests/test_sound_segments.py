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

    def test_unsupported_envelopes_are_not_silently_flattened(self):
        with self.assertRaisesRegex(ValueError, 'Dynamic envelopes'):
            segment(array('h', [100]), 1, {'envelope': [{'pos44': 1}]})

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
