"""Offline-only lexical observer extension; never launches a player."""
import argparse
import difflib
import gzip
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
spec = importlib.util.spec_from_file_location('r03_builder', HERE.parent/'native-fight-r03/build_observer.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
CLOCK = 'DefineSprite_1813/frame_1/DoAction.as'
DECISION = 'DefineSprite_16/frame_1/DoAction.as'


def sources(name):
    return {s['path']: s['source'] for s in json.loads((ROOT/name).read_text())['scripts']}


def patch_fighter(original):
    source = original[DECISION]
    if '__m002' in source:
        raise ValueError('Observer namespace collision')
    sites = []
    function = None
    result = []
    for line_no, line in enumerate(source.splitlines(True), 1):
        match = re.match(r'function (\w+)\(', line)
        if match:
            function = match[1]
        def replace(match):
            site = f'yihu-decision-{len(sites)+1}'
            sites.append(dict(site=site, function=function, line=line_no, argument=match[1], path=DECISION))
            return f'_root.__m002FightKey(_parent,{match[1]},"{site}")'
        result.append(re.sub(r'_parent\.kis\((_parent\.[^()]+)\)', replace, line))
    patched = ''.join(result)
    if len(sites) != 39 or '_parent.kis(' in patched:
        raise ValueError('Fight key inventory changed')
    patched += '\n_root.__m002Emit("decision-installed", "yihu-sprite16," + escape(this._target));\n'
    return patched, sites


def patch_clock(source):
    entry = 'time = function()\r\n{'
    end = '\r\n};\r\nif(_root.maxtime'
    if source.count(entry) != 1 or source.count(end) != 1:
        raise ValueError('Timer boundary changed')
    return source.replace(entry, entry+'\n_root.__m002ClockOrdinal++;\n_root.__m002Clock("entry");', 1).replace(end, '\n_root.__m002Clock("exit");'+end, 1)


def changed_tags(before, after, sprite):
    a, b = base.tags(before), base.tags(after)
    if a.keys() != b.keys():
        raise ValueError('Tag topology changed')
    changed = [k for k in a if a[k] != b[k]]
    if len(changed) != 1 or not changed[0].endswith(f'/sprite{sprite}/1:12'):
        raise ValueError('Unexpected payload changes: '+str(changed))
    return changed


def build(jar, output, run_id):
    temporary_roots = [Path('/tmp').resolve(), Path(tempfile.gettempdir()).resolve()]
    if not any(output.resolve().is_relative_to(root) for root in temporary_roots):
        raise ValueError('Build output must be inside a temporary directory')
    manifest = json.loads((ROOT/'manifest.json').read_text())['file_sha256']
    fighter_json = 'scripts/fighter/yihu.json'
    if base.sha(ROOT/fighter_json) != manifest[fighter_json]:
        raise ValueError('Locked fighter source mismatch')
    # Retain the independently audited r03 stage before extending its copy.
    base.build(jar, output, run_id)
    original = sources('scripts/main.json')
    patched = base.patch_sources(original, run_id)
    patched[base.BOOT] += '\n'+(HERE/'observer.as').read_text()
    patched[CLOCK] = patch_clock(original[CLOCK])
    fighter = sources(fighter_json)
    fighter_patch, sites = patch_fighter(fighter)
    diffs = []
    changes = {}
    for name, source_map, edits, sprite in [
        ('main', original, {base.BOOT: patched[base.BOOT], CLOCK: patched[CLOCK]}, 1813),
        ('fighter/yihu', fighter, {DECISION: fighter_patch}, 16),
    ]:
        patch_dir = output/('extension-'+name.replace('/','-'))
        for path, source in edits.items():
            target = patch_dir/'scripts'/path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(source)
            diffs.extend(difflib.unified_diff(source_map[path].splitlines(True), source.splitlines(True), fromfile=name+'/'+path, tofile=name+'/'+path+'.r05'))
        target = output/'game'/f'{name}.swf'
        before = output/(name.replace('/','-')+'-before.swf')
        before.write_bytes(target.read_bytes())
        command = ['java','-Djava.awt.headless=true','-jar',str(jar),'-importScript',str(before),str(target),str(patch_dir)]
        run = subprocess.run(command, capture_output=True)
        (patch_dir/'stdout.txt').write_bytes(run.stdout)
        (patch_dir/'stderr.txt').write_bytes(run.stderr)
        if run.returncode:
            raise ValueError('Extension compile failed')
        if name == 'main':
            a, b = base.tags(before), base.tags(target)
            delta = [k for k in a if a[k] != b[k]]
            if a.keys() != b.keys() or len(delta)!=2 or 'root/547:12' not in delta or not any(k.endswith('/sprite1813/1:12') for k in delta):
                raise ValueError('Unexpected main extension tag changes')
        else:
            changed_tags(before, target, sprite)
        a, b = base.tags(ROOT/'game'/f'{name}.swf'), base.tags(target)
        if a.keys()!=b.keys():
            raise ValueError('Original tag topology changed')
        changes['game/'+name+'.swf'] = [k for k in a if a[k]!=b[k]]
    outputs = {p.relative_to(output).as_posix():base.sha(p) for p in (output/'game').rglob('*') if p.is_file()}
    for name, digest in outputs.items():
        if name not in changes and digest != manifest[name]:
            raise ValueError('Unexpected asset change: '+name)
    gzip.open(output/'extension.diff.gz','wb').write(''.join(diffs).encode())
    report = json.loads((output/'build.json').read_text())
    report.update(facility='r07', outputs_sha256=outputs, changed_tag_paths_by_asset=changes,
                  fight_sites=sites, source_sites=report['source_sites']+[CLOCK, fighter_json+':'+DECISION],
                  oracle_accepted=False, live_validated=False,
                  facility_sha256={p.name:base.sha(p) for p in [HERE/'build_observer.py',HERE/'observer.as']},
                  extension_diff_sha256=base.sha(output/'extension.diff.gz'))
    report['source_sha256'][fighter_json] = manifest[fighter_json]
    report.pop('changed_tag_paths')
    (output/'build.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(changes))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ffdec', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--run-id', required=True)
    args = parser.parse_args()
    build(args.ffdec.resolve(), args.output.resolve(), args.run_id)
