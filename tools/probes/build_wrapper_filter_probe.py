"""Observe the original Yulong wrapper filter before and after BODY initialization."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from build_parent_goto_probe import ROOT, source_definitions, non_action_tags


def build(output: Path, ffdec: Path) -> None:
    source = ROOT / 'game/fighter/yulong.swf'
    bundle = json.loads((ROOT / 'scripts/fighter/yulong.json').read_text())
    original = next(s['source'] for s in bundle['scripts'] if s['path'] == 'frame_1/DoAction.as')
    observer = '''
var __seq=0;var __tick=0;
function __obs(tag){trace("AIREF|yulong-wrapper-r16|"+(__seq++)+"|0|"+__tick+"|0|state|"+tag+","+mc._currentframe+","+mc.filters.length+","+mc.filters[0].blurX+","+mc.filters[0].blurY);}
__obs("root_initial");
onEnterFrame=function(){__tick++;__obs("initialized");if(__tick==2){delete onEnterFrame;trace("AIREF|yulong-wrapper-r16|"+(__seq++)+"|0|"+__tick+"|0|done|ok");fscommand("quit");}};
'''
    code = '_root.zhanting=true;\n' + original + observer
    output.mkdir(parents=True, exist_ok=False)
    patch = output / 'scripts/frame_1/DoAction.as'
    patch.parent.mkdir(parents=True)
    patch.write_text(code)
    movie = output / 'game/main.swf'
    movie.parent.mkdir()
    subprocess.run(['java', f'-Duser.home={output.resolve()}', '-Djava.awt.headless=true',
                    '-jar', str(ffdec), '-importScript', str(source), str(movie),
                    str(output / 'scripts')], check=True)
    assert source_definitions(source) == source_definitions(movie)
    assert non_action_tags(source) == non_action_tags(movie)
    report = {'run_id': 'yulong-wrapper-r16', 'source': str(source.relative_to(ROOT)),
              'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
              'probe_source_sha256': hashlib.sha256(code.encode()).hexdigest(),
              'ffdec_sha256': hashlib.sha256(ffdec.read_bytes()).hexdigest(),
              'outputs_sha256': {'game/main.swf': hashlib.sha256(movie.read_bytes()).hexdigest()},
              'scope': 'Root observer only; original child definitions and non-action tags unchanged; root pause seeded.'}
    (output / 'build.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--ffdec', type=Path, required=True)
    args = parser.parse_args()
    build(args.output, args.ffdec)
