"""Controlled s240 exit-delay check; hold quit until the next observer callback."""
import argparse
import difflib
import json
from pathlib import Path
import subprocess
import sys

from tools.probes.build_ai_reference import ROOT
from tools.probes.probe_reference_helpers import sha

TERMINAL = '      _root.aiYulongDisplayComplete = true;\n      fscommand("quit");'
CLOSURE = '      _root.aiEvent = function() {};\n      return;'


def defer_quit(source):
    if source.count(TERMINAL) != 1 or source.count(CLOSURE) != 1:
        raise ValueError('missing unique terminal/closure sites')
    return source.replace(TERMINAL, '      _root.aiYulongDisplayComplete = true;', 1).replace(
        CLOSURE, '      _root.aiEvent = function() {};\n      fscommand("quit");\n      return;', 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ffdec', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--run-id', required=True)
    args = parser.parse_args()
    output = args.output.resolve(); ffdec = args.ffdec.resolve()
    case = ROOT / 'evidence/sampling-upgrade/s240/yulong__attack__neutral__ground__near.json'
    subprocess.run([sys.executable, str(ROOT / 'tools/probes/build_ai_reference.py'),
                    '--ffdec', str(ffdec), '--output', str(output), '--run-id', args.run_id,
                    '--frames', '60', '--move-case', str(case), '--p1-character', '石田',
                    '--p2-character', '一护', '--p1-helper', '我爱罗', '--p2-helper', '魂',
                    '--yulong-display-completion'], check=True, stdout=subprocess.DEVNULL)
    metadata = json.loads((output / 'build.json').read_text())
    patch = output / 'patches/main/frame_10/DoAction.as'
    before = patch.read_text(); after = defer_quit(before); patch.write_text(after)
    diff = ''.join(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
                                      fromfile='normal-exit/main/frame_10/DoAction.as',
                                      tofile='held-exit/main/frame_10/DoAction.as'))
    with (output / 'held-exit-build.log').open('w') as log:
        subprocess.run(['java', '-Djava.awt.headless=true', '-jar', str(ffdec),
                        '-importScript', str(ROOT / 'game/main.swf'),
                        str(output / 'game/main.swf'), str(output / 'patches/main')],
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    instrumentation = output / 'instrumentation.diff'
    instrumentation.write_text(instrumentation.read_text() + diff)
    metadata['instrumentation_sha256'] = sha(instrumentation)
    metadata['outputs_sha256']['game/main.swf'] = sha(output / 'game/main.swf')
    metadata['sources_sha256']['tools/probes/build_yulong_display_hold.py'] = sha(Path(__file__))
    metadata['exit_delay_control'] = 'quit requested at next root callback after closing observation window'
    (output / 'build.json').write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({'output': str(output), 'exit_delay_control': metadata['exit_delay_control']}))


if __name__ == '__main__':
    main()
