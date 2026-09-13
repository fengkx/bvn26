import json
import unittest
from pathlib import Path

from tools.test_move_references import resolve_fixture_character


ROOT = Path(__file__).resolve().parents[2]


class MoveReferenceRoleMappingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / 'manifest.json').read_text())['fighter_catalog']

    def test_sakura_directory_maps_to_exact_manifest_source_identity(self):
        self.assertEqual(resolve_fixture_character('sakura', self.manifest), '樱')
        fighter = json.loads((ROOT / 'godot/generated/fighters/sakura/fighter.json').read_text())
        self.assertEqual(fighter['source']['swf_path'], 'game/fighter/Sakura.swf')

    def test_legacy_renji_directory_maps_to_exact_manifest_source_identity(self):
        self.assertEqual(resolve_fixture_character('renji', self.manifest), '恋次')
        fighter = json.loads((ROOT / 'godot/generated/fighters/renji/fighter.json').read_text())
        self.assertEqual(fighter['source']['swf_path'], 'game/fighter/Renji.swf')

    def test_casefold_directory_ambiguity_is_rejected(self):
        class Directory:
            def __init__(self, name):
                self.name = name

            def is_dir(self):
                return True

        from tools.test_move_references import resolve_fixture_directory
        with self.assertRaisesRegex(ValueError, 'ambiguous'):
            resolve_fixture_directory('sakura', [Directory('Sakura'), Directory('sakura')])


if __name__ == '__main__':
    unittest.main()
