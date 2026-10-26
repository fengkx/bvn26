"""Source-bound base BODY initialization cannot drop authored wrapper filters."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/importer'))
from compile_ai_context import compile_context
from frame_call_guard import validate_cached_frame_calls
from placement_build_guard import validate_build_placements


class WrapperFilterInitializationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = json.loads((ROOT / 'scripts/fighter/yulong.json').read_text())
        cls.directory = ROOT / 'godot/generated/fighters/yulong'
        cls.timeline = json.loads((cls.directory / 'timeline.json').read_text())
        cls.cached = json.loads((cls.directory / 'ai.json').read_text())

    def test_original_base_filter_and_initialization_are_retained(self):
        compiled = compile_context(self.bundle, self.timeline)
        self.assertEqual(compiled, self.cached)
        self.assertTrue(compiled['placement_filter_initialization']['clear_placement_filters'])
        self.assertEqual(self.timeline['wrapper']['filters'],
                         [{'type': 'BLURFILTER', 'blurX': 0.0, 'blurY': 0.0, 'passes': 1}])
        validate_build_placements(self.timeline, 'yulong')
        validate_cached_frame_calls(self.timeline, self.cached, directory=self.directory)

    def test_missing_or_changed_cached_reset_fails_at_source_frame(self):
        numeric = {**self.cached['placement_filter_initialization'], 'clear_placement_filters': 1}
        for value in (None, {}, {'clear_placement_filters': False}, numeric):
            cached = copy.deepcopy(self.cached)
            cached['placement_filter_initialization'] = value
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'yulong.swf:DefineSprite_345/frame_1.*placement-filter'):
                validate_cached_frame_calls(self.timeline, cached, directory=self.directory)

    def test_dropping_zero_radius_filter_is_still_an_error(self):
        timeline = copy.deepcopy(self.timeline)
        del timeline['wrapper']['filters']
        with self.assertRaisesRegex(ValueError, 'root/frame_1/depth_1'):
            validate_build_placements(timeline, 'yulong')

    def test_changed_or_conditional_reset_cannot_compile(self):
        for old, new in (('_this.filters = [];', '_this.filters = other;'),
                         ('\nresColor();', '\nif(flag) resColor();')):
            bundle = copy.deepcopy(self.bundle)
            script = next(s for s in bundle['scripts'] if s['path'] == 'DefineSprite_345/frame_1/DoAction.as')
            script['source'] = script['source'].replace(old, new)
            with self.subTest(new=new), self.assertRaisesRegex(ValueError, 'yulong.swf.*frame_1.*initialization'):
                compile_context(bundle, self.timeline)
