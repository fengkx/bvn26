"""Classify observed lexical breadcrumbs; never admit an oracle or infer silence."""
import argparse
import importlib.util
import json
from pathlib import Path
from urllib.parse import unquote

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('r17_history', HERE.parent / 'native-fight-r16/analyze.py')
history = importlib.util.module_from_spec(spec)
spec.loader.exec_module(history)
FLAGS = {name: False for name in ('production_admitted', 'native_parity_proven', 'oracle_accepted', 'certified_global_tick', 'os_input_join_proven')}


def fields(row):
    return list(map(unquote, row['data'].split(',')))


def validate_prefix(prefix, prep, run_tag, rows):
    expected = ['consumer-query-before'] + ['fight-key-return'] * 4 + ['consumer-predicate-result', 'consumer-goto-before']
    if [r['kind'] for r in prefix] != expected:
        raise ValueError('Missing/interleaved full true predicate prefix')
    if [r['seq'] for r in prefix] != list(range(prep['seq']-7, prep['seq'])):
        raise ValueError('Noncontiguous prefix')
    q, pred, before = fields(prefix[0]), fields(prefix[5]), fields(prefix[6])
    p = fields(prep)
    if len(q) != 6 or q[2] not in ('doStand', 'doAllAction') or not q[1].isdigit() or int(q[1]) < 1 or q[-1] != 'false':
        raise ValueError('Malformed/AI query identity')
    if q[0].rsplit('/', 1)[0] != q[3] or before != q or pred != q[:3] + ['true']:
        raise ValueError('Source identity/result mismatch')
    if p != [run_tag, q[0], q[1], q[2]]:
        raise ValueError('Prep tag/identity mismatch')
    installs = [r for r in rows if r['seq'] < prefix[0]['seq'] and r['kind'] == 'decision-installed' and fields(r) == ['yihu-sprite16', q[0]]]
    queries = [r for r in rows if r['kind'] == 'consumer-query-before' and fields(r)[:3] == q[:3]]
    if len(installs) != 1 or len(queries) != 1:
        raise ValueError('Missing/reused installation or invocation identity')
    for row, site, value in zip(prefix[1:5], range(9, 13), ('true', 'false', 'false', 'false')):
        f = fields(row)
        if len(f) != 10 or f[0] != 'yihu-decision-'+str(site) or f[2] != value or f[3] != q[3] or f[4:7] != ['false']*3:
            raise ValueError('Incomplete/nonmatching native short-circuit returns')
    return q


def classify(rows, run_tag):
    outcomes = []
    claimed = set()
    for i, prep in enumerate(rows):
        if prep['kind'] != 'continuation-prep':
            continue
        result = dict(prep_seq=prep['seq'], classification='prep-without-breadcrumb', cause='unproved', source_continuation_observed=False)
        later = [(j, r) for j, r in enumerate(rows) if j > i and r['kind'] == 'continuation-breadcrumb' and r['data'] == prep['data']]
        try:
            q = validate_prefix(rows[max(0, i-7):i], prep, run_tag, rows)
            if len(later) > 1:
                raise ValueError('Duplicate breadcrumb')
            if later:
                j, crumb = later[0]
                claimed.add(j)
                result['breadcrumb_seq'] = crumb['seq']
                if j != i+1 or crumb['seq'] != prep['seq']+1:
                    raise ValueError('Interleaved breadcrumb')
                result.update(classification='matched', source_continuation_observed=True,
                              dynamic_after='absent-or-unmatched')
                if j+1 < len(rows) and rows[j+1]['kind'] == 'consumer-goto-after':
                    after = rows[j+1]
                    if fields(after)[:4] == q[:4] and len(fields(after)) == 6 and fields(after)[-1] == 'false':
                        result['dynamic_after'] = 'observed-separate-channel'
        except ValueError as exc:
            result.update(classification='interleaved-ambiguous', refusal=str(exc), source_continuation_observed=False)
        outcomes.append(result)
    for i, row in enumerate(rows):
        if row['kind'] == 'continuation-breadcrumb' and i not in claimed:
            outcomes.append(dict(breadcrumb_seq=row['seq'], classification='breadcrumb-without-prep', cause='unproved', source_continuation_observed=False))
    return dict(outcomes=outcomes, **FLAGS)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--require-oracle', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    # Historical replay has no new markers; it cannot validate the prepared observer.
    old = history.analyze()
    previous = HERE.parent / 'native-fight-r15'
    build = json.loads((previous / 'build.json').read_text())
    rows = history.r05.base.parse((previous / 'run-01/tagged.log').read_bytes(), build['run_id'])
    report = dict(classify(rows, build['run_id']), historical_missing_post_goto=old['missing_post_goto'],
                  structural_refusal=old['structural_refusal'], live_validated=False)
    if args.output:
        args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(report['structural_refusal'])
    print('No r17 live breadcrumb evidence; admission refused')
    raise SystemExit(1)
