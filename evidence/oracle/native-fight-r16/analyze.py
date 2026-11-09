"""Bound missing source continuation observations without inferring a cause."""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


r15 = load('r16_join', HERE.parent / 'native-fight-r15/consumer_join.py')
r05 = load('r16_structure', HERE.parent / 'native-fight-r05/analyze.py')
r14 = load('r16_builder', HERE.parent / 'native-fight-r14/build_observer.py')


def classify(rows):
    """Add diagnostics to refused intervals; never manufacture a closing marker."""
    joined = r15.join(rows)
    missing = []
    for interval in joined['intervals']:
        markers = interval['markers']
        before = [r for r in markers if r['kind'] == 'consumer-goto-before']
        after = [r for r in markers if r['kind'] == 'consumer-goto-after']
        if not before or after:
            continue
        edge = before[0]
        tail = [r for r in rows if r['seq'] > edge['seq']]
        missing.append(dict(
            classification='goto-before-observed-post-goto-unobserved',
            cause='unproved', key_join_status=interval['key_join_status'],
            query=markers[0], goto_before=edge,
            predicate_prefix=[r for r in rows if markers[0]['seq'] <= r['seq'] <= edge['seq']],
            next_events=tail[:7], later_event_count=len(tail),
            later_counts=dict(Counter(r['kind'] for r in tail)),
            later_installations=[r for r in tail if r['kind'] == 'decision-installed'],
            original_refusal=interval.get('refusal'),
            original_errors=interval['errors'],
            limitation='Later log activity is not continuation, helper removal, native return, or downstream execution proof'))
    return dict(missing_post_goto=missing, validated_count=joined['validated_count'],
                refused_count=joined['refused_count'], interval_count=joined['interval_count'])


def analyze():
    # Pin retained inputs; do not execute historical analyzers that write reports.
    pins = json.loads((HERE / 'input-sha256.json').read_text())
    for path, digest in pins.items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != digest:
            raise ValueError('Pinned input changed: ' + path)
    previous = HERE.parent / 'native-fight-r15'
    build = json.loads((previous / 'build.json').read_text())
    raw = (previous / 'run-01/tagged.log').read_bytes()
    rows = r05.base.parse(raw, build['run_id'])
    result = classify(rows)
    try:
        r05.validate_rows(raw, build)
        result['structural_refusal'] = None
    except ValueError as exc:
        result['structural_refusal'] = str(exc)
    result.update(events=len(rows), replay_only=True, live_performed=False,
                  production_admitted=False, native_parity_proven=False,
                  oracle_accepted=False, certified_global_tick=False,
                  os_input_join_proven=False)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--require-oracle', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        result = analyze()
        rendered = json.dumps(result, indent=2) + '\n'
        if args.output:
            args.output.write_text(rendered)
        print(result['structural_refusal'])
        print('Post-goto cause unproved; full oracle obligations remain unproved')
    except (ValueError, OSError) as exc:
        print('Refused: ' + str(exc))
    raise SystemExit(1)
