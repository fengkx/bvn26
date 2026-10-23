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

    def test_unknown_duplicate_and_incomplete_transform_fields_fail(self):
        cases = [('<matrix futureNumeric="1"/>', 'unsupported matrix'),
                 ('<matrix/><matrix/>', 'duplicate PlaceObject child matrix'),
                 ('<matrix type="MATRIX" translateX="0"/>', 'requires translateY'),
                 ('<matrix type="MATRIX" translateY="0"/>', 'requires translateX'),
                 ('<colorTransform type="CXFORMWITHALPHA" hasMultTerms="true" redMultTerm="256" greenMultTerm="256" blueMultTerm="256"/>', 'requires alphaMultTerm'),
                 ('<colorTransform type="CXFORMWITHALPHA" hasAddTerms="true" redAddTerm="0" greenAddTerm="0" blueAddTerm="0"/>', 'requires alphaAddTerm')]
        for fields, error in cases:
            with self.subTest(fields=fields), self.assertRaisesRegex(ValueError, 'fixture.swf/frame_9:.*' + error):
                placement_delta(ET.fromstring('<item depth="1">' + fields + '</item>'), 'fixture.swf/frame_9')
        for fields in ('depth="NaN"', 'depth="1" ratio="undefined"', 'depth="1" reserved="1"'):
            with self.subTest(fields=fields), self.assertRaisesRegex(ValueError, 'fixture.swf/frame_9:'):
                placement_delta(ET.fromstring('<item ' + fields + '/>'), 'fixture.swf/frame_9')

    def test_serialization_metadata_is_not_a_numeric_operand(self):
        placement = placement_delta(ET.fromstring('''<item depth="1" forceWriteAsLong="true">
            <matrix type="MATRIX" hasScale="false" translateX="20" translateY="0"/>
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
                     '_root.touchFloorEffect(other);', '_root.bsd(pn); extra();',
                     'gotoAndPlay(130);', 'gotoAndStop(frame + 1);', 'stop(1);',
                     'child.gotoAndPlay(130);', 'child.stop();', 'child.play();',
                     '_root.shunbuxg(other);', '_root.shine(color);'):
            bundle = json.loads((ROOT / 'scripts/fighter/didala.json').read_text())
            next(s for s in bundle['scripts'] if s['path'] ==
                 'DefineSprite_542/frame_34/DoAction.as')['source'] = call
            with self.subTest(call=call), self.assertRaisesRegex(
                    ValueError, r'didala.swf.*frame_34.*uncompiled frame call'):
                compile_context(bundle, timeline)

    def test_shared_rush_wrapper_and_literal_flash_are_compiled(self):
        bundle = json.loads((ROOT / 'scripts/fighter/didala.json').read_text())
        timeline = json.loads((ROOT / 'data/slices/didala-base.timeline.json').read_text())
        next(s for s in bundle['scripts'] if s['path'] ==
             'DefineSprite_542/frame_34/DoAction.as')['source'] = (
                 '_root.shunbuxg(_parent);\n_root.shine(303095);')
        calls = compile_context(bundle, timeline)['frame_calls']['34']
        self.assertEqual(calls[0]['op'], 'frame_child_effect')
        self.assertEqual(calls[0]['clip'], 'XG_rush')
        self.assertEqual((calls[0]['offset_x'], calls[0]['offset_y']), (0, 0))
        self.assertTrue(calls[0]['wrapper_sha256'])
        self.assertEqual(calls[1]['color_rgb24'], 303095)
        next(s for s in bundle['scripts'] if s['path'] ==
             'DefineSprite_542/frame_34/DoAction.as')['source'] = '_root.shine(16777216);'
        with self.assertRaisesRegex(ValueError, r'didala.swf.*frame_34.*unsupported shine color'):
            compile_context(bundle, timeline)

    def test_conditional_stop_is_owned_and_cached_calls_cannot_disappear(self):
        from frame_call_guard import calls_digest, validate_cached_frame_calls
        bundle = json.loads((ROOT / 'scripts/fighter/didala.json').read_text())
        timeline = json.loads((ROOT / 'data/slices/didala-base.timeline.json').read_text())
        cached = compile_context(bundle, timeline)
        call = cached['frame_calls']['942'][0]
        self.assertEqual(call['conditions'], [{'field': 'sw', 'operator': 'eq', 'value': True}])
        self.assertEqual(call['calls'], [{'op': 'timeline_stop'}])
        catalog = {f"{bundle['swf_sha256']}:{timeline['sprite_id']}": {
            'source': bundle['game_file'], 'frames': {f: calls_digest(c) for f, c in cached['frame_calls'].items()}}}
        validate_cached_frame_calls(timeline, cached, catalog)
        with self.assertRaisesRegex(ValueError, 'missing reviewed frame-call requirements'):
            validate_cached_frame_calls(timeline, cached, {})
        key = next(iter(catalog))
        with self.assertRaisesRegex(ValueError, 'fixture.swf.*unsupported goto'):
            validate_cached_frame_calls(timeline, cached, {key: {
                'source': 'fixture.swf', 'error': 'fixture.swf/frame_9: unsupported goto'}})
        with self.assertRaisesRegex(ValueError, 'source identity mismatch'):
            validate_cached_frame_calls(timeline, {**cached, 'sprite_id': 999}, catalog)
        effect = {'op': 'frame_child_effect', 'clip': 'missing_effect_fixture'}
        cached['frame_calls']['942'].append(effect)
        catalog[key]['frames']['942'] = calls_digest(cached['frame_calls']['942'])
        with self.assertRaisesRegex(ValueError, r'didala.swf.*frame_942.*missing compiled child effect'):
            validate_cached_frame_calls(timeline, cached, catalog)
        del cached['frame_calls']['942']
        with self.assertRaisesRegex(ValueError, r'didala.swf.*frame_942.*cached frame calls'):
            validate_cached_frame_calls(timeline, cached, catalog)

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


class FilterGuardsTests(unittest.TestCase):
    def test_placement_diagnostic_keeps_swf_and_frame(self):
        for fields in ('blendMode="13"', ''):
            tag = ET.fromstring('<item type="PlaceObject3Tag" depth="1" ' + fields +
                                '><surfaceFilterList><item type="DROPSHADOWFILTER"/>'
                                '</surfaceFilterList></item>')
            with self.subTest(fields=fields), self.assertRaisesRegex(
                    ValueError, 'fixture.swf/DefineSprite_7/frame_3'):
                placement_delta(tag, 'fixture.swf/DefineSprite_7/frame_3')

    def test_shipped_filter_records_are_supported(self):
        from visual_filters import compile_filters
        records = json.loads((ROOT / 'evidence/importer-loud-fail/shipped-filters.json').read_text())
        for record in records:
            with self.subTest(record=record):
                self.assertTrue(compile_filters(ET.fromstring(record['filters']), record['swf']))

    def test_unhandled_or_malformed_filter_fields_name_source(self):
        from visual_filters import compile_filters
        glow = '<item type="GLOWFILTER" blurX="5" blurY="5" passes="1" strength="1" innerGlow="false" knockout="false" compositeSource="true"><glowColor red="81" green="211" blue="239" alpha="255"/></item>'
        blur = '<item type="BLURFILTER" blurX="15" blurY="0" passes="1"/>'
        matrix = '<item type="COLORMATRIXFILTER"><matrix>' + '<item>0</item>' * 20 + '</matrix></item>'
        mutations = [blur.replace('15', 'undefined'), blur.replace('15', 'NaN'),
                     blur.replace('passes="1"', 'passes="1.5"'),
                     blur.replace('/>', ' reserved="1"/>'), blur.replace('/>', ' id="2"/>'),
                     glow.replace('innerGlow="false"', 'innerGlow="true"'),
                     glow.replace('knockout="false"', 'knockout="true"'),
                     glow.replace('compositeSource="true"', 'compositeSource="false"'),
                     glow.replace('red="81"', 'red="256"'), glow.replace('red="81"', ''),
                     glow.replace('strength="1"', ''), glow.replace('red="81"', 'extra="1" red="81"'),
                     matrix.replace('<matrix>', '<matrix extra="1">'),
                     matrix.replace('<item>0</item>', '<unknown>0</unknown>', 1),
                     matrix.replace('</matrix>', '</matrix><matrix/>'),
                     '<item type="BEVELFILTER"/>']
        for value in mutations:
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'fixture.swf/frame_7:'):
                compile_filters(ET.fromstring('<surfaceFilterList>' + value + '</surfaceFilterList>'),
                                'fixture.swf/frame_7')


class CachedPlacementGuardsTests(unittest.TestCase):
    def test_dropped_or_changed_cached_placement_fails(self):
        from copy import deepcopy
        from unittest.mock import patch
        from placement_build_guard import validate_build_placements
        fields = {'filters': [{'type': 'BLURFILTER', 'blurX': 15, 'blurY': 0, 'passes': 3}],
                  'cache_as_bitmap': True, 'blend_mode': 3,
                  'color_transform': {'alphaMultTerm': 128}}
        catalog = {'abc': {'swf': 'fixture.swf', 'records': [], 'obligations': [
            {'sprite': 2, 'frame': 2, 'depth': 1, 'fields': fields}]}}
        timeline = {'source_swf': {'sha256': 'abc'}, 'sprite_id': 1, 'frames': [],
                    'definitions': [{'character_id': 2, 'type': 'DefineSpriteTag',
                                     'display_list_frames': [[], [{'depth': 1, **fields}]]}]}
        with patch('placement_build_guard.Path.read_text', return_value=json.dumps(catalog)):
            validate_build_placements(timeline, 'fixture.json')
            for field in fields:
                changed = deepcopy(timeline)
                del changed['definitions'][0]['display_list_frames'][1][0][field]
                with self.subTest(field=field), self.assertRaisesRegex(
                        ValueError, field + '.*fixture.swf sprite 2 frame 2 depth 1'):
                    validate_build_placements(changed, 'fixture.json')
            for frames in ([[]], [[], []]):
                changed = deepcopy(timeline)
                changed['definitions'][0]['display_list_frames'] = frames
                with self.subTest(frames=frames), self.assertRaisesRegex(
                        ValueError, 'missing source.*fixture.swf.*frame 2'):
                    validate_build_placements(changed, 'fixture.json')


if __name__ == '__main__':
    unittest.main()
