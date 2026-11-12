"""Offline helper-only copy builder; never enters the diagnostic patch pipeline."""
from __future__ import annotations

import difflib
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import zlib

try:
    from .helper_init_observer import configuration, instrument, SITES
except ImportError:
    from helper_init_observer import configuration, instrument, SITES

ROOT = Path(__file__).resolve().parents[2]
ROOT_SITES = {
    "frame_1/DoAction.as": "72c488f6bc45cd94e470e664e771e654869b2b2df3f24c2ed63f90c611dd9614",
    "frame_8/DoAction.as": "75fec07909c55d53217c9b5be24ada24ff02287f17de86cb1f95ae4476cf602b",
}


def flags() -> dict:
    return dict.fromkeys(("production_admitted", "native_parity_proven", "oracle_accepted",
                          "certified_global_tick", "os_input_join_proven", "native_initialization_complete"), False)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def patch(bundle: str, path: str, source: str, run_id: str) -> str:
    if bundle == "main" and path in ROOT_SITES:
        if hashlib.sha256(source.encode()).hexdigest() != ROOT_SITES[path]:
            raise ValueError("Observation logger/Ready source changed")
        if path == "frame_1/DoAction.as":
            # Only observation state is written. No onEnterFrame replacement,
            # timeline jump, key alias, RNG/timer wrapper or auto-quit is installed.
            logger = ('_root.aiSeq = 0;\n_root.aiEvent = function(kind, value)\n{\n'
                      '   trace("AIREF|' + run_id + '|" + (++_root.aiSeq) + "|" + getTimer() + "|-1|-1|" + kind + "|" + value);\n};\n')
            return logger + source
        anchor = 'function startFight()\r\n{\r\n   _root.zhanting = false;\r\n   _root.readying = false;\r\n   _root.setMenuEnable(true);\r\n}'
        if source.count(anchor) != 1:
            raise ValueError("Missing unique startFight source tail")
        return source.replace(anchor, anchor[:-1] + '   _root.aiEvent("ready", "startFight-source-tail");\r\n}')
    return instrument(source, source, bundle, path)


def tag_hashes(path: Path) -> dict:
    raw = path.read_bytes()
    if raw[:3] not in (b"FWS", b"CWS"):
        raise ValueError("Unsupported SWF")
    body = raw[8:] if raw[:3] == b"FWS" else zlib.decompress(raw[8:])
    offset = (5 + 4 * (body[0] >> 3) + 7) // 8 + 4
    result = {"header": hashlib.sha256(raw[3:4] + body[:offset]).hexdigest()}

    def walk(data, owner):
        pos, index, frame = 0, 0, 1
        while pos < len(data):
            header = struct.unpack_from('<H', data, pos)[0]
            pos += 2
            kind, size = header >> 6, header & 63
            if size == 63:
                size = struct.unpack_from('<I', data, pos)[0]
                pos += 4
            payload = data[pos:pos+size]
            pos += size
            if len(payload) != size:
                raise ValueError("Truncated SWF")
            key = f'{owner}/frame{frame}/{index}:{kind}'
            if kind == 39:
                sid, frames = struct.unpack_from('<HH', payload)
                result[key] = [sid, frames]
                walk(payload[4:], f'sprite{sid}')
            else:
                result[key] = hashlib.sha256(payload).hexdigest()
            frame += kind == 1
            index += 1
    walk(body[offset:], 'root')
    return result


def build(ffdec: Path, output: Path, run_id: str, p1_helper: str, p2_helper: str) -> dict:
    config = configuration(p1_helper, p2_helper)
    if not re.fullmatch(r'[A-Za-z0-9_-]+', run_id):
        raise ValueError("Invalid run ID")
    if output.exists():
        raise ValueError("Use a fresh output directory")
    bundles = {name: json.loads((ROOT / f'scripts/{name}.json').read_text())
               for name in ('main', 'fighter/fz/woailuo', 'fighter/fz/kon')}
    patches = {}
    for name, bundle in bundles.items():
        if sha(ROOT / bundle['game_file']) != bundle['swf_sha256']:
            raise ValueError("Locked SWF hash mismatch")
        for row in bundle['scripts']:
            updated = patch(name, row['path'], row['source'], run_id)
            if updated != row['source']:
                patches[(name, row['path'])] = (row['source'], updated)
    expected = set(SITES) | {('main', path) for path in ROOT_SITES}
    if set(patches) != expected:
        raise ValueError("Incomplete observation patch scope")
    # Preserve menu/loader-relative assets and all choices, without assigning
    # selections or changing fighterDir/musicDir to auto-start a fixture.
    shutil.copytree(ROOT / 'game', output / 'game')
    originals = {p.relative_to(ROOT).as_posix(): sha(p) for p in (ROOT / 'game').rglob('*') if p.is_file()}
    changes = []
    for (name, path), (before, after) in patches.items():
        target = output / 'patches' / name / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(after)
        changes.extend(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
                                          fromfile=name+'/'+path, tofile='observer/'+name+'/'+path))
    audits = {}
    for name, bundle in bundles.items():
        original = ROOT / bundle['game_file']
        copied = output / bundle['game_file']
        with (output / (name.replace('/', '-') + '-build.log')).open('w') as log:
            subprocess.run(['java', '-Djava.awt.headless=true', '-jar', str(ffdec), '-importScript',
                            str(original), str(copied), str(output / 'patches' / name)],
                           stdout=log, stderr=subprocess.STDOUT, check=True)
        before, after = tag_hashes(original), tag_hashes(copied)
        changed = sorted(k for k in before.keys() | after.keys() if before.get(k) != after.get(k))
        allowed = ('root/frame1/', 'root/frame8/', 'sprite1900/frame1/') if name == 'main' else ('root/frame1/',)
        if (before.keys() != after.keys() or len(changed) != (3 if name == 'main' else 1)
                or any(not k.endswith(':12') or not k.startswith(allowed) for k in changed)):
            raise ValueError(f'Unexpected compiled tag changes: {name}: {changed}')
        audits[name] = changed
    modified = {bundle['game_file'] for bundle in bundles.values()}
    outputs = {p.relative_to(output).as_posix(): sha(p) for p in (output / 'game').rglob('*') if p.is_file()}
    if outputs.keys() != originals.keys() or any(outputs[k] != v for k, v in originals.items() if k not in modified):
        raise ValueError("Unexpected copied asset change")
    (output / 'instrumentation.diff').write_text(''.join(changes))
    report = {**flags(), 'status': 'built_not_run', 'profile': 'helper-observation', 'run_id': run_id,
              'helper_init_observer': config, 'source_sha256': originals, 'outputs_sha256': outputs,
              'compiler_sha256': sha(ffdec), 'changed_tag_paths': audits,
              'source_sites': [name+'#'+path for name, path in sorted(patches)],
              'instrumentation_sha256': sha(output / 'instrumentation.diff'),
              'auto_start': False, 'key_injection': False, 'body_boundaries': False,
              'diagnostic_trace_hooks': False, 'ready_boundary': 'startFight-source-tail',
              'display_tick': 'unobserved (-1)', 'fight_tick': 'unobserved (-1)',
              'selection_policy': 'physical menu; expected helpers checked by event analyzer, not assigned',
              'noninterference_proven': False}
    (output / 'build.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    return report
