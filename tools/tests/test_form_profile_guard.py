"""Replacement activation requires complete packages and reviewed source graphs."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'importer'))
from form_profile_guard import FORMAT, METHODS, digest, package_hashes, validate_form_manifest
from frame_call_guard import validate_cached_frame_calls


class FormProfileGuardTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.base = self.root / 'godot/generated/fighters/fixture'
        self.target = self.root / 'godot/generated/forms/fixture-2'
        source = {'path': 'game/fighter/fixture.swf', 'sha256': 'a' * 64}
        self.requirements = {str(frame): {'target_parent_frame': frame,
            'target_body_sprite': sprite, 'target_depth': 1,
            'load_path': f'frame_{frame}/PlaceObject2_{sprite}_1/load.as',
            'load_sha256': str(frame) * 64, 'source_swf_sha256': source['sha256'],
            'body_init_path': f'DefineSprite_{sprite}/frame_1/DoAction.as',
            'body_init_sha256': str(sprite) * 32,
            'load_declarations': [{'field': 'touch', 'value': True, 'line': 2}]}
            for frame, sprite in ((1, 11), (2, 22))}
        self.nodes = {}
        for frame, target, sprite in (('1', self.base, 11), ('2', self.target, 22)):
            target.mkdir(parents=True)
            files = {'timeline.json': {'source_swf': source, 'sprite_id': sprite},
                     'ai.json': {'source_swf': source, 'sprite_id': sprite,
                         'parent_initial_values': {'万解': False}, 'frame_calls': {}},
                     'player_controller/body.json': {'swf_sha256': source['sha256'],
                         'source_sha256': self.requirements[frame]['body_init_sha256'], 'functions': sorted(METHODS)},
                     'assets.json': {'assets': [{'path': 'image.png'}]}}
            if frame == '1':
                files['ai.json']['frame_calls']['1307'] = [{'op': 'body_form_call', 'method': 'wankai',
                    'replacement': self.requirements['2']}]
            for name in ('fighter.json', 'combat.json', 'hurt_voice.json', 'sound_segments.json', 'player_controller/controller.json'):
                files[name] = {}
            for name, value in files.items():
                path = target / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(value))
            for name in ('image.png', 'ai_hit_state.gd', 'player_controller/body.gd', 'player_controller/controller.gd', 'player_controller/predicates.gd'):
                (target / name).write_text('fixture')
            context = files['ai.json']
            self.nodes[frame] = {'sprite_id': sprite, 'requirement': self.requirements[frame],
                'frames': {key: digest(value) for key, value in context['frame_calls'].items()},
                'parent_initial_values_digest': digest([context['parent_initial_values']])}
        self.manifest = {'format': FORMAT, 'source_swf_sha256': source['sha256'], 'parent_frame': 1,
            'base_sprite_id': 11, 'base_files': package_hashes(self.base), 'profiles': {'2': {
                'directory': 'res://generated/forms/fixture-2', 'sprite_id': 22,
                'files': package_hashes(self.target), 'requirement': self.requirements['2'],
                'load_declarations': deepcopy(self.requirements['2']['load_declarations'])}}}
        self.contract = {'nodes': self.nodes}
        self.write_manifest()

    def write_manifest(self):
        path = self.base / 'form_profiles.json'
        path.write_text(json.dumps(self.manifest))
        self.contract['manifest_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()

    def test_complete_source_bound_graph_passes(self):
        validate_form_manifest(self.base, self.contract, self.root)
        hashes = package_hashes(self.base)
        (self.base / 'editor.import').write_text('machine-specific')
        (self.base / 'script.gd.uid').write_text('generated')
        self.assertEqual(package_hashes(self.base), hashes)

    def test_reviewed_target_still_requires_shared_child_effect(self):
        path = self.target / 'ai.json'
        data = json.loads(path.read_text())
        calls = [{'op': 'conditional_frame', 'calls': [
            {'op': 'frame_child_effect', 'clip': 'XG_rush'}]}]
        data['frame_calls']['21'] = calls
        path.write_text(json.dumps(data))
        self.nodes['2']['frames']['21'] = digest(calls)
        self.manifest['profiles']['2']['files'] = package_hashes(self.target)
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, 'DefineSprite_22/frame_21: missing compiled child effect XG_rush'):
            validate_form_manifest(self.base, self.contract, self.root)
        effect = self.root / 'godot/generated/effects/XG_rush/effect.json'
        effect.parent.mkdir(parents=True)
        effect.write_text('{}')
        validate_form_manifest(self.base, self.contract, self.root)

    def test_changed_asset_and_unreviewed_manifest_fail(self):
        (self.target / 'image.png').write_text('changed')
        with self.assertRaisesRegex(ValueError, 'changed/missing form package files'):
            validate_form_manifest(self.base, self.contract, self.root)
        (self.base / 'form_profiles.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'missing/changed reviewed form manifest'):
            validate_form_manifest(self.base, self.contract, self.root)

    def test_missing_and_escaped_target_fail(self):
        self.manifest['profiles']['2']['directory'] = 'res://generated/forms/../../tests/fixture'
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, 'escaped form target'):
            validate_form_manifest(self.base, self.contract, self.root)

    def test_rehashed_load_cannot_change_boolean_to_number(self):
        self.manifest['profiles']['2']['load_declarations'][0]['value'] = 1
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, 'changed source load'):
            validate_form_manifest(self.base, self.contract, self.root)

    def test_rehashed_frame_call_still_requires_source_contract(self):
        path = self.base / 'ai.json'
        data = json.loads(path.read_text())
        data['frame_calls'] = {}
        path.write_text(json.dumps(data))
        self.manifest['base_files'] = package_hashes(self.base)
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, 'changed source-compiled form frame calls'):
            validate_form_manifest(self.base, self.contract, self.root)

    def test_unresolved_transition_is_rejected(self):
        path = self.base / 'ai.json'
        data = json.loads(path.read_text())
        data['frame_calls']['1307'][0]['replacement']['target_parent_frame'] = 3
        path.write_text(json.dumps(data))
        self.manifest['base_files'] = package_hashes(self.base)
        self.nodes['1']['frames']['1307'] = digest(data['frame_calls']['1307'])
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, 'frame_1307: unresolved form target 3'):
            validate_form_manifest(self.base, self.contract, self.root)

    def test_rehashed_asset_reference_cannot_escape_package(self):
        path = self.target / 'assets.json'
        path.write_text(json.dumps({'assets': [{'path': '../unreviewed.png'}]}))
        self.manifest['profiles']['2']['files'] = package_hashes(self.target)
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, 'unpinned form asset'):
            validate_form_manifest(self.base, self.contract, self.root)

    def test_rehashed_missing_body_function_still_fails(self):
        path = self.target / 'player_controller/body.json'
        metadata = json.loads(path.read_text())
        metadata['functions'].remove('doWanKai')
        path.write_text(json.dumps(metadata))
        self.manifest['profiles']['2']['files'] = package_hashes(self.target)
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, 'missing source-bound BODY form functions'):
            validate_form_manifest(self.base, self.contract, self.root)

    def test_frame_guard_rejects_unreviewed_form_events(self):
        timeline = json.loads((self.base / 'timeline.json').read_text())
        cached = json.loads((self.base / 'ai.json').read_text())
        catalog = {'a' * 64 + ':11': {'source': 'fixture.swf', 'frames': self.nodes['1']['frames'],
            'parent_initial_values': {'万解': False}}}
        with self.assertRaisesRegex(ValueError, 'no reviewed replacement graph'):
            validate_cached_frame_calls(timeline, cached, catalog)


if __name__ == '__main__':
    unittest.main()
