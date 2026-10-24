"""Native byte observations, not approximations of the old float shader."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/probes'))
sys.path.insert(0, str(ROOT/'tools/importer'))
from decode_placement_math_capture import blend_bytes, decode
from visual_blend_modes import validate_blend_mode


class IntegerBlendArithmeticTests(unittest.TestCase):
    def test_native_alpha_ramp_matches_every_premultiplied_channel(self):
        rows = json.loads((ROOT/'tools/probes/flash_filters/blend-alpha-ramp-native.json').read_text())
        self.assertEqual(len(rows), 3072)
        self.assertTrue(any(r['front_alpha'] != r['requested_front_alpha'] for r in rows))
        for row in rows:
            self.assertEqual(blend_bytes(row['back_premultiplied'], row['front_premultiplied'], row['mode']),
                             row['premultiplied'], row)

    def test_admission_does_not_include_unimplemented_modes(self):
        for mode in (7, 13):
            self.assertEqual(validate_blend_mode(mode), mode)
        for mode in (10, 11, 12, 99):
            with self.assertRaisesRegex(ValueError, 'fixture.swf/frame_3'):
                validate_blend_mode(mode, 'fixture.swf/frame_3')

    def test_incomplete_native_ramp_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Incomplete ramp'):
            decode([], 'ramp')

    def test_shadow_binary_phase_impulses_measure_weight_residual(self):
        rows = json.loads((ROOT/'tools/probes/flash_filters/shadow-impulse-native.json').read_text())
        self.assertEqual(len(rows), 136)
        for row in rows:
            step = row['step']
            x, y = step % 16, step % 16 if row['diagonal'] else 0
            weights = [(16-x)*(16-y), x*(16-y), (16-x)*y]
            weights.append(256-sum(weights))
            actual = [[0, 0, 0, 0] for _ in range(16)]
            base_x, base_y = 1 + step//16, 1 + (step//16 if row['diagonal'] else 0)
            for (dx, dy), weight in zip(((0,0),(1,0),(0,1),(1,1)), weights):
                actual[(base_y+dy)*4+base_x+dx][3] = row['source_alpha']*weight//256
            self.assertEqual(actual, row['pixels'], row)

    def test_even_alpha_uses_low_overlay_branch_at_exact_half(self):
        rows = json.loads((ROOT/'tools/probes/flash_filters/blend-alpha-boundaries-native.json').read_text())
        self.assertEqual(len(rows), 336)
        for row in rows:
            self.assertEqual(blend_bytes(row['back_premultiplied'], row['front_premultiplied'], row['mode']),
                             row['premultiplied'], row)
