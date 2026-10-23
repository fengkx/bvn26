import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/importer'))
from parent_form_requirements import parent_form_requirement


class ParentFormRequirementsTests(unittest.TestCase):
    def setUp(self):
        self.bundle = json.loads((ROOT / 'scripts/fighter/daitu.json').read_text())

    def test_all_load_fields_are_preserved_in_source_order(self):
        result = parent_form_requirement(self.bundle, 2, 'fixture.swf:frame_1309')
        self.assertEqual((result['target_body_sprite'], result['target_depth']), (1138, 1))
        fields = {d['field']: d for d in result['load_declarations']}
        self.assertEqual(fields['spd']['value'], 17)
        self.assertEqual(fields['jumpPower']['value'], 20)
        self.assertEqual(fields['kcplayed']['value'], 0)
        self.assertEqual(fields['kis']['binding'], 'Key.isDown')
        self.assertEqual(result['status'], 'requires_replacement_runtime_and_assets')

    def test_unknown_load_statement_fails_with_both_locations(self):
        path = parent_form_requirement(self.bundle, 2, 'source')['load_path']
        next(s for s in self.bundle['scripts'] if s['path'] == path)['source'] = 'onClipEvent(load){\nvar speed = missing * 2;\n}'
        with self.assertRaisesRegex(ValueError, r'fixture.swf:frame_1309.*frame_2.*:2:.*missing'):
            parent_form_requirement(self.bundle, 2, 'fixture.swf:frame_1309')

    def test_missing_and_ambiguous_loads_fail(self):
        with self.assertRaisesRegex(ValueError, 'found 0'):
            parent_form_requirement(self.bundle, 99, 'fixture.swf')
        path = parent_form_requirement(self.bundle, 2, 'source')['load_path']
        duplicate = copy.deepcopy(next(s for s in self.bundle['scripts'] if s['path'] == path))
        duplicate['path'] = duplicate['path'].replace('_1138_1/', '_1139_2/')
        self.bundle['scripts'].append(duplicate)
        with self.assertRaisesRegex(ValueError, 'found 2'):
            parent_form_requirement(self.bundle, 2, 'fixture.swf')

    def test_missing_init_and_malformed_load_fail(self):
        requirement = parent_form_requirement(self.bundle, 2, 'fixture.swf')
        self.bundle['scripts'] = [s for s in self.bundle['scripts'] if s['path'] != requirement['body_init_path']]
        with self.assertRaisesRegex(ValueError, 'missing replacement body initialization'):
            parent_form_requirement(self.bundle, 2, 'fixture.swf')
        self.setUp()
        next(s for s in self.bundle['scripts'] if s['path'] == requirement['load_path'])['source'] = 'unknown();'
        with self.assertRaisesRegex(ValueError, 'unsupported parent target load'):
            parent_form_requirement(self.bundle, 2, 'fixture.swf')
