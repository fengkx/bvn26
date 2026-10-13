"""Itachi's source placements and receiver callbacks must survive compilation."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


def read(path):
    return json.loads((ROOT / path).read_text())


class ItachiImportTests(unittest.TestCase):
    def test_target_relative_loads_and_later_hitbox_copies(self):
        model = read('data/actions/itachi-base.json')
        self.assertEqual(model, read('godot/generated/fighters/itachi/combat.json'))
        events = {event['frame']: event for event in model['clip_placements']}
        # The original load callback refuses targets behind the caster; the
        # normal super has no such restriction and copies only horizontal position.
        self.assertTrue(events[305]['front_only'])
        self.assertEqual(events[305]['y_pixels'], -36)
        self.assertTrue(events[405]['front_only'])
        self.assertFalse(events[678]['front_only'])
        self.assertFalse(events[678]['place_y'])
        self.assertEqual(events[313]['reference_instance'], 'zzzz')
        self.assertEqual(events[313]['x_facing_pixels'], 10)
        self.assertEqual(events[313]['y_pixels'], -4)
        self.assertEqual(events[415]['reference_instance'], 'zzzz')
        self.assertFalse(events[415]['place_y'])

    def test_fractional_projectile_motion_and_counter_lifetime(self):
        metadata = read('godot/generated/fighters/itachi/player_controller/controller.json')
        projectiles = {h['placement_frame']: h['projectile'] for h in metadata['projectile_hooks']}
        for frame in (157, 160, 163):
            self.assertEqual(projectiles[frame]['local_y_factor'], 0.5)
        for frame in (526, 529, 532):
            self.assertEqual(projectiles[frame]['local_y_factor'], -0.5)
        counter = next(h for h in metadata['receiver_hooks'] if h['placement_frame'] == 448)
        self.assertEqual(counter['receiver'], 'checkHit')
        self.assertEqual(counter['counter_label'], '招21')
        self.assertEqual(counter['member_frames'], list(range(448, 468)))

    def test_nested_hit_sound_retains_independent_channel_envelope(self):
        timeline = read('godot/generated/fighters/itachi/timeline.json')
        child = next(d for d in timeline['definitions'] if d['character_id'] == 61)
        event = next(e for e in child['display_list_frame_events'][9] if e.get('type') == 'start_sound')
        self.assertEqual(event['sound_id'], 42)
        self.assertEqual(event['envelope'], [
            {'pos44': 0, 'left_level': 20369, 'right_level': 20665}])
        segments = read('godot/generated/fighters/itachi/sound_segments.json')
        record = segments['nested_frames']['61:10'][0]
        self.assertEqual(record['source_event'], event)
        self.assertTrue((ROOT / 'godot/generated/fighters/itachi' / record['stream']).is_file())

    def test_clip_depth_mask_uses_source_contour(self):
        timeline = read('godot/generated/fighters/itachi/timeline.json')
        mask = next(d for d in timeline['definitions'] if d['character_id'] == 6)
        self.assertEqual(mask['mask_polygon'], [
            [72.45, 15.8], [72.45, 92.55], [36.7, 92.55], [36.7, 15.8]])
        frame = next(f for f in timeline['frames'] if f['frame'] == 313)
        placements = {p['depth']: p for p in frame['display_list']}
        self.assertEqual(placements[28]['character_id'], 6)
        self.assertEqual(placements[28]['clip_depth'], 30)
        self.assertEqual(placements[29]['character_id'], 44)

    def test_source_super_and_receive_frames(self):
        model = read('data/actions/itachi-base.json')
        self.assertFalse(model['extracted_partial'])
        self.assertEqual([(event['frame'], event['op']) for event in model['super_events']],
                         [(580, 'super_start'), (599, 'super_end'),
                          (655, 'super_start'), (675, 'super_end'),
                          (758, 'super_start'), (834, 'super_end')])
        self.assertEqual([(e['frame'], e['flying']) for e in model['on_be_hit_frames']],
                         [(1010, False), (1023, True)])
        warp = model['body_warps'][0]
        self.assertEqual(warp['frame'], 494)
        self.assertEqual(warp['xscale_gt_0']['x_bdmn_width'], -0.7)
        self.assertEqual(warp['xscale_lt_0']['x_bdmn_width'], 0.7)
        self.assertTrue(warp['place_y'])


if __name__ == '__main__':
    unittest.main()
