"""Reject or constrain the fixed right-border hypothesis on independent kernels/widths."""
import argparse
import hashlib
import json
from pathlib import Path
from tools.probes.run_native_extent_rows import ROOT
from tools.probes.run_nested_filters import unpack
from tools.probes.analyze_filter_borders import predict


def decode(native):
    build=json.loads((native/'build.json').read_text())
    if hashlib.sha256((ROOT/build['source']).read_bytes()).hexdigest()!=build['source_sha256']:
        raise ValueError('Native source changed')
    events=[line.split('|') for line in (native/'native.log').read_text().splitlines() if line.startswith('AIREF|')]
    if len(events)!=1513 or events[-1][6:]!=['done','ok']:
        raise ValueError('Held-out controls incomplete')
    for i,row in enumerate(events):
        if row[1]!=build['run_id'] or row[2:6]!=[str(i),'0','0','0']:
            raise ValueError('Native control identity/order changed')
    cases=[]
    for w in (5,8,9,12,13,21,25,35,65):
        for left in (40,41):
            for op in (100,50):
                for kernel in (2,3,4,6,7,8,9):
                    index=len(cases);rows=events[index*6:index*6+6]
                    key=list(map(int,rows[1][7].split(',')))
                    if rows[1][6]!='case' or len(key)!=11 or key[:5]!=[index,w,left,op,kernel]:
                        raise ValueError('Held-out case identity changed')
                    _,_,_,_,_,x,y,rw,rh,bw,bh=key
                    pad=left-x
                    if pad<0 or key[6:]!=[40-pad,w+2*pad,64+2*pad,w+2*pad+1,64+2*pad]:
                        raise ValueError('Measured rectangle or actual bitmap size inconsistent')
                    case={'key':key,'measured_padding':pad}
                    for row,stage in zip((rows[0],*rows[2:]),('input','implicit_filtered','implicit_final','explicit_filtered','explicit_final')):
                        values=row[7].split(',')
                        if row[6]!='row' or values[:2]!=[str(index),stage] or len(values)!=322:
                            raise ValueError('Native stage missing/reordered')
                        case[stage]=unpack(list(map(int,values[2:])))
                    cases.append(case)
    return cases


def analyze(native):
    cases=decode(native);scores={k:{'pixels':40320,'exact':0,'failures':[]} for k in ('filtered','final','declared_model')}
    padding={}
    for case in cases:
        key=case['key'];padding.setdefault(str(key[4]),set()).add(case['measured_padding'])
        for stage in ('filtered','final'):
            for x,(a,b) in enumerate(zip(case['implicit_'+stage],case['explicit_'+stage])):
                if a==b:scores[stage]['exact']+=1
                else:scores[stage]['failures'].append({'key':key,'x':x,'implicit':a,'explicit':b})
        for x,(p,target) in enumerate(zip(case['explicit_filtered'],case['explicit_final'])):
            actual=predict(p,key[3],key[9],x-key[5])
            if actual==target:scores['declared_model']['exact']+=1
            else:scores['declared_model']['failures'].append({'key':key,'x':x,'model':actual,'native':target})
    return {'scores':scores,'measured_padding':{k:sorted(v) for k,v in padding.items()},
            'right_border_hypothesis_passed':not scores['final']['failures'],
            'implicit_extent_model_admitted':False,'production_admitted':False}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();r=analyze(args.native.resolve());args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'analysis.json').write_text(json.dumps(r,indent=2)+'\n')
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    files=['tools/probes/analyze_filter_border_heldout.py','tools/probes/flash_filters/filter-border-heldout.as','tools/probes/analyze_filter_borders.py','tools/probes/native_cxform_candidate.py']
    p={'source_sha256':{s:sha(ROOT/s) for s in files},'native_sha256':{s:sha(args.native/s) for s in ('build.json','native.log')},'output_sha256':{'analysis.json':sha(args.output/'analysis.json')},'production_admitted':False}
    (args.output/'provenance.json').write_text(json.dumps(p,indent=2)+'\n')
    print({k:(v['exact'],v['pixels']) for k,v in r['scores'].items()});print('padding',r['measured_padding'])
    raise SystemExit(1)
