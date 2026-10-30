"""Extend s260 with observations of authored query calls; no artificial calls."""
import argparse
import difflib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time

from tools.sampling_native import sha

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RECEIVER = 'DefineSprite_2/frame_1/DoAction.as'


def base_module():
    spec = importlib.util.spec_from_file_location('s260_builder', HERE.parent / 's260/build_probe.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def patch_receiver(source):
    replace = base_module().replace_once
    for signature, phase, arguments in (
        ('function beida()', 'beida_entry', 'undefined,undefined,undefined,undefined'),
        ('function checkHit()', 'checkHit_entry', 'undefined,undefined,undefined,undefined'),
        ('function getHitObj(array, player, afterFix, ppw)', 'getHitObj_entry', 'array,player,afterFix,undefined'),
        ('function getStgHitObj()', 'getStgHitObj_entry', 'stgks,_root.game.layer_effect,undefined,undefined'),
    ):
        needle = signature + '\n{'
        source = replace(source, needle, needle + '\n   _root.s264Query("' + phase + '",this,' + arguments + ');')
    # Both authored consumers keep the original evaluation and result unchanged.
    needle = '   var _loc2_ = checkHit();'
    if source.count(needle) != 2:
        raise ValueError('expected beida/fangyu consumers')
    source = source.replace(needle, needle + '\n   _root.s264Query("checkHit_result",this,undefined,undefined,undefined,_loc2_);')
    for operand, phase in (('_loc4_', 'fighter_helper_operand'), ('_loc4_.mian', 'stage_operand')):
        needle = '         if(this.hitTest(' + operand + '))'
        source = replace(source, needle, '         _root.s264Query("' + phase + '",this,undefined,' + operand + ',undefined,undefined);\n' + needle)
    return source


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ffdec', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--run-id', required=True)
    args = parser.parse_args()
    started = time.monotonic()
    output = args.output.resolve()
    subprocess.run([sys.executable, str(HERE.parent / 's260/build_probe.py'), '--ffdec', str(args.ffdec.resolve()), '--output', str(output), '--run-id', args.run_id], check=True)
    metadata = json.loads((output / 'build.json').read_text())
    diff = []
    for name, path in [('main', 'frame_1/DoAction.as'), ('fighter/didala', RECEIVER)]:
        patch = output / 'patches' / name / path
        before = patch.read_text()
        after = (HERE / 'observer.as').read_text() + '\n' + before if name == 'main' else patch_receiver(before)
        patch.write_text(after)
        diff.extend(difflib.unified_diff(before.splitlines(True), after.splitlines(True), fromfile='s260/' + name + '/' + path, tofile='s264/' + name + '/' + path))
        with (output / (name.replace('/', '-') + '-s264-build.log')).open('w') as log:
            subprocess.run(['java', '-Djava.awt.headless=true', '-jar', str(args.ffdec.resolve()), '-importScript', str(ROOT / 'game' / (name + '.swf')), str(output / 'game' / (name + '.swf')), str(output / 'patches' / name)], stdout=log, stderr=subprocess.STDOUT, check=True)
        metadata['outputs_sha256']['game/' + name + '.swf'] = sha(output / 'game' / (name + '.swf'))
    instrumentation = output / 'instrumentation.diff'
    instrumentation.write_text(instrumentation.read_text() + ''.join(diff))
    metadata['instrumentation_sha256'] = sha(instrumentation)
    for path in (Path(__file__), HERE / 'observer.as'):
        metadata['sources_sha256'][path.relative_to(ROOT).as_posix()] = sha(path)
    metadata['s264_observer'] = {'scope': 'P1 bdmn authored query entries/results/operands at ticks10-12', 'build_elapsed_seconds': time.monotonic() - started}
    (output / 'build.json').write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(metadata['s264_observer']))


if __name__ == '__main__':
    main()
