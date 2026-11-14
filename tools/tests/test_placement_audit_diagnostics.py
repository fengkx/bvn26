"""Inventory all independently rejected fields and use the real form contracts."""
from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'importer'))
from audit_importer import audit_xml, audit_shipped_contexts


class PlacementAuditDiagnosticsTests(unittest.TestCase):
    def test_bad_blend_cannot_hide_bad_filter_or_field(self):
        root = ET.fromstring('''<swf><tags><item type="PlaceObject3Tag" depth="7"
            characterId="9" blendMode="10" unexpected="true">
            <surfaceFilterList><item type="DROPSHADOWFILTER"/></surfaceFilterList>
            </item></tags></swf>''')
        row = audit_xml(root, 'fixture.swf')['failures'][0]
        self.assertEqual({d['field'] for d in row['diagnostics']}, {'fields', 'blend_mode', 'filters'})
        self.assertEqual(row['character_id'], 9)
        self.assertFalse(row['move'])
        for diagnostic in row['diagnostics']:
            self.assertIn('fixture.swf/root/frame_1/depth_7', diagnostic['error'])

    def test_move_error_resolves_previous_character(self):
        root = ET.fromstring('''<swf><tags>
            <item type="PlaceObject2Tag" depth="7" characterId="9"/>
            <item type="ShowFrameTag"/>
            <item type="PlaceObject3Tag" depth="7" placeFlagMove="true" blendMode="10"/>
            </tags></swf>''')
        row = audit_xml(root, 'fixture.swf')['failures'][0]
        self.assertEqual(row['character_id'], 9)
        self.assertTrue(row['move'])
        self.assertIn('frame_2/depth_7', row['error'])

    def test_rejected_field_lives_until_explicit_overwrite_not_unrelated_move(self):
        from placement_build_guard import placement_requirements, validate_build_placements
        from unittest.mock import patch
        import json
        root = ET.fromstring('''<swf><tags>
            <item type="PlaceObject3Tag" depth="7" characterId="9" blendMode="10"/>
            <item type="ShowFrameTag"/>
            <item type="PlaceObject2Tag" depth="7" placeFlagMove="true"/>
            <item type="ShowFrameTag"/>
            <item type="PlaceObject3Tag" depth="7" placeFlagMove="true" blendMode="1"/>
            <item type="ShowFrameTag"/>
            </tags></swf>''')
        report = {**audit_xml(root, 'fixture.swf'), 'sha256': 'abc'}
        self.assertEqual(report['failures'][0]['last_frame'], 2)
        catalog = placement_requirements([report])
        timeline = {'source_swf': {'sha256': 'abc'}, 'sprite_id': 0,
                    'definitions': [], 'frames': [{'frame': 2, 'display_list': []}]}
        with patch('placement_build_guard.Path.read_text', return_value=json.dumps(catalog)):
            with self.assertRaisesRegex(ValueError, 'fixture.swf/root/frame_1/depth_7'):
                validate_build_placements(timeline, 'later-frame-only.json')
            timeline['frames'] = []
            # The interval itself no longer rejects a slice after the explicit overwrite.
            catalog['abc']['obligations'] = []
            timeline['frames'] = [{'frame': 3, 'display_list': []}]
            with patch('placement_build_guard.Path.read_text', return_value=json.dumps(catalog)):
                validate_build_placements(timeline, 'repaired-frame.json')

    def test_new_failed_move_still_replaces_its_explicit_old_fields(self):
        root = ET.fromstring('''<swf><tags>
            <item type="PlaceObject3Tag" depth="7" characterId="9" blendMode="10"/>
            <item type="ShowFrameTag"/>
            <item type="PlaceObject3Tag" depth="7" placeFlagMove="true" blendMode="1">
              <surfaceFilterList><item type="DROPSHADOWFILTER"/></surfaceFilterList>
            </item><item type="ShowFrameTag"/>
            <item type="PlaceObject3Tag" depth="7" placeFlagMove="true"><surfaceFilterList/></item>
            <item type="ShowFrameTag"/>
            </tags></swf>''')
        failures = audit_xml(root, 'fixture.swf')['failures']
        self.assertEqual([r['last_frame'] for r in failures], [1, 2])
        self.assertEqual([r['diagnostics'][0]['field'] for r in failures], ['blend_mode', 'filters'])

    def test_remove_or_new_placement_ends_rejected_field_lifetime(self):
        for replacement in ('<item type="RemoveObject2Tag" depth="7"/>',
                            '<item type="PlaceObject2Tag" depth="7" characterId="10"/>'):
            root = ET.fromstring('<swf><tags><item type="PlaceObject3Tag" depth="7" characterId="9" blendMode="10"/>'
                                 '<item type="ShowFrameTag"/>' + replacement +
                                 '<item type="ShowFrameTag"/></tags></swf>')
            with self.subTest(replacement=replacement):
                self.assertEqual(audit_xml(root, 'fixture.swf')['failures'][0]['last_frame'], 1)

    def test_full_source_audit_accepts_all_current_form_aware_caches(self):
        rows = audit_shipped_contexts()
        self.assertEqual(len(rows), 27)
        self.assertEqual({r['status'] for r in rows}, {'passed'})
        for row in rows:
            self.assertEqual(row['compile_status'], 'passed')
            self.assertEqual(row['cache_status'], 'passed')
