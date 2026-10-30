"""Build only the Chad post-goto plain-object continuation discriminator."""
import argparse
import difflib
import json
from pathlib import Path
import subprocess
import sys
import time

from tools.probes.build_ai_reference import ROOT
from tools.probes.chad_lifecycle_observer import CALLEE
from tools.sampling_native import sha

HERE = Path(__file__).resolve().parent


def replace_once(source, old, new):
    if source.count(old) != 1:
        raise ValueError('missing unique probe boundary: ' + old)
    return source.replace(old, new)


def patch_callee(source):
    before = '''var s257Witness = {token:"s257-chad-normal-goto",before:1,post:0,observerEntry:0};
var s257Observe = _global.bvnChadObserve;
_global.bvnChadRoot.s257Witness = s257Witness;
s257Observe("s257_control", this, s257Witness);
s257Witness.control = s257Witness.observerEntry;
s257Witness.observerEntry = 0;
'''
    source = replace_once(source, '_global.bvnChadObserve("goto_before", this);',
                          before + '_global.bvnChadObserve("goto_before", this);')
    return replace_once(source, '_global.bvnChadObserve("goto_after", this);',
                        's257Witness.post = 1;\ns257Observe("goto_after", this, s257Witness);')


def patch_root(source):
    needle = '   _global.bvnChadObserve("root_sample", undefined);'
    return replace_once(source, needle, '''   if(aiFight >= 10 && aiFight <= 12)
   {
      var witness = _root.s257Witness;
      aiEvent("s257_witness", typeof(witness) + "," + witness.token + "," + witness.before + "," + witness.control + "," + witness.post + "," + witness.observerEntry);
   }
''' + needle)


def patch_hooks(source):
    return replace_once(source, '_global.bvnChadObserve = function(phase, receiver)\n{',
                        '''_global.bvnChadObserve = function(phase, receiver, s257Witness)
{
   s257Witness.observerEntry = 1;
   if(phase == "s257_control") return;''')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ffdec', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--run-id', required=True)
    args = parser.parse_args()
    started = time.monotonic()
    output = args.output.resolve()
    if output.exists():
        raise ValueError('use a fresh output directory')
    subprocess.run([sys.executable, str(ROOT / 'tools/probes/build_ai_reference.py'),
                    '--ffdec', str(args.ffdec.resolve()), '--output', str(output),
                    '--run-id', args.run_id, '--frames', '60', '--move-case',
                    str(ROOT / 'evidence/sampling-upgrade/s76/chad__attack__neutral__ground__near.json'),
                    '--p1-character', '茶渡', '--p2-character', '一护',
                    '--p1-helper', '我爱罗', '--p2-helper', '魂', '--chad-lifecycle'],
                   check=True, stdout=subprocess.DEVNULL)
    metadata = json.loads((output / 'build.json').read_text())
    diffs = []
    for name, patches in [('main', [('frame_1/DoAction.as', patch_hooks),
                                    ('frame_10/DoAction.as', patch_root)]),
                           ('fighter/chad', [(CALLEE, patch_callee)])]:
        for path, transform in patches:
            patch = output / 'patches' / name / path
            before = patch.read_text()
            after = transform(before)
            patch.write_text(after)
            diffs.extend(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
                                            fromfile='ordinary/' + name + '/' + path,
                                            tofile='s257/' + name + '/' + path))
        with (output / (name.replace('/', '-') + '-s257-build.log')).open('w') as log:
            subprocess.run(['java', '-Djava.awt.headless=true', '-jar', str(args.ffdec.resolve()),
                            '-importScript', str(ROOT / 'game' / (name + '.swf')),
                            str(output / 'game' / (name + '.swf')), str(output / 'patches' / name)],
                           stdout=log, stderr=subprocess.STDOUT, check=True)
        metadata['outputs_sha256']['game/' + name + '.swf'] = sha(output / 'game' / (name + '.swf'))
    instrumentation = output / 'instrumentation.diff'
    instrumentation.write_text(instrumentation.read_text() + ''.join(diffs))
    metadata['instrumentation_sha256'] = sha(instrumentation)
    metadata['sources_sha256'][Path(__file__).relative_to(ROOT).as_posix()] = sha(Path(__file__))
    metadata['s257_observer'] = {'scope': 'Chad normal goto continuation, root ticks 10-12',
                                'build_elapsed_seconds': time.monotonic() - started}
    (output / 'build.json').write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(metadata['s257_observer']))


if __name__ == '__main__':
    main()
