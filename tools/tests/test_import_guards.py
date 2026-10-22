"""Mutation tests for inputs that previously defaulted or disappeared."""
import json
from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/importer'))
from compile_ai_context import compile_context, movement_expression
from extract_timeline_geometry import build_frames, placement_delta
from import_guards import finite_numbers


class ImportGuardsTests(unittest.TestCase):
    def test_active_unsupported_placement_flags_fail(self):
        for flag in ('HasClassName',
                     'HasImage', 'HasVisible', 'OpaqueBackground'):
            with self.subTest(flag=flag):
                tag = ET.fromstring(f'<item type="PlaceObject3Tag" depth="1" '
                                    f'characterId="2" placeFlag{flag}="true"/>')
                with self.assertRaisesRegex(ValueError, r'fixture.swf.*frame_1.*' + flag):
                    build_frames([tag], 'fixture.swf/DefineSprite_7')

    def test_unknown_fields_and_children_fail_even_without_flags(self):
        for extra in ('futureField="1"', 'className="Foo"'):
            tag = ET.fromstring(f'<item depth="1" {extra}/>')
            with self.assertRaisesRegex(ValueError, 'unsupported PlaceObject field'):
                placement_delta(tag)
        with self.assertRaisesRegex(ValueError, 'unsupported PlaceObject child filters'):
            placement_delta(ET.fromstring('<item depth="1"><filters/></item>'))

    def test_missing_flagged_fields_fail_instead_of_defaulting(self):
        for flag, field in (('HasCharacter', 'characterId'), ('HasBlendMode', 'blendMode'),
                            ('HasRatio', 'ratio'), ('HasName', 'name'),
                            ('HasClipDepth', 'clipDepth'), ('HasMatrix', 'matrix'),
                            ('HasColorTransform', 'colorTransform'),
                            ('HasClipActions', 'clipActions')):
            with self.subTest(flag=flag), self.assertRaisesRegex(ValueError, 'requires ' + field):
                placement_delta(ET.fromstring(f'<item depth="1" placeFlag{flag}="true"/>'))

    def test_transform_missing_terms_and_nonfinite_values_fail(self):
        for child, expected in (
            ('<matrix hasScale="true" scaleX="1"/>', 'scaleY'),
            ('<matrix hasRotate="true" rotateSkew0="0"/>', 'rotateSkew1'),
            ('<colorTransform hasMultTerms="true" redMultTerm="256"/>', 'greenMultTerm'),
            ('<colorTransform hasAddTerms="true" redAddTerm="0"/>', 'greenAddTerm'),
            ('<matrix translateX="NaN"/>', 'non-finite'),
            ('<matrix translateX="Infinity"/>', 'non-finite'),
            ('<matrix translateX="undefined"/>', 'invalid numeric'),
            ('<matrix hasScale="1"/>', 'invalid'),
        ):
            with self.subTest(child=child), self.assertRaisesRegex(ValueError, expected):
                placement_delta(ET.fromstring(f'<item depth="1">{child}</item>'))

    def test_serialization_metadata_is_not_a_numeric_operand(self):
        placement = placement_delta(ET.fromstring('''<item depth="1" forceWriteAsLong="true">
            <matrix type="MATRIX" hasScale="false" translateX="20"/>
            <colorTransform type="CXFORMWITHALPHA" hasMultTerms="false"/>
            </item>'''))
        self.assertEqual(placement['matrix']['translateX'], 20)

    def test_nonfinite_json_and_expression_literals_fail(self):
        for value in (float('nan'), float('inf'), -float('inf')):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'fixture/frame_3/x'):
                finite_numbers({'frame_3': {'x': value}}, 'fixture')
        with self.assertRaisesRegex(ValueError, 'non-finite'):
            movement_expression('1e309 * speed', {'speed'})

    def test_unsupported_owned_call_arguments_fail_with_source(self):
        timeline = json.loads((ROOT / 'data/slices/didala-base.timeline.json').read_text())
        for call in ('_root.bsd();', '_root.bsd(other);', '_root.showFace(pn, name);',
                     'followMc(target);', 'updateDirect(1);', 'resColor(1);',
                     '_root.touchFloorEffect(other);', '_root.bsd(pn); extra();'):
            bundle = json.loads((ROOT / 'scripts/fighter/didala.json').read_text())
            next(s for s in bundle['scripts'] if s['path'] ==
                 'DefineSprite_542/frame_34/DoAction.as')['source'] = call
            with self.subTest(call=call), self.assertRaisesRegex(
                    ValueError, r'didala.swf.*frame_34.*uncompiled frame call'):
                compile_context(bundle, timeline)

    def test_movement_with_space_cannot_bypass_guard(self):
        bundle = json.loads((ROOT / 'scripts/fighter/didala.json').read_text())
        timeline = json.loads((ROOT / 'data/slices/didala-base.timeline.json').read_text())
        next(s for s in bundle['scripts'] if s['path'] ==
             'DefineSprite_542/frame_34/DoAction.as')['source'] = '_parent.moveX ();'
        with self.assertRaisesRegex(ValueError, 'Uncompiled wrapper movement.*didala.swf.*frame_34'):
            compile_context(bundle, timeline)



class NestedControlGuardsTests(unittest.TestCase):
    def fixture(self, source='stop();', controls=None):
        bundle = {'game_file': 'fixture.swf', 'swf_sha256': 'abc', 'scripts': [
            {'path': 'DefineSprite_2/frame_1/DoAction.as', 'source': source}]}
        timeline = {'source_swf': {'sha256': 'abc'}, 'definitions': [
            {'character_id': 2, 'display_list_frame_events': [[
                {'visual_controls': controls or []}]]}]}
        return timeline, bundle

    def test_anonymous_stop_missing_or_changed_is_rejected(self):
        from visual_control_guard import validate_nested_controls
        for controls in ([], [{'op': 'play'}]):
            timeline, bundle = self.fixture(controls=controls)
            with self.assertRaisesRegex(ValueError, 'fixture.swf.*frame_1.*dropped/changed'):
                validate_nested_controls(timeline, bundle, [])

    def test_goto_target_and_mode_are_checked(self):
        from visual_control_guard import validate_nested_controls
        timeline, bundle = self.fixture('gotoAndStop("end");',
                                       [{'op': 'goto', 'label': 'end'}, {'op': 'stop'}])
        validate_nested_controls(timeline, bundle, [])
        timeline['definitions'][0]['display_list_frame_events'][0][0]['visual_controls'][0]['label'] = 'start'
        with self.assertRaisesRegex(ValueError, 'dropped/changed'):
            validate_nested_controls(timeline, bundle, [])

    def test_conditional_stop_cannot_become_unconditional(self):
        from visual_control_guard import validate_nested_controls
        timeline, bundle = self.fixture('if(flag) { stop(); }', [{'op': 'stop'}])
        with self.assertRaisesRegex(ValueError, 'needs an owner'):
            validate_nested_controls(timeline, bundle, [])

    def test_expression_goto_or_nonempty_stop_is_rejected(self):
        from visual_control_guard import validate_nested_controls
        for source in ('gotoAndPlay(speed * 2);', 'gotoAndStop(other());', 'stop(1);'):
            timeline, bundle = self.fixture(source)
            with self.subTest(source=source), self.assertRaisesRegex(ValueError, 'unsupported nested'):
                validate_nested_controls(timeline, bundle, [])

    def test_frame_allowlist_is_scoped_and_hash_pinned(self):
        from import_guards import allowed_frame_source
        bundle = json.loads((ROOT / 'scripts/fighter/Byakuya.json').read_text())
        path = 'DefineSprite_631/frame_985/DoAction.as'
        source = next(s['source'] for s in bundle['scripts'] if s['path'] == path)
        self.assertTrue(allowed_frame_source(bundle, path, source, 1))
        self.assertFalse(allowed_frame_source(bundle, path, source, 2))
        self.assertFalse(allowed_frame_source(bundle, path, source + '\n', 1))
        self.assertFalse(allowed_frame_source(bundle, path + '.changed', source, 1))
        bundle['swf_sha256'] = 'changed'
        self.assertFalse(allowed_frame_source(bundle, path, source, 1))

    def test_shipped_control_requirements_match_locked_source(self):
        from visual_control_guard import requirements
        catalog = json.loads((ROOT / 'tools/importer/visual_control_requirements.json').read_text())
        for path in (ROOT / 'scripts').rglob('*.json'):
            bundle = json.loads(path.read_text())
            if 'swf_sha256' in bundle and 'scripts' in bundle:
                with self.subTest(path=path):
                    self.assertEqual(catalog[bundle['swf_sha256']], requirements(bundle))


if __name__ == '__main__':
    unittest.main()
