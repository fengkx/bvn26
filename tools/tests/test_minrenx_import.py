"""Source identity and replacement obligations for Sage Naruto; no admission claim."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/importer'))
from audit_form_profiles import audit_form_manifest
from compile_ai_context import compile_context
from extract_fighter_slice import extract_slice
from frame_call_guard import validate_cached_frame_calls


class MinrenxImportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = json.loads((ROOT / 'scripts/fighter/minrenx.json').read_text())
        cls.timeline = json.loads((ROOT / 'data/slices/minrenx-base.timeline.json').read_text())

    def test_standalone_source_identity(self):
        fighter = extract_slice(ROOT, '仙鸣')
        self.assertEqual(fighter['form_frame'], 1)
        self.assertEqual(fighter['source']['timeline_symbol_id'], 449)
        self.assertEqual(fighter['source']['swf_path'], 'game/fighter/minrenx.swf')

    def test_form_unaware_compilation_still_rejects_replacement(self):
        with self.assertRaisesRegex(ValueError, 'uncompiled form replacement call'):
            compile_context(self.bundle, self.timeline)

    def test_reviewed_graph_retains_both_source_replacement_calls(self):
        directory = ROOT / 'godot/generated/fighters/minrenx'
        contract = audit_form_manifest(directory, self.bundle)
        self.assertEqual(len(contract['nodes']), 2)
        context = json.loads((directory / 'ai.json').read_text())
        timeline = json.loads((directory / 'timeline.json').read_text())
        validate_cached_frame_calls(timeline, context, directory=directory)
        self.assertEqual(context['frame_calls']['1294'][0]['replacement']['target_body_sprite'], 1172)
        self.assertEqual(context['frame_calls']['1297'][0]['replacement']['target_body_sprite'], 1172)


if __name__ == '__main__':
    unittest.main()
