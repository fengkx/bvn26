"""Bound r25 identity claims without turning ordered paths into native lifetimes."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from urllib.parse import unquote

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
LIVE = HERE.parent / 'native-fight-r25'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


channels = load('r26_channels', LIVE / 'channels.py')
r23 = channels.r23
r21 = r23.r21
r17 = r21.r19.r17
FLAGS = r17.FLAGS


def fields(row):
    return list(map(unquote, row['data'].split(',')))


def classify(raw, tag):
    records, rows = r21.parse(raw, tag)
    targets = r23.target_observations(raw, tag)
    lines = raw.splitlines()
    root_lines = {}
    for number, line in enumerate(lines, 1):
        if line.startswith(('M002|' + tag + '|').encode()):
            root_lines[int(line.split(b'|')[2])] = number
    prefixes = []
    for index, prep in enumerate(rows):
        if prep['kind'] != 'continuation-prep':
            continue
        try:
            query = r17.validate_prefix(rows[max(0, index - 7):index], prep, tag, rows)
            prefixes.append(dict(prep_seq=prep['seq'], raw_line=root_lines[prep['seq']],
                                 helper_path=query[0], serial=query[1], site=query[2],
                                 body_path=query[3], recorded_body_frame=query[4],
                                 source_prefix_valid=True))
        except ValueError as exc:
            prefixes.append(dict(prep_seq=prep['seq'], source_prefix_valid=False, refusal=str(exc)))
    outcomes = []
    for target in targets:
        before = [r for r in rows if root_lines[r['seq']] < target['raw_line']]
        after = [r for r in rows if root_lines[r['seq']] > target['raw_line']]
        installations = []
        for row in before:
            if row['kind'] != 'decision-installed':
                continue
            f = fields(row)
            if len(f) == 2 and f[1].rsplit('/', 1)[0] == target['owner']:
                mentions = [r['seq'] for r in rows if f[1] in fields(r)]
                queries = [r for r in rows if r['kind'] == 'consumer-query-before' and fields(r)[0] == f[1]]
                installations.append(dict(seq=row['seq'], source_marker=f[0], helper_path=f[1],
                                          query_count=len(queries), last_exact_path_root_seq=max(mentions),
                                          termination_observed=False))
        candidates = [p for p in prefixes if p['source_prefix_valid'] and
                      p['body_path'] == target['owner'] and p['raw_line'] < target['raw_line']]
        outcomes.append(dict(target=target, classification='body-target-observed-dispatch-identity-unjoined',
                             preceding_root_seq=before[-1]['seq'] if before else None,
                             following_root_seq=after[0]['seq'] if after else None,
                             source_prefix_candidates=candidates,
                             observed_installation_paths=installations,
                             missing_witnesses=['target has no originating helper or invocation token',
                                                'installation has no parent-definition/depth/generation binding',
                                                'no observed native removal/interrupt edge',
                                                'no observed dispatch entry/exit identity'],
                             initiating_call_join_proven=False, helper_lifetime_proven=False,
                             removal_edge_proven=False, native_return_proven=False, cause='unproved'))
    return dict(**FLAGS, targets=outcomes, source_prefixes=prefixes,
                literal=r21.classify(records, rows, tag),
                sink=r17.classify(rows, tag))


def replay():
    for name, digest in json.loads((HERE / 'input-pins.json').read_text()).items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
            raise ValueError('Pinned input changed: ' + name)
    build = json.loads((LIVE / 'build.json').read_text())
    run = LIVE / 'run-01'
    raw = (run / 'combined.log').read_bytes()
    provenance = load('r26_provenance', LIVE / 'analyze.py')
    provenance.validate_combined_bytes((run / 'flashlog.prelaunch.log').read_bytes(),
                                      (run / 'flashlog.input-baseline.log').read_bytes(),
                                      (run / 'flashlog.after.log').read_bytes(), raw,
                                      (run / 'tagged.log').read_bytes(), build['run_id'])
    channels.validate_build(build)
    report = classify(raw, build['run_id'])
    report.update(run_tag=build['run_id'], new_live=False)
    try:
        r17.history.r05.validate_rows((run / 'tagged.log').read_bytes(), build)
    except ValueError as exc:
        report['structural_refusal'] = str(exc)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--require-oracle', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    report = replay()
    if args.output:
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(report['structural_refusal'])
    print('Body target observed; dispatch identity/lifetime/native return unjoined')
    raise SystemExit(1)
