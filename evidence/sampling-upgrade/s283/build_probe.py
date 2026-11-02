"""Compile a rejected-or-qualified candidate in a temporary directory; never capture."""
import argparse
import hashlib
import gzip
import json
import re
from pathlib import Path
import subprocess
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BODY = 'DefineSprite_638/frame_1/DoAction.as'


def callback(source):
    start = source.index('function on_enterframe()')
    end = source.index('\nfunction ', start + 1)
    return source[start:end]


def instrument(source):
    original = callback(source)
    candidate = original
    replacements = [
        ('bdmn.hitTest(_root.game["p" + pn].mc.bdmn)',
         '_root.s283Value("result", _root.s283Value("receiver", bdmn, this).hitTest(_root.s283Value("target", _root.game["p" + pn].mc.bdmn, this)), this)'),
        ('if(dashing)', 'if(_root.s283Value("dashing", dashing, this))'),
        ('if(_root.zhanting)', 'if(_root.s283Value("paused", _root.zhanting, this))'),
        ('airBody == false', '_root.s283Value("own_air", airBody == false, this)'),
        ('_root.game["p" + pn].mc.airBody == false', '_root.s283Value("other_air", _root.game["p" + pn].mc.airBody == false, this)'),
        ('_loc3_ >= 0', '_root.s283Value("displacement", _loc3_ >= 0, this)'),
    ]
    # Replace the full opponent expression before its shorter own-air suffix.
    replacements[3], replacements[4] = replacements[4], replacements[3]
    for old, new in replacements:
        if candidate.count(old) != 1:
            # The own expression is also a suffix of the already wrapped opponent.
            if old == 'airBody == false':
                old, new = 'if(airBody == false', 'if(' + new
            else:
                raise ValueError('ambiguous observer replacement: ' + old)
        candidate = candidate.replace(old, new, 1)
    if candidate.count('.hitTest(') != 1:
        raise ValueError('extra hitTest')
    return source.replace(original, candidate, 1)


def function_pcode(source):
    start = source.index('DefineFunction2 "on_enterframe"')
    end = source.index('\n}', start)
    terminal = re.match(r'\n}(?:\n)(loc[0-9a-f]+):', source[end:])
    if terminal is None:
        raise ValueError('missing exported terminal address')
    # FFDec prints the function-end address on the next definition. Retain it.
    return source[start:end] + '\n' + terminal[1] + ':\n}\n'


def build(output, ffdec):
    output.mkdir(parents=True, exist_ok=False)
    source = next(s['source'] for s in json.loads((ROOT / 'scripts/fighter/yihu.json').read_text())['scripts'] if s['path'] == BODY).replace('\r\n', '\n')
    candidate = instrument(source)
    patch = output / 'patches' / BODY
    patch.parent.mkdir(parents=True)
    patch.write_text(candidate)
    commands = []
    base = ['java', '-Duser.home=' + str(output / 'java-home'), '-Djava.awt.headless=true', '-jar', str(ffdec)]
    def run(args):
        started = time.monotonic()
        result = subprocess.run(base + args, capture_output=True, text=True)
        log = output / ('command-' + str(len(commands)) + '.log')
        log.write_text(result.stdout + result.stderr)
        commands.append({'command': base + args, 'exit_code': result.returncode, 'wall_seconds': time.monotonic()-started, 'log_sha256': hashlib.sha256(log.read_bytes()).hexdigest()})
        result.check_returncode()
    run(['-importScript', str(ROOT / 'game/fighter/yihu.swf'), str(output / 'candidate.swf'), str(output / 'patches')])
    for name, swf in [('original', ROOT / 'game/fighter/yihu.swf'), ('candidate', output / 'candidate.swf')]:
        run(['-format', 'script:pcode', '-selectid', '638', '-export', 'script', str(output / name), str(swf)])
        full = (output / name / 'scripts' / BODY.replace('.as', '.pcode')).read_text()
        (HERE / (name + '.frame.pcode.gz')).write_bytes(gzip.compress(full.encode(), mtime=0))
        (HERE / (name + '.pcode')).write_text(function_pcode(full))
    (HERE / 'candidate.as').write_text(callback(candidate) + '\n')
    hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in [ffdec, ROOT / 'game/fighter/yihu.swf', output / 'candidate.swf', patch]}
    (HERE / 'build-audit.json').write_text(json.dumps({'commands':commands, 'sha256':hashes, 'player_launches':0, 'candidate_only':True, 'helper_installed':False, 'capture_ready':False},indent=2)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--ffdec', type=Path, required=True)
    args = parser.parse_args()
    build(args.output.resolve(), args.ffdec.resolve())
