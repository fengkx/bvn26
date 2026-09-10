import gzip
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class TimeoutBadgeEvidenceTests(unittest.TestCase):
    def test_original_counter_changes_without_resolving_badge_aliases(self):
        log = gzip.decompress((ROOT / 'evidence/config/rendering/native.log.gz').read_bytes()).decode()
        events = [line.split('|', 7) for line in log.splitlines()]
        aliases = [e[7].split(',')[1:] for e in events if e[6] == 'timeout_badge_aliases']
        markers = [e[7].rsplit(',', 1) for e in events if e[6] == 'timeout_badge_frame']
        self.assertEqual(len(aliases), 231)
        self.assertTrue(all(row == ['undefined'] * 4 for row in aliases))
        self.assertEqual(len(markers), 462)
        self.assertTrue(all(frame == '1' for _, frame in markers))
        self.assertTrue(any(e[6] == 'timeout_state' and e[7].split(',')[3] == '2' for e in events))
        self.assertEqual(events[-1][6], 'done')

    def test_source_normal_ko_and_timeout_use_different_targets(self):
        sources = {s['path']: s['source'] for s in json.loads((ROOT / 'scripts/main.json').read_text())['scripts']}
        self.assertIn('_root.updateWins()', sources['DefineSprite_1858/frame_94/DoAction.as'])
        timeout = sources['DefineSprite_1848/frame_67/DoAction.as']
        for slot in ['p1', 'p2']:
            self.assertIn(f'_root.{slot}win.bzxg.play()', timeout)
            self.assertIn(f'{slot}xt.win.gotoAndStop', sources['DefineSprite_1814/frame_1/DoAction.as'])
        presentation = json.loads((ROOT / 'godot/generated/main/health/presentation.json').read_text())
        self.assertEqual(presentation['win_source_sprite'], 1785)
        self.assertEqual([len(presentation['win_frames'][str(frame)]) for frame in [1, 2, 3]], [0, 1, 2])
        self.assertEqual(sources['DefineSprite_1785/frame_1/DoAction.as'].strip(), 'stop();')


if __name__ == '__main__':
    unittest.main()
