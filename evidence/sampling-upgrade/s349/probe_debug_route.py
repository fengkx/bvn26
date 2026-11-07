"""Probe an independent debugger-entry route without launching either movie."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CANDIDATE = Path('/private/tmp/bvn-s283-qualification-r02/candidate.swf')
ORIGINAL = ROOT / 'game/fighter/yihu.swf'
TAGS = {'EnableDebugger': 58, 'DebugID': 63, 'EnableDebugger2': 64}


def scan(path):
    spec = importlib.util.spec_from_file_location('s349_swf', ROOT / 'tools/inspect_swf.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result = module.inspect(path)
    return dict(sha256=result['sha256'], file_bytes=result['file_bytes'],
                swf_version=result['swf_version'],
                debug_tag_counts={name: result['tag_counts'].get(code, 0)
                                  for name, code in TAGS.items()},
                validated_timelines=len(result['timelines']))


def probe():
    receipt = json.loads((HERE.parent / 's283/build-audit.json').read_text())['sha256']
    original = scan(ORIGINAL)
    if original['sha256'] != receipt[str(ORIGINAL)]:
        raise ValueError('original differs from compile receipt')
    candidate = dict(path=str(CANDIDATE), expected_sha256=receipt[str(CANDIDATE)])
    try:
        raw = CANDIDATE.read_bytes()
    except FileNotFoundError:
        candidate.update(status='absent-at-exact-receipt-path', observed_sha256=None,
                         debug_metadata=None)
    else:
        digest = hashlib.sha256(raw).hexdigest()
        candidate.update(status='receipt-match' if digest == candidate['expected_sha256']
                         else 'receipt-mismatch', observed_sha256=digest,
                         debug_metadata=scan(CANDIDATE) if digest == candidate['expected_sha256'] else None)
    return dict(slice='s349', route='unmodified-artifact-debugger-entry',
                hypothesis='Existing debugger metadata could supply a source-breakpoint entry independent of s283Value.',
                original=original, candidate=candidate,
                loaded_body_binding=None, breakpoint_entry=None, invocation_pair=None,
                generation_channel=None, activation_measurements=None, coercion_measurements=None,
                native_observations=[], new_builds=0, new_player_launches=0,
                new_attaches=0, new_memory_reads=0, helper_installed=False,
                conclusion='No independent invocation or generation channel established. '
                           'Tag absence is a disk observation only; candidate absence is local to the receipt path. '
                           'Neither proves that native debugging is impossible. No SWF was changed or launched.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(json.dumps(probe(), indent=2) + '\n')
    print('S349_DEBUG_ROUTE_RECORDED; invocation/generations/erasure unproved')


if __name__ == '__main__':
    main()
