"""Placement filters must remain source-bound until the authored reset executes."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/importer'))
from compile_ai_context import form_initialization


class FormFilterInitializationTests(unittest.TestCase):
    def setUp(self):
        bundle = json.loads((ROOT / 'scripts/fighter/minren.json').read_text())
        self.path = 'game/fighter/minren.swf:DefineSprite_1821/frame_1/DoAction.as'
        self.source = next(s['source'] for s in bundle['scripts']
                           if s['path'] == 'DefineSprite_1821/frame_1/DoAction.as')

    def test_original_initial_frame_compiles_exact_filter_reset(self):
        result = form_initialization(self.source, self.path, placement_filters=True)
        self.assertTrue(result['clear_placement_filters'])
        self.assertEqual(len(result['filter_reset_source_sha256']), 64)

    def test_changed_filter_reset_or_conditional_call_is_rejected(self):
        for source in (self.source.replace('_this.filters = [];', '_this.filters = other;'),
                       self.source.replace('\nresColor();', '\nif(flag) resColor();')):
            with self.subTest(source=source[-80:]), self.assertRaisesRegex(ValueError, 'minren.swf.*frame_1.*initialization'):
                form_initialization(source, self.path, placement_filters=True)
