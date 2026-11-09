"""Describe partial live evidence without relaxing the retained admission gate."""
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import sys
from urllib.parse import unquote

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent / 'native-fight-r03'))
from analyze import parse
from build_observer import tags


def decode(value):
    text = unquote(value)
    if not text.startswith('f:'):
        return text
    _, sign, exponent, high, low = text.split(':')
    significand = (int(high) * 67108864 + int(low)) / 4503599627370496
    return int(sign) * math.ldexp(significand, int(exponent))


def describe():
    directory = HERE / 'run-01'
    session = json.loads((directory / 'session.json').read_text())
    build = json.loads((HERE / 'build.json').read_text())
    if build != session['observer_build']:
        raise ValueError('Build/receipt identity mismatch')
    run_id = build['run_id']
    prefix = ('M002|' + run_id + '|').encode()
    raw = (directory / 'tagged.log').read_bytes()
    pre = (directory / 'flashlog.prelaunch.log').read_bytes()
    baseline = (directory / 'flashlog.input-baseline.log').read_bytes()
    final = (directory / 'flashlog.after.log').read_bytes()
    if prefix in pre or not final.startswith(baseline):
        raise ValueError('Fresh-tag or input-interval append check failed')
    selected = b'\n'.join(line for line in final.splitlines() if line.startswith(prefix)) + b'\n'
    if selected != raw:
        raise ValueError('Tagged/raw log mismatch')
    rows = parse(raw, run_id)
    entries = [r for r in rows if r['kind'] == 'game-state' and r['phase'] == 'game-entry']
    exits = [r for r in rows if r['kind'] == 'game-state' and r['phase'] == 'game-exit']
    expected = list(range(1, len(entries) + 1))
    if [r['ordinal'] for r in entries] != expected or [r['ordinal'] for r in exits] != expected:
        raise ValueError('Callback entry/exit sequence mismatch')
    first = next(r for r in entries if r['data'].split(',')[2:4] == ['false', 'false'])
    fields = ['slot', 'container_x', 'container_y', 'container_xscale', 'body_frame', 'hp', 'ql', 'action', 'beida', 'kcplayed']
    actors = [dict(seq=r['seq'], fields=dict(zip(fields, map(decode, r['data'].split(',')))))
              for r in rows if r['ordinal'] == first['ordinal'] and r['kind'] == 'actor-state' and r['phase'] == 'game-entry']
    randoms = [dict(r, decoded_return=decode(r['data'].split(',', 1)[1]))
               for r in rows if r['kind'] == 'random-return']
    keys = [r for r in rows if r['kind'] == 'key-return']
    pid = session['movie_pid']
    for operation in session['input_operations']:
        if operation['pid'] != pid or not operation['result'].startswith(str(pid) + ', true,'):
            raise ValueError('Input receipt PID mismatch')
    if session['remaining_movie_pids'] or session['asset_recheck'] != 'passed':
        raise ValueError('Cleanup/asset check failed')
    # Recheck the retained original/output byte identities while the temporary build exists.
    movie = Path(session['build']['path']) / 'game/main.swf'
    if hashlib.sha256(movie.read_bytes()).hexdigest() != build['outputs_sha256']['game/main.swf']:
        raise ValueError('Instrumented movie hash mismatch')
    original_tags, observed_tags = tags(ROOT / 'game/main.swf'), tags(movie)
    changed = [k for k in original_tags if original_tags[k] != observed_tags[k]]
    if original_tags.keys() != observed_tags.keys() or changed != build['changed_tag_paths']:
        raise ValueError('Tag audit mismatch')
    report = {
        'kind': 'partial-native-observation-description-not-admission',
        'production_admitted': False, 'native_parity_proven': False, 'oracle_accepted': False,
        'strict_analyzer_exit': 1, 'strict_analyzer_reason': 'State/input/random live observations missing',
        'specific_missing_condition': 'zero positive intro key-return observations; positive fight J is outside the instrumented intro query path',
        'movie_pid': pid, 'run_id': run_id, 'events': len(rows), 'counts': dict(Counter(r['kind'] for r in rows)),
        'local_callback_pairs': len(entries), 'first_observed_unpaused_entry': first,
        'first_observed_unpaused_actors': actors, 'random_returns': randoms,
        'key_queries': len(keys), 'positive_key_queries': sum(r['data'].endswith(',true') for r in keys),
        'key_sites': dict(Counter(r['data'].rsplit(',', 2)[0] for r in keys)),
        'key_ordinal_range': [min(r['ordinal'] for r in keys), max(r['ordinal'] for r in keys)],
        'fresh_tag_and_contiguous_sequence': True, 'raw_tag_selection_verified': True,
        'changed_tag_paths': changed, 'same_pid_returned_for_all_physical_operations': True,
        'capture_seconds': session['completed_unix'] - session['started_unix'],
        'end_marker_present': any(r['kind'] == 'end' for r in rows),
        'limits': ['local ordinal is not global tick', 'first unpaused checkpoint is not proved initial-state boundary',
                   'intro key queries are not fight-path consumption', 'one music draw is not full random tape',
                   'unique-tag filtering is not independent per-write PID attestation or exclusive complete state trace',
                   'no deterministic repeat or same-input instrumented/uninstrumented comparison'],
    }
    (HERE / 'observations.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ['events', 'local_callback_pairs', 'key_queries', 'positive_key_queries', 'capture_seconds']}))


if __name__ == '__main__':
    describe()
