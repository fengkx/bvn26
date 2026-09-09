"""Run unchanged option callback bodies in a separate native Flash copy."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]


def build(output: Path, ffdec: Path) -> None:
    sources = {s['path']: s['source'] for s in json.loads((ROOT/'scripts/main.json').read_text())['scripts']}
    patch = output/'patch'; (output/'game').mkdir(parents=True, exist_ok=False)
    updated = {'frame_7/DoAction.as': sources['frame_7/DoAction.as'] + '\n' + (Path(__file__).parent/'as2/config_reference/probe.as').read_text()}
    for path, source in sources.items():
        if not path.startswith('DefineSprite_836/') or 'onClipEvent(load)' not in path:
            continue
        down = path.replace('onClipEvent(load)', 'onClipEvent(keyDown)')
        if down not in sources:
            continue
        depth = int(path.split('/')[2].split('_')[-1])
        body = sources[down].split('{',1)[1].rsplit('}',1)[0].replace('Key.isDown(', '_root.cfgKey(')
        # Expose the original body for a deterministic function-input oracle;
        # preserve real load/enterFrame/timeline execution in Flash.
        injection = f'\n_root.cfgClips[{depth}] = this;\nthis.cfgDown = function() {{\n{body}\n}};\n'
        updated[path] = source.rsplit('}',1)[0] + injection + '}\n'
    diffs = []
    for path, value in updated.items():
        dest=patch/path; dest.parent.mkdir(parents=True, exist_ok=True); dest.write_text(value)
        diffs.extend(difflib.unified_diff(sources[path].splitlines(True),value.splitlines(True),fromfile=path,tofile=path))
    (output/'instrumentation.diff').write_text(''.join(diffs))
    subprocess.run(['java','-Djava.awt.headless=true','-jar',str(ffdec),'-importScript',str(ROOT/'game/main.swf'),str(output/'game/main.swf'),str(patch)],check=True)
    (output/'build.json').write_text(json.dumps({'run_id':'config-r01','source_sha256':hashlib.sha256((ROOT/'game/main.swf').read_bytes()).hexdigest(),'scope':'native original option callback bodies; explicit row selection; not physical-key dispatch'},indent=2))


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--ffdec',type=Path,required=True);a=p.parse_args();build(a.output,a.ffdec)
