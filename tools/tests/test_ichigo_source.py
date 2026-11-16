"""Source invariants for the standalone Ichigo roster entry and its replacement."""
import json
import copy
from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/importer'))
from compile_ai_context import conditional_frame_calls
from extract_timeline_geometry import referenced_definitions
from bitmap_shape_polygon import adjacent_fill_boundary
from undefined_body_calls import resolve_undefined_body_calls
from compile_ai_controller import compile_body as compile_controller_body


class IchigoSourceTests(unittest.TestCase):
    def test_absent_method_keeps_calls_and_refuses_new_bindings(self):
        bundle = json.loads((ROOT / 'scripts/fighter/ichigo.json').read_text())
        resolved = resolve_undefined_body_calls(bundle, 632)
        self.assertEqual([r['name'] for r in resolved], ['setDirect'])
        code = compile_controller_body('probe', '', '_parent.setDirect(-1);',
                                       undefined_body_calls=['setDirect'])
        self.assertIn('adapter.body_call("setDirect", [', code)
        with self.assertRaisesRegex(ValueError, 'Unreviewed undefined BODY'):
            compile_controller_body('probe', '', '_parent.setDirect(-1);')
        changed = copy.deepcopy(bundle)
        changed['scripts'].append({'path': 'new/DoAction.as',
                                   'source': 'function setDirect(direction) {}'})
        with self.assertRaisesRegex(ValueError, 'unresolved source binding'):
            resolve_undefined_body_calls(changed, 632)

    def test_mask_union_rejects_disconnected_duplicate_and_crossing_edges(self):
        rectangle = [[0, 0], [2, 0], [2, 2], [0, 2]]
        self.assertIsNone(adjacent_fill_boundary([rectangle, rectangle]))
        self.assertIsNone(adjacent_fill_boundary([
            rectangle, [[3, 0], [4, 0], [4, 1], [3, 1]]]))
        # A shared edge alone cannot justify a self-intersecting outer contour.
        self.assertIsNone(adjacent_fill_boundary([
            rectangle, [[2, 0], [0, 0], [3, 3], [3, -1]]]))

    def test_opponent_recovery_preserves_stop_then_play(self):
        bundle = json.loads((ROOT / 'scripts/fighter/ichigo.json').read_text())
        path = 'DefineSprite_274/frame_415/DoAction.as'
        source = next(s['source'] for s in bundle['scripts'] if s['path'] == path)
        calls = conditional_frame_calls(source, path, 415)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]['conditions'],
                         [{'field': 'opponent_action', 'operator': 'eq', 'value': -1}])
        self.assertEqual(calls[0]['calls'], [])
        self.assertEqual(calls[0]['else_calls'], [
            {'op': 'timeline_goto', 'label': '站立', 'play': False},
            {'op': 'timeline_play'},
        ])
        self.assertEqual(conditional_frame_calls(source + '\nunknown();', path, 415), [])

    def test_mask_uses_both_adjacent_authored_fills(self):
        shape = ET.parse(ROOT / 'evidence/characters/ichigo/source-mask309.xml').getroot()
        root = ET.Element('swf')
        tags = ET.SubElement(root, 'tags')
        tags.append(shape)
        ET.SubElement(tags, 'item', type='PlaceObject2Tag', characterId='309',
                      placeFlagHasClipDepth='true', clipDepth='29')
        definition = referenced_definitions(root, [
            {'frame': 1, 'display_list': [{'character_id': 309}]}])[0]
        polygon = definition['mask_polygon']
        self.assertEqual(set(map(tuple, polygon)), {
            (38.15, 62.15), (38.15, 74.75), (9.75, 74.75), (9.75, 51.6),
            (38.15, 51.6), (38.15, 57.55), (40.75, 57.55), (40.75, 62.15),
        })


if __name__ == '__main__':
    unittest.main()
