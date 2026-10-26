"""Recompile and validate a complete form graph before writing its activation.

This proves source compilation and dependency closure, not native parity. Only
activate graphs whose runtime/native acceptance has been separately reviewed.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import tempfile

from audit_form_profiles import audit_form_manifest
from build_form_profile import compile_programs, write
from form_profile_guard import FORMAT, ROOT, package_hashes, read_json
from parent_form_requirements import parent_form_requirement
from placement_build_guard import validate_build_placements
from visual_control_guard import validate_build_controls
from visual_blend_modes import validate_timeline_blends


def publish_programs(staged: dict[int, Path], directories: dict[int, Path]) -> None:
    """Prepare every write first and restore installed bytes on publication errors.

    Per-file replacements are atomic; this is not a cross-directory crash
    transaction. The reviewed build catalog still rejects an interrupted graph.
    """
    writes = []
    for frame, directory in directories.items():
        source = staged[frame]
        files = [source / 'ai.json']
        for name in ('ai_controller', 'player_controller'):
            files.extend(path for path in sorted((source / name).rglob('*')) if path.is_file())
        writes.extend((path, directory / path.relative_to(source)) for path in files)
    writes.append((staged[1] / 'form_profiles.json', directories[1] / 'form_profiles.json'))
    prepared = []
    replaced = []
    temporary = []
    created_directories = []
    preserve_recovery = False
    published = False
    try:
        for source, destination in writes:
            missing = []
            parent = destination.parent
            while not parent.exists():
                missing.append(parent)
                parent = parent.parent
            for parent in reversed(missing):
                parent.mkdir()
                created_directories.append(parent)
            # Use the destination filesystem so replacement cannot fail EXDEV.
            with tempfile.NamedTemporaryFile(dir=destination.parent, prefix='.form-new-', delete=False) as handle:
                pending = Path(handle.name)
            temporary.append(pending)
            shutil.copyfile(source, pending)
            backup = None
            if destination.exists():
                with tempfile.NamedTemporaryFile(dir=destination.parent, prefix='.form-old-', delete=False) as handle:
                    backup = Path(handle.name)
                temporary.append(backup)
                shutil.copyfile(destination, backup)
            prepared.append((pending, destination, backup))
        for pending, destination, backup in prepared:
            os.replace(pending, destination)
            replaced.append((destination, backup))
        published = True
    except BaseException:
        try:
            for destination, backup in reversed(replaced):
                if backup is None:
                    destination.unlink()
                else:
                    os.replace(backup, destination)
        except OSError as error:
            preserve_recovery = True
            raise RuntimeError(f'Form publication rollback failed; preserve recovery files: {temporary}') from error
        raise
    finally:
        if not preserve_recovery:
            for path in temporary:
                path.unlink(missing_ok=True)
            if not published:
                for directory in reversed(created_directories):
                    directory.rmdir()


def prepare(base: Path, targets: dict[int, Path], *, write_outputs: bool = False,
            root: Path = ROOT) -> dict:
    root = root.resolve()
    base = base.resolve()
    if base.parent != root / 'godot/generated/fighters' or not targets:
        raise ValueError('A shipped base fighter and a nonempty target graph are required')
    targets = {frame: path.resolve() for frame, path in targets.items()}
    for frame, path in targets.items():
        if frame <= 1 or path.parent != root / 'godot/generated/forms':
            raise ValueError(f'Invalid parent frame/production target: {frame}: {path}')
    timeline = read_json(base / 'timeline.json')
    source = timeline['source_swf']['path']
    bundle = read_json(root / source.replace('game/', 'scripts/', 1).replace('.swf', '.json'))
    with tempfile.TemporaryDirectory(prefix='bvn-form-graph-') as scratch:
        staged_root = Path(scratch)
        effects = root / 'godot/generated/effects'
        if effects.is_dir():
            shutil.copytree(effects, staged_root / 'godot/generated/effects',
                            ignore=shutil.ignore_patterns('*.uid', '*.import', '.*'))
        directories = {1: base, **targets}
        staged = {}
        for frame, directory in directories.items():
            destination = staged_root / directory.relative_to(root)
            # Stage the entire graph: a later compile failure must not leave
            # half-refreshed programs behind an old activation manifest.
            shutil.copytree(directory, destination,
                            ignore=shutil.ignore_patterns('*.uid', '*.import', '.*'))
            compile_programs(destination, bundle, read_json(destination / 'timeline.json'))
            compiled_timeline = read_json(destination / 'timeline.json')
            for validate in (validate_timeline_blends, validate_build_controls, validate_build_placements):
                validate(compiled_timeline, str(directory / 'timeline.json'))
            staged[frame] = destination
        manifest = {'format': FORMAT, 'source_swf_sha256': bundle['swf_sha256'],
                    'parent_frame': 1, 'base_sprite_id': timeline['sprite_id'],
                    'base_files': package_hashes(staged[1]), 'profiles': {}}
        for frame, directory in targets.items():
            requirement = parent_form_requirement(bundle, frame, source)
            manifest['profiles'][str(frame)] = {
                'directory': 'res://' + directory.relative_to(root / 'godot').as_posix(),
                'sprite_id': read_json(staged[frame] / 'timeline.json')['sprite_id'],
                'requirement': requirement, 'load_declarations': requirement['load_declarations'],
                'files': package_hashes(staged[frame])}
        write(staged[1] / 'form_profiles.json', manifest)
        contract = audit_form_manifest(staged[1], bundle, root=staged_root)
        if write_outputs:
            # Publish the activation last; the build still needs its reviewed
            # frame-call catalog updated by the explicit source-audit command.
            publish_programs(staged, directories)
        return {'source': source, 'written': write_outputs, 'contract': contract}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, required=True)
    parser.add_argument('--target', action='append', required=True, metavar='FRAME=DIRECTORY')
    parser.add_argument('--write', action='store_true')
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    targets = {}
    for item in args.target:
        frame, path = item.split('=', 1)
        frame = int(frame)
        if frame in targets:
            parser.error(f'duplicate parent frame {frame}')
        targets[frame] = Path(path)
    result = prepare(args.base, targets, write_outputs=args.write)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    write(args.report, result)
    print(json.dumps({'source': result['source'], 'written': result['written'],
                      'nodes': len(result['contract']['nodes'])}))


if __name__ == '__main__':
    main()
