"""Nested stage writes have a complete source compiler and cached obligation."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'importer'))
from compile_ai_context import nested_stage_frames
from frame_call_guard import validate_cached_frame_calls


class NestedStageFramesTest(unittest.TestCase):
    def bundle(self, source):
        return {'game_file': 'game/fighter/test.swf', 'scripts': [
            {'path': 'DefineSprite_7/frame_1/DoAction.as', 'source': source}]}

    def test_chain_and_flash_preserve_order(self):
        result = nested_stage_frames(self.bundle('_root._x = _root._y = 0;\n_root.shine();'),
                                     {'definitions': [{'character_id': 7}]})
        events = result['7']['1']['events']
        self.assertEqual([e['op'] for e in events], ['root_position', 'root_position', 'screen_flash'])
        self.assertEqual([e['axis'] for e in events[:2]], ['y', 'x'])

    def test_unsupported_expression_condition_and_sibling_call_reject(self):
        for source in ('_root._y -= speed * 5;', 'if (ready) { _root._y -= 5; }',
                       '_root._y -= 5;\nunknown();'):
            with self.subTest(source=source), self.assertRaisesRegex(ValueError, r'test.swf:DefineSprite_7/frame_1/DoAction.as:[12]: unsupported nested'):
                nested_stage_frames(self.bundle(source), {'definitions': [{'character_id': 7}]})

    def test_nonfinite_literal_rejects_with_source(self):
        with self.assertRaisesRegex(ValueError, 'DefineSprite_7/frame_1/DoAction.as'):
            nested_stage_frames(self.bundle('_root._y = ' + '9' * 400 + ';'), {'definitions': [{'character_id': 7}]})

    def test_cached_drop_or_mutation_reject(self):
        timeline = {'source_swf': {'sha256': 'hash'}, 'sprite_id': 1}
        actions = nested_stage_frames(self.bundle('_root._y -= 5;'), {'definitions': [{'character_id': 7}]})
        cached = {**timeline, 'nested_stage_frames': actions}
        catalog = {'hash:1': {'source': 'game/fighter/test.swf', 'frames': {}, 'nested_stage_frames': actions}}
        validate_cached_frame_calls(timeline, cached, catalog)
        for changed in ({}, {'7': {'1': {'events': []}}}):
            bad = copy.deepcopy(cached)
            bad['nested_stage_frames'] = changed
            with self.assertRaisesRegex(ValueError, 'dropped/changed nested stage'):
                validate_cached_frame_calls(timeline, bad, catalog)
