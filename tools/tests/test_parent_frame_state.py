import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/importer'))
from compile_ai_context import compile_context, conditional_frame_calls, parent_initial_values, writes
from frame_call_guard import validate_cached_frame_calls


class ParentFrameStateTests(unittest.TestCase):
    def test_source_blocks_keep_condition_and_call_before_write(self):
        for name, sprite, frame in [('minren', 1293, 996), ('Sasuke', 1019, 1024)]:
            bundle = json.loads((ROOT / f'scripts/fighter/{name}.json').read_text())
            path = f'DefineSprite_{sprite}/frame_{frame}/DoAction.as'
            source = next(s['source'] for s in bundle['scripts'] if s['path'] == path)
            calls = conditional_frame_calls(source, path, frame)
            self.assertEqual(writes(source, path), [])
            self.assertEqual(calls[0]['op'], 'parent_conditional_frame')
            self.assertEqual([c['op'] for c in calls[0]['calls']], ['super_end', 'frame_field'])
            self.assertEqual(parent_initial_values(bundle, {str(frame): calls}), {'万解': False})
            mutated = source.replace('_parent.万解', '_parent.unknown')
            with self.assertRaisesRegex(ValueError, 'missing/ambiguous parent boolean initializer'):
                parent_initial_values(bundle, {str(frame): conditional_frame_calls(mutated, path, frame)})

    def test_extra_conditional_statement_is_not_accepted(self):
        source = 'if(_parent.万解 == true) { _root.cbsw(pn); bs = 0; unexpected(); }'
        self.assertEqual(conditional_frame_calls(source, 'fixture', 1), [])

    def test_cached_parent_initializer_cannot_be_removed_or_changed(self):
        directory = ROOT / 'godot/generated/fighters/byakuya'
        timeline = json.loads((directory / 'timeline.json').read_text())
        cached = json.loads((directory / 'ai.json').read_text())
        # Test initializer validation independently of the now-rejected wankai call.
        cached['frame_calls'] = {}
        key = f"{timeline['source_swf']['sha256']}:{timeline['sprite_id']}"
        catalog = {key: {'source': timeline['source_swf']['path'], 'frames': {},
                         'parent_initial_values': {'万解': False}}}
        validate_cached_frame_calls(timeline, cached, catalog)
        for value in ({}, {'万解': True}, {'万解': 0}, {'万解': None}):
            broken = copy.deepcopy(cached)
            broken['parent_initial_values'] = value
            with self.assertRaisesRegex(ValueError, 'dropped/changed parent initial values'):
                validate_cached_frame_calls(timeline, broken, catalog)

    def test_frame_interval_cannot_disappear_behind_parent_flag_write(self):
        bundle = json.loads((ROOT / 'scripts/fighter/minren.json').read_text())
        timeline = json.loads((ROOT / 'godot/generated/fighters/minren/timeline.json').read_text())
        # Isolate the timer guard from the earlier, independently rejected transfer.
        timeline['frames'] = [f for f in timeline['frames'] if f['frame'] not in (1379, 1380)]
        with self.assertRaisesRegex(ValueError, r'minren.swf.*frame_1381.*:3: uncompiled frame timer'):
            compile_context(bundle, timeline)

    def test_parent_write_expression_is_not_silently_ignored(self):
        bundle = json.loads((ROOT / 'scripts/fighter/didala.json').read_text())
        timeline = json.loads((ROOT / 'data/slices/didala-base.timeline.json').read_text())
        next(s for s in bundle['scripts'] if s['path'] == 'DefineSprite_542/frame_34/DoAction.as')['source'] = '_parent.万解 = other;'
        with self.assertRaisesRegex(ValueError, r'didala.swf.*frame_34.*uncompiled parent boolean write'):
            compile_context(bundle, timeline)

    def test_replacement_helpers_fail_at_the_call_and_name_the_definition(self):
        for name, sprite, frame in [('daitu', 458, 1307), ('yihu', 638, 1052)]:
            bundle = json.loads((ROOT / f'scripts/fighter/{name}.json').read_text())
            timeline = json.loads((ROOT / f'godot/generated/fighters/{name}/timeline.json').read_text())
            with self.assertRaisesRegex(ValueError, rf'{name}.swf.*frame_{frame}.*uncompiled form replacement call.*#wankai sha256='):
                compile_context(bundle, timeline)

    def test_wrapper_transfer_is_not_a_body_scalar_write(self):
        for name, source, frame in [('minren', 'minren', 1379), ('sasuke', 'Sasuke', 1228)]:
            bundle = json.loads((ROOT / f'scripts/fighter/{source}.json').read_text())
            timeline = json.loads((ROOT / f'godot/generated/fighters/{name}/timeline.json').read_text())
            with self.assertRaisesRegex(ValueError, rf'{source}.swf.*frame_{frame}.*:5: uncompiled wrapper transfer:.*中转.ql = ql'):
                compile_context(bundle, timeline)

    def test_existing_caches_cannot_bypass_newly_detected_form_calls(self):
        for name, frame in [('byakuya', 1110), ('rifagu', 1233), ('rukia', 1164)]:
            directory = ROOT / f'godot/generated/fighters/{name}'
            timeline = json.loads((directory / 'timeline.json').read_text())
            cached = json.loads((directory / 'ai.json').read_text())
            with self.assertRaisesRegex(ValueError, rf'frame_{frame}.*uncompiled form replacement call'):
                validate_cached_frame_calls(timeline, cached)
