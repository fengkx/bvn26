"""Keep selectable form frame calls synchronized with their source compiler."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/importer'))
from compile_ai_context import compile_context


class SelectedFormSourceTests(unittest.TestCase):
    def test_selected_form_contexts_match_fresh_source_compilation(self):
        available = json.loads((ROOT / 'godot/generated/main/character_selection/available.json').read_text())
        for slug in available['forms']:
            with self.subTest(form=slug):
                folder = ROOT / 'godot/generated/forms' / slug
                timeline = json.loads((folder / 'timeline.json').read_text())
                source_name = Path(timeline['source_swf']['path']).stem
                bundle = json.loads((ROOT / 'scripts/fighter' / (source_name + '.json')).read_text())
                self.assertEqual(
                    json.loads((folder / 'ai.json').read_text()),
                    compile_context(bundle, timeline, form_replacement=True),
                )


if __name__ == '__main__':
    unittest.main()
