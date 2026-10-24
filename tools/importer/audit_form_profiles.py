"""Recompile source contracts before admitting a native replacement graph."""
import hashlib
from pathlib import Path

from compile_ai_context import compile_context
from compile_ai_controller import compile_controller
from compile_ai_predicates import compile_source, controller_script
from parent_form_requirements import parent_form_requirement
from form_profile_guard import ROOT, digest, inspect_form_manifest, validate_form_manifest


def audit_form_manifest(directory: Path, bundle: dict, root: Path = ROOT) -> dict:
    from compile_ai_body import compile_player_body
    manifest, nodes = inspect_form_manifest(directory, root)
    if manifest['source_swf_sha256'] != bundle['swf_sha256']:
        raise ValueError(f'{directory}: form manifest source SWF mismatch')
    contract = {'manifest_sha256': hashlib.sha256((directory / 'form_profiles.json').read_bytes()).hexdigest(),
                'nodes': {}}
    for frame, node in nodes.items():
        target = node['directory']
        sprite = node['sprite_id']
        requirement = parent_form_requirement(bundle, int(frame), str(target))
        if requirement['target_body_sprite'] != sprite:
            raise ValueError(f'{target}: source parent frame {frame} places another body')
        compiled = compile_context(bundle, node['timeline'], form_replacement=True)
        if digest(compiled) != digest(node['context']):
            raise ValueError(f'{target}: cached form AI differs from freshly compiled source')
        body, body_metadata = compile_player_body(bundle, sprite, node['timeline'], form_helpers=True)
        controller, controller_metadata = compile_controller(bundle, sprite, node['timeline'], player=True, form_replacement=True)
        controller_metadata['input_mode'] = 'player'
        predicates = compile_source(controller_script(bundle, sprite)['source'], player=True)
        for name, expected in (('body.gd', body), ('controller.gd', controller), ('predicates.gd', predicates)):
            if (target / 'player_controller' / name).read_text() != expected:
                raise ValueError(f'{target}: {name} differs from freshly compiled source')
        from form_profile_guard import read_json
        for name, expected in (('body.json', body_metadata), ('controller.json', controller_metadata)):
            if digest(read_json(target / 'player_controller' / name)) != digest(expected):
                raise ValueError(f'{target}: {name} differs from freshly compiled source')
        contract['nodes'][frame] = {'sprite_id': sprite, 'requirement': requirement,
                                  'frames': {key: digest(value) for key, value in compiled['frame_calls'].items()},
                                  'nested_stage_frames': compiled.get('nested_stage_frames', {}),
                                  'parent_initial_values_digest': digest([compiled.get('parent_initial_values', {})])}
    validate_form_manifest(directory, contract, root)
    return contract
