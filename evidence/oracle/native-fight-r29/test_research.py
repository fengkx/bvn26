"""Recheck public-source evidence without connecting or promoting client IDs to native proof."""
import gzip
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from analyze import HERE, FLAGS, analyze, inspect_client, read_sources

PREFIX = 'modules/debugger/src/java/flash/tools/debugger/'

class ResearchTests(unittest.TestCase):
    def test_actual_protocol_lead_is_not_native_binding(self):
        result = analyze()
        self.assertEqual(result['message_constants']['InPlaceObject'], 13)
        self.assertEqual(result['message_constants']['InRemoveObject'], 4)
        self.assertTrue(result['independent_source_semantics_found'])
        self.assertIsNone(result['native_boundary'])
        for flag in [*FLAGS, 'native_return_proven', 'target_call_join_proven',
                     'pinned_player_emission_proven', 'live_started']:
            self.assertIs(result[flag], False)
        self.assertEqual(result['historical_structural_refusal'], 'Incomplete actor state at clock boundary')

    def test_public_snapshot_tampering_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            shutil.copyfile(HERE / 'source-receipts.json', directory / 'source-receipts.json')
            shutil.copytree(HERE / 'public-sources', directory / 'public-sources')
            row = json.loads((directory / 'source-receipts.json').read_text())['sources'][0]
            (directory / row['snapshot']).write_bytes(gzip.compress(b'changed source'))
            with self.assertRaisesRegex(ValueError, 'snapshot mismatch'):
                read_sources(directory)

    def test_changed_retention_behavior_requires_reassessment(self):
        sources = read_sources()
        key = PREFIX + 'concrete/DManager.java'
        sources[key] = sources[key].replace('// m_bag.removeObject', 'm_bag.removeObject')
        with self.assertRaisesRegex(ValueError, 'handler changed'):
            inspect_client(sources)

    def test_protocol_message_is_not_inferred_from_name_alone(self):
        sources = read_sources(); key = PREFIX + 'concrete/DMessage.java'
        sources[key] = sources[key].replace('InRemoveObject', 'OtherMessage')
        with self.assertRaisesRegex(ValueError, 'Nonunique message'):
            inspect_client(sources)

    def test_null_and_frame_semantics_are_required_anchors(self):
        for filename, phrase in [('Session.java', 'go out of scope are no longer accessible'),
                                 ('Frame.java', 'only valid when execution has suspended'),
                                 ('concrete/DManager.java', 'attempting to guess')]:
            sources = read_sources(); key = PREFIX + filename
            sources[key] = sources[key].replace(phrase, 'changed contract')
            with self.assertRaisesRegex(ValueError, 'semantic anchor'):
                inspect_client(sources)

    def test_avm2_source_cannot_be_silently_relabelled(self):
        sources = read_sources()
        sources['doc/avmspec/intro.dox'] = sources['doc/avmspec/intro.dox'].replace('\\page AVM2', '\\page AVM1')
        with self.assertRaisesRegex(ValueError, 'semantic anchor'):
            inspect_client(sources)

    def test_debug_client_is_not_assumed_passive(self):
        result = inspect_client(read_sources())
        self.assertTrue(result['source_checks']['client_sends_script_stuck_options'])
        self.assertTrue(result['source_checks']['incoming_this_id_discarded'])
        self.assertTrue(result['source_checks']['frame_mapping_heuristic'])
        self.assertFalse(result['current_host_compatibility_tested'])
