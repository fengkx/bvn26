"""Source invariants for the Ulquiorra base candidate; not parity admission."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/importer'))
from build_combat_model import parse_body_warp
from compile_ai_context import compile_context
from extract_fighter_slice import extract_slice
from audit_form_profiles import audit_form_manifest
from frame_call_guard import validate_cached_frame_calls


class WeqalImportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = json.loads((ROOT / 'scripts/fighter/weqal.json').read_text())
        cls.scripts = {item['path']: item['source'] for item in cls.bundle['scripts']}
        cls.timeline = json.loads((ROOT / 'data/slices/weqal-base.timeline.json').read_text())

    def test_base_identity_is_source_selected(self):
        fighter = extract_slice(ROOT, '小乌')
        self.assertEqual(fighter['form_frame'], 1)
        self.assertEqual(fighter['source']['timeline_symbol_id'], 387)
        self.assertEqual(fighter['source']['swf_path'], 'game/fighter/weqal.swf')

    def test_low_attack_reverses_facing_and_copies_both_axes(self):
        source = self.scripts['DefineSprite_387/frame_233/DoAction.as']
        self.assertEqual(parse_body_warp(source), {
            'op': 'warp_to_opponent', 'place_x': True, 'place_y': True,
            'xscale_lt_0': {'set_xscale': 100.0, 'x_pixels': -100.0},
            'xscale_gt_0': {'set_xscale': -100.0, 'x_pixels': 100.0},
        })

    def test_normal_super_falls_through_to_air_super(self):
        labels = {label: frame['frame'] for frame in self.timeline['frames'] for label in frame['labels']}
        self.assertEqual((labels['必杀'], labels['空中必杀']), (468, 469))
        self.assertNotIn('DefineSprite_387/frame_468/DoAction.as', self.scripts)
        self.assertEqual(self.scripts['DefineSprite_387/frame_470/DoAction.as'].strip(),
                         '动作 = 3;\r\nbs = 1;\r\nql -= 100;')

    def test_replacement_calls_require_the_complete_graph(self):
        # A form-unaware compile must still reject the reachable source call.
        with self.assertRaisesRegex(ValueError, 'uncompiled form replacement call'):
            compile_context(self.bundle, self.timeline)
        compiled = compile_context(self.bundle, self.timeline, form_replacement=True)
        calls = compiled['frame_calls']['1148']
        self.assertEqual(calls[0]['op'], 'body_form_call')
        self.assertEqual(calls[0]['replacement']['target_body_sprite'], 808)
        self.assertEqual(compiled['frame_calls']['1152'][0]['op'], 'parent_form_goto')

    def test_reviewed_graph_closes_both_replacement_edges(self):
        directory = ROOT / 'godot/generated/fighters/weqal'
        contract = audit_form_manifest(directory, self.bundle)
        self.assertEqual(len(contract['nodes']), 2)
        context = json.loads((directory / 'ai.json').read_text())
        timeline = json.loads((directory / 'timeline.json').read_text())
        validate_cached_frame_calls(timeline, context, directory=directory)
        self.assertEqual(context['frame_calls']['1152'][0]['replacement']['target_body_sprite'], 808)

    def test_failure_falls_through_without_input(self):
        combat = json.loads((ROOT / 'data/actions/weqal-base.json').read_text())
        entries = combat['timeline_fallthroughs']
        self.assertTrue(any(row.get('from') == '失败' and row.get('to') == '万解' for row in entries), entries)


if __name__ == '__main__':
    unittest.main()
