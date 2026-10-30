"""Bounded pass-through instrumentation of the locked s247 Yulong build."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tarfile
import time

from tools.sampling_native import sha

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PREFIX = 'DefineSprite_345/frame_188/PlaceObject2_104_28/'
ENTER = PREFIX + 'CLIPACTIONRECORD onClipEvent(enterFrame).as'


def instrument(source, expected):
    if sha_text(source) != expected:
        raise ValueError('changed source')
    sites = re.findall(r'(hitmc\.mian|mian)\.hitTest\((_root\.game\["p" \+ _parent\.pn\]\.mc\.\w+)\)', source)
    if [r for r, _ in sites] != ['mian', 'mian', 'mian', 'hitmc.mian', 'mian']:
        raise ValueError('changed operand chain')
    result = source
    replacements = []
    for i, (receiver, target) in enumerate(sites, 1):
        old = f'{receiver}.hitTest({target})'
        new = f'_root.s275Value("result{i}", _root.s275Value("receiver{i}", {receiver}).hitTest(_root.s275Value("target{i}", {target})))'
        replacements.append((old, new))
    for old, new in replacements:
        result = result.replace(old, new, 1)
    for site, expression in [('pause', '_root.zhanting == false'), ('played', 'played == 0')]:
        old, new = expression, f'_root.s275Value("{site}", {expression})'
        replacements.append((old, new))
        result = result.replace(old, new, 1)
    old = 'gotoAndPlay(5);'
    new = '_root.s275Boundary("before_goto", this);\n         gotoAndPlay(5);\n         _root.s275Boundary("after_goto", this);'
    replacements.append((old, new))
    result = result.replace(old, new, 1)
    restored = result
    for old, new in reversed(replacements):
        restored = restored.replace(new, old, 1)
    if restored != source or result.count('.hitTest(') != 5:
        raise ValueError('source preservation failure')
    return result


def sha_text(source):
    return hashlib.sha256(source.encode()).hexdigest()


def build(out, ffdec):
    started = time.monotonic()
    out.mkdir(parents=True, exist_ok=False)
    with tarfile.open(HERE.parent / 's247/native-build.tar.gz') as archive:
        archive.extractall(out, members=[m for m in archive.getmembers() if not m.issym()], filter='data')
    (out / 'game/music').symlink_to(ROOT / 'game/music', target_is_directory=True)
    meta = json.loads((out / 'build.json').read_text())
    for name, digest in meta['outputs_sha256'].items():
        if sha(out / name) != digest:
            raise ValueError('locked output mismatch: ' + name)
    for name, digest in meta['sources_sha256'].items():
        if sha(ROOT / name) != digest:
            raise ValueError('locked source mismatch: ' + name)
    scripts = {s['path']: s['source'].replace('\r\n', '\n') for s in json.loads((ROOT / 'scripts/fighter/yulong.json').read_text())['scripts']}
    diagnosis = json.loads((HERE.parent / 's270/diagnosis.json').read_text())
    locked = diagnosis['outer_clip_actions'][ENTER].replace('\r\n', '\n')
    patches = out / 's275-patches'
    diffs = []
    def patch(group, path, before, after):
        dest = patches / group / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(after)
        diffs.extend(difflib.unified_diff(before.splitlines(True), after.splitlines(True), fromfile='s247/' + group + '/' + path, tofile='s275/' + group + '/' + path))
    before = scripts[ENTER]
    patch('fighter/yulong', ENTER, before, instrument(before, sha_text(locked)))
    path = 'DefineSprite_104/frame_5/DoAction.as'
    before = scripts[path]
    if before.strip() != 'this._name = "abcd";':
        raise ValueError('changed rename source')
    patch('fighter/yulong', path, before, '_root.s275Boundary("before_rename", this);\n' + before + '_root.s275Boundary("after_rename", this);\n')
    path = 'frame_1/DoAction.as'
    before = (out / 'patches/main' / path).read_text()
    after = before.replace(meta['run_id'], 's275-yulong-r01')
    # All static loader URLs must point to this extended build, never the old binary.
    old_build = json.loads((HERE.parent / 's247/native-receipt.json').read_text())['build']
    after = after.replace(old_build, str(out))
    patch('main', path, before, (HERE / 'observer.as').read_text() + after)
    path = 'frame_10/DoAction.as'
    before = (out / 'patches/main' / path).read_text()
    after = before.replace(old_build, str(out))
    needle = '_root.aiGeometrySample();'
    if after.count(needle) != 1 or old_build in after:
        raise ValueError('changed root sample boundary')
    after = after.replace(needle, '_root.s275Boundary("root_slot", _root.game.p1.mc.getInstanceAtDepth(-16356));\n' + needle)
    patch('main', path, before, after)
    for group in ('main', 'fighter/yulong'):
        with (out / 's275-build.log').open('a') as log:
            target = out / 'game' / (group + '.swf')
            original = out / (group.replace('/', '-') + '-locked.swf')
            original.write_bytes(target.read_bytes())
            subprocess.run(['java', '-Djava.awt.headless=true', '-jar', str(ffdec), '-importScript', str(original), str(target), str(patches / group)], stdout=log, stderr=subprocess.STDOUT, check=True)
        meta['outputs_sha256']['game/' + group + '.swf'] = sha(target)
    instrumentation = out / 'instrumentation.diff'
    instrumentation.write_text(instrumentation.read_text() + '\n' + ''.join(diffs))
    meta['run_id'] = 's275-yulong-r01'
    meta['instrumentation_sha256'] = sha(instrumentation)
    for path in (Path(__file__), HERE / 'observer.as'):
        meta['sources_sha256'][str(path.relative_to(ROOT))] = sha(path)
    meta['s275_observer'] = {'build_elapsed_seconds': time.monotonic() - started, 'ffdec_sha256': sha(ffdec), 'scope': 'frame188 existing operand/branch evaluations and child/rename/parent slot boundaries, ticks15-22', 'extra_hit_tests': 0, 'semantic_equivalence_proved': False}
    (out / 'build.json').write_text(json.dumps(meta, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(meta['s275_observer']))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--ffdec', type=Path, required=True)
    args = parser.parse_args()
    build(args.output.resolve(), args.ffdec.resolve())
