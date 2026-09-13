"""Prevent comparing original and GameWorld traces with different helpers."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from test_move_references import (  # noqa: E402
    assert_fixture_helper_configuration,
    resolve_fixture_helper,
)


class MoveReferenceHelperMappingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads((ROOT / 'manifest.json').read_text())['fighter_catalog']

    def test_jinye_and_kon_match_original_source_roles(self):
        template = {
            'configuration': {'p1sf': '松本', 'p2sf': '魂'},
            'p1_helper': '松本',
            'p2_helper': None,
        }
        case = {'p1_helper': 'jinye', 'p2_helper': 'kon'}
        case['source_helpers'] = {
            'p1': resolve_fixture_helper('jinye', self.catalog),
            'p2': resolve_fixture_helper('kon', self.catalog),
        }
        assert_fixture_helper_configuration(case, template, self.catalog)

    def test_missing_explicit_jinye_helper_rejects_mixed_comparison(self):
        template = {
            'configuration': {'p1sf': '松本', 'p2sf': '魂'},
            'p1_helper': '松本',
        }
        with self.assertRaisesRegex(ValueError, 'Fixture/probe helper mismatch: p1'):
            assert_fixture_helper_configuration({}, template, self.catalog)

    def test_source_stem_maps_to_exact_swf_and_manifest_hash(self):
        helper = resolve_fixture_helper('jinye', self.catalog)
        self.assertEqual(helper['id'], '松本')
        self.assertEqual(helper['swf'], 'game/fighter/fz/jinye.swf')
        self.assertEqual(
            helper['sha256'],
            '03736bfd2ef7e9b79f958971fc7192ea641653039212e29793ed291c56bfa62a',
        )


if __name__ == '__main__':
    unittest.main()
