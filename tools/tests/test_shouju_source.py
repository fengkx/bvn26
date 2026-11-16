"""Source-bound checks, not original-player parity acceptance."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/importer'))
from compile_ai_context import compile_context
from frame_call_guard import validate_cached_frame_calls


class TemariSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = ROOT / 'godot/generated/fighters/shouju'
        cls.bundle = json.loads((ROOT / 'scripts/fighter/shouju.json').read_text())
        cls.timeline = json.loads((cls.directory / 'timeline.json').read_text())
        cls.context = json.loads((cls.directory / 'ai.json').read_text())

    def test_context_matches_strict_source_compilation(self):
        self.assertEqual(self.context, compile_context(self.bundle, self.timeline))
        validate_cached_frame_calls(self.timeline, self.context, directory=self.directory)

    def test_every_authored_frame_call_is_guarded(self):
        for frame, calls in self.context['frame_calls'].items():
            for index in range(len(calls)):
                with self.subTest(frame=frame, call=index):
                    changed = copy.deepcopy(self.context)
                    changed['frame_calls'][frame].pop(index)
                    with self.assertRaisesRegex(ValueError, 'dropped/changed cached frame calls'):
                        validate_cached_frame_calls(self.timeline, changed, directory=self.directory)

    def test_source_super_and_recovery_boundaries(self):
        scripts = {row['path']: row['source'] for row in self.bundle['scripts']}
        for frame, name in ((601, 'bsd'), (689, 'bsd'), (792, 'cbsd')):
            source = scripts[f'DefineSprite_541/frame_{frame}/DoAction.as']
            self.assertIn(f'_root.{name}(pn);', source)
            self.assertIn('_root.showFace(pn,"手鞠1");', source)
        for frame in (652, 741, 934):
            calls = self.context['frame_calls'][str(frame)]
            self.assertEqual(calls[0]['op'], 'timeline_goto')
            self.assertEqual(calls[0]['label'], '站立')
            self.assertEqual(calls[1]['op'], 'timeline_play')


if __name__ == '__main__':
    unittest.main()
