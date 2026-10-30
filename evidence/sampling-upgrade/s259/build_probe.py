"""Opt-in s232 geometry completion experiment, with a declared held-quit control."""
import argparse
import difflib
import json
from pathlib import Path
import subprocess
import sys

from tools.probes.build_ai_reference import ROOT
from tools.probes.probe_reference_helpers import sha
from tools.probes.yulong_display_completion import instrument

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
    parser.add_argument('--hold-quit', action='store_true')
    args = parser.parse_args()
    output = args.output.resolve(); ffdec = args.ffdec.resolve()
    if output.exists():
        raise ValueError('use a fresh output directory')
    case = ROOT / 'evidence/sampling-upgrade/s232/yijiao__attack__neutral__ground__near.json'
    subprocess.run([sys.executable, str(ROOT / 'tools/probes/build_ai_reference.py'),
                    '--ffdec', str(ffdec), '--output', str(output), '--run-id', args.run_id,
                    '--frames', '60', '--move-case', str(case), '--p1-character', '一角',
                    '--p2-character', '一护', '--p1-helper', '我爱罗', '--p2-helper', '魂',
                    '--sampling-geometry'], check=True, stdout=subprocess.DEVNULL)
    metadata = json.loads((output / 'build.json').read_text())
    patch = output / 'patches/main/frame_10/DoAction.as'
    before = patch.read_text()
    after = instrument(before)
    if args.hold_quit:
        after = defer_quit(after)
    patch.write_text(after)
    diff = ''.join(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
                                      fromfile='ordinary-geometry/main/frame_10/DoAction.as',
                                      tofile='s259-geometry/main/frame_10/DoAction.as'))
    with (output / 'held-exit-build.log').open('w') as log:
        subprocess.run(['java', '-Djava.awt.headless=true', '-jar', str(ffdec),
                        '-importScript', str(ROOT / 'game/main.swf'),
                        str(output / 'game/main.swf'), str(output / 'patches/main')],
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    instrumentation = output / 'instrumentation.diff'
    instrumentation.write_text(instrumentation.read_text() + diff)
    metadata['instrumentation_sha256'] = sha(instrumentation)
    metadata['outputs_sha256']['game/main.swf'] = sha(output / 'game/main.swf')
    metadata['sources_sha256']['evidence/sampling-upgrade/s259/build_probe.py'] = sha(Path(__file__))
    metadata['geometry_completion_window'] = 's259 opt-in exact s232 case only'
    metadata['exit_delay_control'] = ('quit requested at next root callback after closing observation window'
                                      if args.hold_quit else 'ordinary quit at done')
    (output / 'build.json').write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({'output': str(output), 'exit_delay_control': metadata['exit_delay_control']}))


if __name__ == '__main__':
    main()
