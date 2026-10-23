import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/importer'))
from stage_parent_forms import resolve_target, stage
from extract_fighter_slice import extract_slice


class ParentFormStagingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.requirements = json.loads((ROOT / 'evidence/importer-loud-fail/r07/parent-form-requirements.json').read_text())

    def test_four_targets_bind_to_catalog_and_locked_source(self):
        for row in self.requirements:
            key, bundle = resolve_target(row)
            self.assertTrue(key)
            self.assertEqual(bundle['swf_sha256'], row['source_swf_sha256'])

    def test_unlisted_replacement_uses_exact_parent_placement(self):
        row = next(r for r in self.requirements if r['source'].endswith('/daitu.swf'))
        key, _ = resolve_target(row)
        result = extract_slice(ROOT, key, allow_forms=True, parent_frame=2)
        self.assertEqual(result['form_frame'], 2)
        self.assertEqual(result['source']['timeline_symbol_id'], 1138)
        self.assertEqual(result['movement_constants']['speed_per_tick'], 17)
        self.assertIn('frame_2/PlaceObject2_1138_1/', result['movement_constants']['source']['path'])
        for value in (0, True, 2.5):
            with self.assertRaises(ValueError):
                extract_slice(ROOT, key, allow_forms=True, parent_frame=value)
        with self.assertRaises(ValueError):
            extract_slice(ROOT, key, parent_frame=2)

    def test_stale_source_or_load_obligations_reject_before_export(self):
        for field, value in [('source_swf_sha256', '0' * 64),
                             ('target_body_sprite', 1), ('target_depth', True), ('load_sha256', '0' * 64),
                             ('load_declarations', [])]:
            row = copy.deepcopy(self.requirements[0])
            row[field] = value
            with tempfile.TemporaryDirectory() as temporary, patch('stage_parent_forms.export_swf') as export:
                results = stage([row], Path('unused.jar'), Path(temporary) / 'forms')
                self.assertEqual(results[0]['stages']['source']['status'], 'failed')
                self.assertFalse(results[0]['runtime_integrated'])
                export.assert_not_called()

    def test_existing_output_is_not_reused(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(FileExistsError):
                stage([], Path('unused.jar'), Path(temporary))


if __name__ == '__main__':
    unittest.main()
