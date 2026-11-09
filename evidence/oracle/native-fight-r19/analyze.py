"""Require an exact root-prep/direct-trace bridge; never infer absent execution."""
import argparse
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('r19_pair',HERE.parent/'native-fight-r17/analyze.py')
r17=importlib.util.module_from_spec(spec);spec.loader.exec_module(r17)


def classify(records, rows, tag):
    """Records preserve combined raw-line order; side records have kind/data/phase."""
    results=[];claimed=set()
    for i,before in enumerate(records):
        if before['kind']!='direct' or before['phase']!='before':continue
        result=dict(classification='before-without-after',cause='unproved',source_continuation_observed=False)
        try:
            if i==0 or records[i-1]['kind']!='continuation-prep':raise ValueError('Missing adjacent root prep')
            prep=records[i-1]
            if before['data']!=prep['data']:raise ValueError('Root/side identity mismatch')
            pos=next(j for j,r in enumerate(rows) if r['seq']==prep['seq'])
            r17.validate_prefix(rows[max(0,pos-7):pos],prep,tag,rows)
            befores=[r for r in records if r['kind']=='direct' and r['phase']=='before' and r['data']==before['data']]
            afters=[(j,r) for j,r in enumerate(records) if r['kind']=='direct' and r['phase']=='after' and r['data']==before['data']]
            if len(befores)!=1 or len(afters)>1:raise ValueError('Repeated side identity')
            if afters:
                j,after=afters[0];claimed.add(j)
                if j!=i+1:raise ValueError('Interleaved/reversed direct pair')
                result.update(classification='matched-direct-trace',source_continuation_observed=True)
        except (ValueError,StopIteration) as exc:
            result.update(classification='ambiguous',refusal=str(exc))
        results.append(result)
    for i,r in enumerate(records):
        if r['kind']=='direct' and r['phase']=='after' and i not in claimed:
            results.append(dict(classification='after-without-before',cause='unproved',source_continuation_observed=False))
    return dict(outcomes=results,**r17.FLAGS)


def parse_combined(raw,tag):
    root=[];records=[]
    for line in raw.splitlines():
        if line.startswith(b'M002|'):
            root.append(line);f=line.decode('ascii').split('|',7)
            if len(f)!=8 or f[1]!=tag:raise ValueError('Foreign/malformed root tag')
            records.append(dict(seq=int(f[2]),kind=f[6],data=f[7]))
        elif line.startswith(b'M002SIDE|'):
            f=line.decode('ascii').split('|')
            if len(f)!=3 or f[2] not in ('before','after') or f[1].split(',')[0]!=tag:raise ValueError('Foreign/malformed side tag')
            records.append(dict(kind='direct',phase=f[2],data=f[1]))
        elif line.strip():
            # Unknown log content is an ordering barrier, not silently erased.
            records.append(dict(kind='unclassified',data=line.decode('ascii',errors='replace')))
    rows=r17.history.r05.base.parse(b'\n'.join(root)+b'\n',tag)
    return records,rows


def replay():
    old=HERE.parent/'native-fight-r18'
    build=json.loads((old/'build.json').read_text())
    raw=(old/'run-01/tagged.log').read_bytes()
    pins=json.loads((HERE/'historical-pins.json').read_text())
    import hashlib
    for name,digest in pins.items():
        if hashlib.sha256((HERE.parents[2]/name).read_bytes()).hexdigest()!=digest:raise ValueError('Historical input changed')
    records,rows=parse_combined(raw,build['run_id'])
    report=classify(records,rows,build['run_id'])
    report['r17_pairing']=r17.classify(rows,build['run_id'])
    report['candidate']=[r for r in rows if 8210<=r['seq']<=8224]
    report['live_validated']=False
    try:r17.history.r05.validate_rows(raw,build)
    except ValueError as exc:report['structural_refusal']=str(exc)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--require-oracle',action='store_true');p.add_argument('--output',type=Path);a=p.parse_args()
    r=replay()
    if a.output:a.output.write_text(json.dumps(r,indent=2)+'\n')
    print(r.get('structural_refusal','Full oracle obligations unproved'))
    print('No r19 live side-channel evidence; admission refused')
    raise SystemExit(1)
