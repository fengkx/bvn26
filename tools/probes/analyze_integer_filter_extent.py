"""Bound a common integer-consumption extent against all prior and fresh native controls."""
import argparse
import hashlib
import json
import math
from pathlib import Path
from tools.probes.run_native_extent_rows import ROOT, decode as initial_decode
from tools.probes.analyze_filter_border_heldout import decode as integer_decode
from tools.probes.analyze_conservative_filter_extent import decode as fractional_decode, score
from tools.probes.analyze_filter_borders import predict
from tools.probes.run_nested_filters import unpack


def extent(width, left, kernel):
    if not all(math.isfinite(v) for v in (width,left,kernel)) or width<=0 or kernel<0:
        raise ValueError('Invalid bounded extent input')
    if width!=int(width) or left!=int(left):
        raise ValueError('Fractional origin/width not admitted by this diagnostic')
    padding=math.floor(kernel/2)+1
    return width+2*padding+1,left-padding


def decode(native):
    build=json.loads((native/'build.json').read_text())
    if hashlib.sha256((ROOT/build['source']).read_bytes()).hexdigest()!=build['source_sha256']:
        raise ValueError('Native source changed')
    events=[s.split('|') for s in (native/'native.log').read_text().splitlines() if s.startswith('AIREF|')]
    if len(events)!=1153 or events[-1][6:]!=['done','ok']:raise ValueError('New controls incomplete')
    for i,row in enumerate(events):
        if row[1]!=build['run_id'] or row[2:6]!=[str(i),'0','0','0']:raise ValueError('Native identity/order changed')
    cases=[]
    for width in (5,9,17,33):
        for left in (40,41):
            for opacity in (100,50):
                for kernel in (0,0.5,1,1.5,1.99609375,2,2.00390625,2.5,3.5,4,4.5,8):
                    index=len(cases);rows=events[index*6:index*6+6];key=list(map(float,rows[1][7].split(',')))
                    cw,cx=extent(width,left,kernel);pad=left-cx
                    if rows[1][6]!='case' or len(key)!=14 or key[:5]!=[index,width,left,opacity,kernel]:
                        raise ValueError('Fresh case identity changed')
                    if key[9:]!=[cw,64+2*pad+1,cx,40-pad,kernel]:raise ValueError('Declared extent/property changed')
                    public=left-key[5]
                    if key[5:9]!=[left-public,40-public,width+2*public,64+2*public]:raise ValueError('Public rectangle inconsistent')
                    case={'key':key}
                    for row,stage in zip((rows[0],*rows[2:]),('input','implicit_filtered','implicit_final','explicit_filtered','explicit_final')):
                        values=row[7].split(',')
                        if row[6]!='row' or values[:2]!=[str(index),stage] or len(values)!=322:raise ValueError('Native stage incomplete')
                        case[stage]=unpack(list(map(int,values[2:])))
                    cases.append(case)
    return cases


def analyze(native):
    fresh=decode(native);old=[]
    for c in initial_decode(ROOT/'evidence/importer-loud-fail/r62/native'):
        old.append(([c['id'],c['width'],c['left'],c['opacity'],5],c['filtered'],c['final']))
    for directory,reader in [('r66',integer_decode),('r68',fractional_decode)]:
        for c in reader(ROOT/'evidence/importer-loud-fail'/directory/'native'):
            old.append((c['key'][:5],c['implicit_filtered'],c['implicit_final']))
    def predictions(rows):
        for key,source,target in rows:
            width,origin=extent(key[1],key[2],key[4])
            for x,(p,q) in enumerate(zip(source,target)):
                yield key,x,predict(p,int(key[3]),int(width),x-int(origin)),q
    prior=score(predictions(old))
    explicit=score(predictions([(c['key'][:5],c['explicit_filtered'],c['explicit_final']) for c in fresh]))
    comparisons={stage:score((c['key'],x,p,q) for c in fresh for x,(p,q) in enumerate(zip(c['implicit_'+stage],c['explicit_'+stage]))) for stage in ('filtered','final')}
    passed=all(not v['failures'] for v in [prior,explicit,*comparisons.values()])
    return {'prior_implicit':prior,'new_explicit':explicit,'new_native_comparisons':comparisons,
            'bounded_native_controls_passed':passed,'production_admitted':False,
            'scope':'Integer destination origins, one Glow pass; no internal instruction/allocator or general affine claim.'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();r=analyze(args.native.resolve());args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'analysis.json').write_text(json.dumps(r,indent=2)+'\n')
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    files=['tools/probes/analyze_integer_filter_extent.py','tools/probes/flash_filters/filter-integer-extent.as','tools/probes/analyze_filter_borders.py','tools/probes/native_cxform_candidate.py']+['evidence/importer-loud-fail/'+s+'/native/native.log' for s in ('r62','r66','r68')]
    p={'source_sha256':{s:sha(ROOT/s) for s in files},'native_sha256':{s:sha(args.native/s) for s in ('build.json','native.log')},'output_sha256':{'analysis.json':sha(args.output/'analysis.json')},'production_admitted':False}
    (args.output/'provenance.json').write_text(json.dumps(p,indent=2)+'\n')
    print('prior',r['prior_implicit']['exact'],r['prior_implicit']['pixels']);print('new explicit',r['new_explicit']['exact'],r['new_explicit']['pixels']);print({k:(v['exact'],v['pixels']) for k,v in r['new_native_comparisons'].items()})
    raise SystemExit(0 if r['bounded_native_controls_passed'] else 1)
