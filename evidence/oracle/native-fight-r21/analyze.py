"""Classify a literal continuation channel without proving lifetime or admission."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
spec=importlib.util.spec_from_file_location('r21_parent_analysis',HERE.parent/'native-fight-r19/analyze.py')
r19=importlib.util.module_from_spec(spec);spec.loader.exec_module(r19)


def parse(raw,tag):
    records,rows=r19.parse_combined(raw,tag)
    for record in records:
        if record['kind']=='unclassified' and record['data'].startswith('M002LITERAL|'):
            f=record['data'].split('|')
            if len(f)!=4 or f[1]!=tag or f[2] not in ('doStand','doAllAction') or f[3] not in ('before','after'):
                raise ValueError('Foreign/malformed literal channel')
            record.update(kind='literal',tag=f[1],site=f[2],phase=f[3])
    return records,rows


def classify(records,rows,tag):
    outcomes=[];claimed=set()
    for i,before in enumerate(records):
        if before['kind']!='literal' or before['phase']!='before':continue
        result=dict(classification='literal-before-without-after',cause='unproved',source_continuation_observed=False)
        try:
            if i<2 or records[i-1]['kind']!='direct' or records[i-1]['phase']!='before' or records[i-2]['kind']!='continuation-prep':
                raise ValueError('Missing adjacent prep/direct bridge')
            prep,side=records[i-2:i]
            if side['data']!=prep['data']:raise ValueError('Bridge identity mismatch')
            pos=next(j for j,r in enumerate(rows) if r['seq']==prep['seq'])
            q=r19.r17.validate_prefix(rows[max(0,pos-7):pos],prep,tag,rows)
            if before['tag']!=tag or before['site']!=q[2]:raise ValueError('Literal site/tag mismatch')
            result.update(prep_seq=prep['seq'],helper=q[0],serial=q[1],site=q[2])
            if i+1<len(records) and records[i+1]['kind']=='literal':
                after=records[i+1]
                if after['phase']!='after' or (after['tag'],after['site'])!=(tag,q[2]):raise ValueError('Mismatched literal after')
                claimed.add(i+1)
                if i+2<len(records) and records[i+2]['kind']=='literal':raise ValueError('Duplicate/interleaved literal marker')
                result.update(classification='matched-literal-source',source_continuation_observed=True)
            elif any(r['kind']=='literal' and r['phase']=='after' and r['site']==q[2] for r in records[i+1:]):
                raise ValueError('Nonadjacent literal after cannot be joined')
        except (ValueError,StopIteration) as exc:
            result.update(classification='ambiguous',refusal=str(exc),source_continuation_observed=False)
        outcomes.append(result)
    for i,r in enumerate(records):
        if r['kind']=='literal' and r['phase']=='after' and i not in claimed:
            outcomes.append(dict(classification='literal-after-without-before',cause='unproved',source_continuation_observed=False))
    return dict(outcomes=outcomes,**r19.r17.FLAGS)


def replay():
    for name,digest in json.loads((HERE/'historical-pins.json').read_text()).items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest:raise ValueError('Historical input changed')
    result=dict(**r19.r17.FLAGS,live_validated=False,runs={})
    for number,first,last in [('18',8210,8224),('20',6451,6465)]:
        package=HERE.parent/('native-fight-r'+number)
        build=json.loads((package/'build.json').read_text())
        path=package/'run-01/combined.log' if number=='20' else package/'run-01/flashlog.after.log'
        raw=path.read_bytes();records,rows=parse(raw,build['run_id'])
        report=dict(literal=classify(records,rows,build['run_id']),direct=r19.classify(records,rows,build['run_id']),sink=r19.r17.classify(rows,build['run_id']),candidate=[r for r in rows if first<=r['seq']<=last])
        try:r19.r17.history.r05.validate_rows((package/'run-01/tagged.log').read_bytes(),build)
        except ValueError as exc:report['structural_refusal']=str(exc)
        result['runs']['r'+number]=report
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--require-oracle',action='store_true');p.add_argument('--output',type=Path);a=p.parse_args();r=replay()
    if a.output:a.output.write_text(json.dumps(r,indent=2)+'\n')
    print({k:v.get('structural_refusal') for k,v in r['runs'].items()})
    print('No literal-channel live proof; admission refused');raise SystemExit(1)
