"""Build a separate observer copy; retain source diffs and audit every SWF tag."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import zlib

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
JAR_SHA = '090ab695053ad94cba6408574c7d7eea20ec60b6ae789ee6056a23f45106762f'
BOOT = 'frame_1/DoAction.as'
GAME = 'DefineSprite_1991/frame_1/DoAction.as'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tags(path):
    raw = path.read_bytes()
    body = raw[8:] if raw[:3] == b'FWS' else zlib.decompress(raw[8:])
    offset = (5 + 4 * (body[0] >> 3) + 7) // 8 + 4
    result = {'header': hashlib.sha256(body[:offset]).hexdigest()}
    def walk(data, prefix):
        pos = 0
        index = 0
        while pos < len(data):
            header = struct.unpack_from('<H', data, pos)[0]; pos += 2
            kind, size = header >> 6, header & 63
            if size == 63:
                size = struct.unpack_from('<I', data, pos)[0]; pos += 4
            payload = data[pos:pos+size]; pos += size
            if len(payload) != size:
                raise ValueError('Truncated SWF tag')
            key = f'{prefix}/{index}:{kind}'
            if kind == 39:
                sprite, frames = struct.unpack_from('<HH', payload)
                result[key] = f'sprite:{sprite}:frames:{frames}'
                walk(payload[4:], key + f'/sprite{sprite}')
            else:
                result[key] = hashlib.sha256(payload).hexdigest()
            index += 1
    walk(body[offset:], 'root')
    return result


def patch_sources(by_path, run_id):
    if not re.fullmatch(r'[a-z0-9-]{10,80}', run_id):
        raise ValueError('Invalid run tag')
    if any('__m002' in source for source in by_path.values()):
        raise ValueError('Observer namespace collision')
    number = (ROOT / 'tools/probes/as2/ai_reference/number.as').read_text().replace('aiNumber', '__m002Number')
    observer = (HERE / 'observer.as').read_text().replace('__RUN_ID__', run_id)
    game = by_path[GAME]
    entry = 'onEnterFrame = function()\r\n{'
    end = '\r\n};\r\nvar _kn = 0;'
    ready = '_root.ready.play();'
    if any(game.count(marker) != 1 for marker in [entry, end, ready]):
        raise ValueError('Original callback/ready boundary is not unique')
    game = game.replace(entry, entry + '\n_root.__m002Ordinal++;\n_root.__m002Checkpoint("game-entry");', 1)
    game = game.replace(end, '\n_root.__m002Checkpoint("game-exit");\n_root.__m002Phase = "between-game-callbacks";\nif(_root.__m002Ordinal == 900) { _root.__m002Emit("end", "900-local-callbacks"); _root.__m002Ended = true; }' + end, 1)
    game = game.replace(ready, '_root.__m002Emit("ready-play-before", "source-goStep4");\n' + ready, 1)
    return {BOOT: by_path[BOOT] + '\n' + number + observer, GAME: game}


def build(jar, output, run_id):
    if sha(jar) != JAR_SHA:
        raise ValueError('Compiler hash mismatch')
    manifest = json.loads((ROOT / 'manifest.json').read_text())['file_sha256']
    source_hashes = {k:v for k,v in manifest.items() if k.startswith('game/') or k == 'scripts/main.json'}
    for name, digest in source_hashes.items():
        if sha(ROOT / name) != digest:
            raise ValueError('Locked source mismatch: ' + name)
    output.mkdir(parents=True, exist_ok=False)
    shutil.copytree(ROOT / 'game', output / 'game')
    bundle = json.loads((ROOT / 'scripts/main.json').read_text())
    original = {s['path']:s['source'] for s in bundle['scripts']}
    patched = patch_sources(original, run_id)
    diff = []
    for name, source in patched.items():
        target = output / 'patch/scripts' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source)
        diff.extend(difflib.unified_diff(original[name].splitlines(True), source.splitlines(True), fromfile=name, tofile=name+'.observer'))
    (output / 'instrumentation.diff').write_text(''.join(diff))
    command = ['java','-Djava.awt.headless=true','-jar',str(jar),'-importScript',str(ROOT/'game/main.swf'),str(output/'game/main.swf'),str(output/'patch')]
    result = subprocess.run(command,capture_output=True,text=True)
    (output/'compiler.stdout.txt').write_text(result.stdout)
    (output/'compiler.stderr.txt').write_text(result.stderr)
    if result.returncode:
        raise RuntimeError('Compiler failed; logs retained')
    before, after = tags(ROOT/'game/main.swf'), tags(output/'game/main.swf')
    if before.keys() != after.keys():
        raise ValueError('SWF topology changed')
    changed = [k for k in before if before[k] != after[k]]
    if len(changed) != 2 or any(not k.endswith(':12') for k in changed) or not any('/sprite1991/' in k for k in changed):
        raise ValueError('Unexpected tag changes: '+str(changed))
    outputs = {p.relative_to(output).as_posix():sha(p) for p in (output/'game').rglob('*') if p.is_file()}
    for name,digest in outputs.items():
        if name != 'game/main.swf' and digest != manifest[name]:
            raise ValueError('Non-main asset changed')
    report = {'kind':'observe-only-native-copy','run_id':run_id,'compiler_sha256':sha(jar),'command':command,'source_sha256':source_hashes,'outputs_sha256':outputs,'instrumentation_sha256':sha(output/'instrumentation.diff'),'changed_tag_paths':changed,'all_other_tag_payloads_unchanged':True,'source_sites':[BOOT,GAME],'production_admitted':False,'native_parity_proven':False}
    (output/'build.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'run_id':run_id,'changed_tags':changed}))


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ffdec',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--run-id',required=True)
    args=parser.parse_args()
    build(args.ffdec.resolve(),args.output.resolve(),args.run_id)
