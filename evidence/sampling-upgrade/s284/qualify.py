"""Qualify only the source-preserving s228 completion-window build."""
import difflib
import hashlib
import json
from pathlib import Path
import tarfile

from tools.sampling_doaction import check_inventory

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def qualify(build, held, recorded_build=None):
    old_dir = HERE.parent / 's228'
    old = json.loads((old_dir / 'native-build.json').read_text())
    meta = json.loads((build / 'build.json').read_text())
    for key in ('configuration', 'move_case', 'frames_after_ready', 'doaction_inventory',
                'sampling_doaction', 'sampling_display', 'sampling_geometry',
                'sampling_bitmap', 'sampling_clipaction', 'sampling_callsite'):
        if meta[key] != old[key]:
            raise ValueError('changed configuration: ' + key)
    check_inventory(meta)
    for name, expected in meta['sources_sha256'].items():
        if sha((ROOT / name).read_bytes()) != expected:
            raise ValueError('changed source: ' + name)
    for name, expected in meta['outputs_sha256'].items():
        if sha((build / name).read_bytes()) != expected:
            raise ValueError('changed output: ' + name)
        if name != 'game/main.swf' and expected != old['outputs_sha256'][name]:
            raise ValueError('changed fighter/helper binary: ' + name)
    diff = (build / 'instrumentation.diff').read_text()
    if sha((build / 'instrumentation.diff').read_bytes()) != meta['instrumentation_sha256']:
        raise ValueError('changed instrumentation')
    with tarfile.open(old_dir / 'native-build.tar.gz') as archive:
        previous = archive.extractfile('instrumentation.diff').read().decode().replace('\r\n', '\n')
    previous = previous.replace('/private/tmp/bvn-s228-build', str(recorded_build or build)).replace(old['run_id'], meta['run_id'])
    baseline, delta = diff.split('--- ordinary-doaction/', 1)
    if baseline != previous:
        raise ValueError('ordinary instrumentation drift')
    candidate = (build / 'patches/main/frame_10/DoAction.as').read_text()
    from tools.probes.yulong_display_completion import FLAG, HEADER, GUARD, DONE, ARM
    rename = lambda text: text.replace('aiYulongDisplayComplete', 'aiS284DoActionComplete')
    guard = rename(GUARD)
    if held:
        guard = guard.replace('      return;', '      fscommand("quit");\n      return;')
    marker = rename(FLAG) + HEADER + guard
    terminal = DONE + rename(ARM) + ('' if held else '\n      fscommand("quit");')
    if candidate.count(marker) != 1 or candidate.count(terminal) != 1:
        raise ValueError('changed closure/terminal placement')
    restored = candidate.replace(marker, HEADER, 1).replace(terminal, DONE + '\n      fscommand("quit");', 1)
    root_diff = baseline.split('--- main/frame_10/DoAction.as\n', 1)[1].split('\n--- ', 1)[0]
    archived_root = ''.join(line[1:] + '\n' for line in root_diff.splitlines()
                            if line.startswith('+') and not line.startswith('+++'))
    if restored != archived_root:
        raise ValueError('candidate does not erase to the archived root source')
    expected = ''.join(difflib.unified_diff(restored.splitlines(True), candidate.splitlines(True),
        fromfile='ordinary-doaction/main/frame_10/DoAction.as', tofile='s284-doaction/main/frame_10/DoAction.as'))
    if expected != '--- ordinary-doaction/' + delta:
        raise ValueError('non-window change in candidate')
    return {'source_preserving_build_qualified': True, 'mode': 'held' if held else 'normal',
            'ordinary_diff_equal_after_run_id_and_build_path_substitution': True,
            'fighter_helper_binaries_unchanged': True, 'inventory_unchanged': True,
            'guard_before_clock_input_and_sample': True,
            'scope': 'source/inventory/binary qualification; no native parity or callback completeness claim',
            'production_admitted': False, 'native_parity_proven': False}
