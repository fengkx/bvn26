"""Bound archived terminal callback source; never infer returns from log silence."""
import argparse
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tarfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
LOCKED = HERE.parent / 's293'
SOURCE = 'patches/main/frame_10/DoAction.as'
GATES = {
    'callback-completion': 'S304_CALLBACK_COMPLETION_UNPROVED',
    'terminal-completeness': 'S304_TERMINAL_CALLBACK_COMPLETENESS_UNPROVED',
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def source_bounds(source):
    lines = source.splitlines()
    def line(text):
        matches = [i + 1 for i, value in enumerate(lines) if value.strip() == text]
        if len(matches) != 1:
            raise ValueError('S304_SOURCE_BOUNDARY_AMBIGUOUS: ' + text)
        return matches[0]
    points = {name: line(text) for name, text in {
        'assignment': 'onEnterFrame = function()',
        'guard': 'if(_root.aiS284DoActionComplete)',
        'closure_marker': 'aiEvent("capture_window_closed", "before-next-root-increment");',
        'replace_callback': '_root.onEnterFrame = function() {};',
        'disable_logger': '_root.aiEvent = function() {};',
        'explicit_return': 'return;',
        'clock_increment': 'aiDisplay++;',
        'done_marker': 'aiEvent("done", "");',
        'arm_guard': '_root.aiS284DoActionComplete = true;',
        'timeout_guard': 'if(aiDisplay > 60 + 900)',
    }.items()}
    quits = [i + 1 for i, value in enumerate(lines) if value.strip() == 'fscommand("quit");']
    if len(quits) != 2 or list(points.values()) != sorted(points.values()):
        raise ValueError('S304_SOURCE_ORDER_INVALID')
    if not points['disable_logger'] < quits[0] < points['explicit_return']:
        raise ValueError('S304_CLOSURE_ORDER_INVALID')
    if lines[-1] != '};' or quits[1] <= points['timeout_guard']:
        raise ValueError('S304_CALLBACK_END_INVALID')
    return {'archive_member': SOURCE, 'sha256': sha(source.encode()),
            'lines': points, 'quit_lines': quits, 'fallthrough_end_line': len(lines),
            'source': source,
            'owner': 'root onEnterFrame property assigned by root frame_10 DoAction',
            'entry': 'function body before completion guard; no entry marker',
            'exits': ['guard branch: quit request then explicit return if execution resumes',
                      'ordinary branch: implicit fallthrough after timeout conditional',
                      'timeout branch: quit request before possible fallthrough'],
            'closure_owner': 'next root callback invocation, not the done-emitting invocation',
            'live_activation_identity': None, 'observed_return': None}


def suffix(trace):
    rows = []
    for raw in trace.decode().splitlines():
        fields = raw.split('|', 7)
        if len(fields) != 8 or fields[0] != 'AIREF':
            raise ValueError('S304_EVENT_INVALID')
        rows.append(dict(run_id=fields[1], sequence=int(fields[2]), time_ms=int(fields[3]),
                         display=int(fields[4]), tick=int(fields[5]), kind=fields[6], payload=fields[7]))
    done = [i for i, row in enumerate(rows) if row['kind'] == 'done']
    if len(done) != 1:
        raise ValueError('S304_DONE_AMBIGUOUS')
    if [r['sequence'] for r in rows] != list(range(1, len(rows) + 1)):
        raise ValueError('S304_EVENT_ORDER_INVALID')
    tail = rows[done[0] + 1:]
    return {'done': rows[done[0]], 'suffix': tail, 'events': len(rows),
            'suffix_kind_counts': {kind: sum(r['kind'] == kind for r in tail)
                                   for kind in sorted({r['kind'] for r in tail})},
            'suffix_clock_pairs': [list(pair) for pair in sorted({(r['display'], r['tick']) for r in tail})],
            'completion_witness': None}


def diagnose():
    for name, expected in json.loads((HERE / 'input-sha256.json').read_text()).items():
        if sha((ROOT / name).read_bytes()) != expected:
            raise ValueError('S304_LOCKED_INPUT_CHANGED: ' + name)
    spec = importlib.util.spec_from_file_location('s293_locked', LOCKED / 'diagnose.py')
    retained = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(retained)
    historical = retained.diagnose()
    if historical != json.loads((LOCKED / 'diagnosis.json').read_text()):
        raise ValueError('S304_LOCKED_S293_DRIFT')
    with tarfile.open(LOCKED / 'held/native-build.tar.gz') as archive:
        source = archive.extractfile(SOURCE).read().decode()
    runs = {mode: suffix(gzip.decompress((LOCKED / mode / 'native-capture.log.gz').read_bytes()))
            for mode in ('normal', 'held')}
    return {'scope': 'AFTER-s299 rank #5 only', 'production_admitted': False,
            'native_parity_proven': False, 'locked_s293_diagnosis_equal': True,
            'independent_pair_proved_and_closed': historical['independent_pair_proved'],
            'source_callback': source_bounds(source), 'runs': runs,
            'ownership_limit': 'key_read carries receiver text, key and value, not caller, closure generation, activation ID or return; no suffix row is assigned to a gameplay callback',
            'missing_independent_witness': [
                'Qualified observer independent of aiEvent binds root callback entry to exact loaded body, owner generation and activation ID.',
                'Same activation is observed returning to its dispatcher (or explicit unwind/termination classified separately), after done and after the closure marker; property replacement is not a return.',
                'For every-callback completeness additionally enumerate pending/dispatched terminal callbacks with owner generations and matched exits, including callbacks without key reads; qualify observer-off/on preservation before capture.'],
            'gates': {name: {'proved': False, 'code': code} for name, code in GATES.items()},
            'new_builds': 0, 'new_player_launches': 0, 'new_captures': 0,
            'other_ranks_executed': False, 'fixed_suffix_threshold': None,
            'full_as_proven': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    for name in GATES:
        parser.add_argument('--require-' + name, action='store_true')
    args = parser.parse_args()
    try:
        report = diagnose()
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    except (ValueError, KeyError, OSError, TypeError) as error:
        print('S304_EVIDENCE_INVALID: ' + str(error), file=sys.stderr)
        return 1
    for name, code in GATES.items():
        if getattr(args, 'require_' + name.replace('-', '_')):
            print(code, file=sys.stderr)
            return 1
    print('S304_DIAGNOSIS_OK production_admitted=false native_parity_proven=false')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
