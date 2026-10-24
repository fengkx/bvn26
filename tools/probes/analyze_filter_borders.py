"""Evaluate independently declared transparent border controls without admitting a padding rule."""
import argparse
import hashlib
import json
from pathlib import Path
from tools.probes.run_native_extent_rows import decode as decode_prior, ROOT
from tools.probes.run_nested_filters import unpack
from tools.probes.native_cxform_candidate import channel

BORDERS = ((0,0),(0,1),(0,2),(0,3),(1,0),(2,0),(3,0))


def decode(native):
    build = json.loads((native/'build.json').read_text())
    if hashlib.sha256((ROOT/build['source']).read_bytes()).hexdigest()!=build['source_sha256']:
        raise ValueError('Native source changed')
    events = [line.split('|') for line in (native/'native.log').read_text().splitlines() if line.startswith('AIREF|')]
    if len(events)!=1121 or events[-1][6:]!=['done','ok']:
        raise ValueError('Missing border controls')
    for i,r in enumerate(events):
        if r[1]!=build['run_id'] or r[2:6]!=[str(i),'0','0','0']:
            raise ValueError('Native event identity/order changed')
    cases=[]
    for w in (15,16,17,18,19,20,31,32,33,64):
        for left in (40,41):
            for op in (100,50):
                for lp,rp in BORDERS:
                    index=len(cases);rows=events[index*4:index*4+4]
                    key=[index,w,left,op,lp,rp,w+6+lp+rp,70,left-3-lp,37]
                    if rows[1][6]!='case' or list(map(int,rows[1][7].split(',')))!=key:
                        raise ValueError('Border dimensions or identity changed')
                    case={'key':key}
                    for row,stage in zip((rows[0],rows[2],rows[3]),('input','filtered','final')):
                        values=row[7].split(',')
                        if row[6]!='row' or values[:2]!=[str(index),stage] or len(values)!=322:
                            raise ValueError('Native stage incomplete')
                        case[stage]=unpack(list(map(int,values[2:])))
                    cases.append(case)
    return cases


def predict(pixel, opacity, width, x):
    a=pixel[3];op=opacity*256//100
    if a==0 or not 0<=x<width:
        return [0,0,0,0]
    if width>=16 and x<width//4*4:
        return [channel((c,a,0,d,opacity)) for c,d in zip(pixel[:3],(57,148,230))]+[a*op//256]
    alpha=a*op//256
    return [d*(alpha+1)//256 for d in (57,148,230)]+[alpha]


def analyze(native):
    cases=decode(native)
    implicit=decode_prior(ROOT/'evidence/importer-loud-fail/r62/native')
    explicit=decode_prior(ROOT/'evidence/importer-loud-fail/r64/native')
    unchanged={stage:{'pixels':44800,'exact':0,'failures':[]} for stage in ('input','filtered')}
    models={'pixels':44800,'exact':0,'failures':[]}
    comparisons={str(list(border)):{'pixels':6400,'exact':0,'failures':[]} for border in BORDERS}
    for case in cases:
        key=case['key'];index,w,left,op,lp,rp,width,_,origin,_=key;base=index//len(BORDERS)
        if (lp,rp)==(0,0) and any(case[s]!=explicit[base][s] for s in ('input','filtered','final')):
            raise ValueError('Zero-border explicit baseline regressed')
        for stage in unchanged:
            for x,(p,q) in enumerate(zip(case[stage],implicit[base][stage])):
                if p==q:unchanged[stage]['exact']+=1
                else:unchanged[stage]['failures'].append({'key':key,'x':x,'new':p,'old':q})
        for x,(p,target) in enumerate(zip(case['filtered'],case['final'])):
            actual=predict(p,op,width,x-origin)
            if actual==target:models['exact']+=1
            else:models['failures'].append({'key':key,'x':x,'model':actual,'native':target})
        group=comparisons[str([lp,rp])]
        for x,(p,q) in enumerate(zip(case['final'],implicit[base]['final'])):
            if p==q:group['exact']+=1
            else:group['failures'].append({'key':key,'x':x,'explicit':p,'implicit':q})
    return {'unchanged_stages':unchanged,'declared_extent_model':models,'implicit_comparisons':comparisons,
            'implicit_extent_model_admitted':False,'production_admitted':False,
            'scope':'Fixed declared extents explain explicit controls; matches do not establish an implicit-cache padding rule.'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();r=analyze(args.native.resolve());args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'analysis.json').write_text(json.dumps(r,indent=2)+'\n')
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    sources=['tools/probes/analyze_filter_borders.py','tools/probes/flash_filters/filter-border-extent.as','tools/probes/native_cxform_candidate.py','evidence/importer-loud-fail/r62/native/native.log','evidence/importer-loud-fail/r64/native/native.log']
    p={'source_sha256':{s:sha(ROOT/s) for s in sources},'native_sha256':{s:sha(args.native/s) for s in ('build.json','native.log')},'output_sha256':{'analysis.json':sha(args.output/'analysis.json')},'production_admitted':False}
    (args.output/'provenance.json').write_text(json.dumps(p,indent=2)+'\n')
    print('Input/filter',{k:(v['exact'],v['pixels']) for k,v in r['unchanged_stages'].items()})
    print('Declared model',r['declared_extent_model']['exact'],r['declared_extent_model']['pixels'])
    print('Implicit comparisons',{k:v['exact'] for k,v in r['implicit_comparisons'].items()})
    raise SystemExit(1)
