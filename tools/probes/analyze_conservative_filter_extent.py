"""Reject conservative ceil extents against old and independent fractional controls."""
import argparse
import hashlib
import json
import math
from pathlib import Path
from tools.probes.run_native_extent_rows import ROOT, decode as old_decode
from tools.probes.analyze_filter_border_heldout import decode as heldout_decode
from tools.probes.analyze_filter_borders import predict
from tools.probes.run_nested_filters import unpack


def decode(native):
    build=json.loads((native/'build.json').read_text())
    if hashlib.sha256((ROOT/build['source']).read_bytes()).hexdigest()!=build['source_sha256']:
        raise ValueError('Native source changed')
    events=[s.split('|') for s in (native/'native.log').read_text().splitlines() if s.startswith('AIREF|')]
    if len(events)!=1441 or events[-1][6:]!=['done','ok']:raise ValueError('Fractional controls incomplete')
    for i,row in enumerate(events):
        if row[1]!=build['run_id'] or row[2:6]!=[str(i),'0','0','0']:raise ValueError('Native order/identity changed')
    cases=[]
    for width in (5,9,13,17,33,64):
        for left in (40,41):
            for opacity in (100,50):
                for kernel in (3.5,3.99609375,4,4.00390625,4.5,7.5,7.99609375,8,8.00390625,8.5):
                    index=len(cases);rows=events[index*6:index*6+6];key=list(map(float,rows[1][7].split(',')))
                    pad=math.ceil((kernel+1)/2)
                    if rows[1][6]!='case' or len(key)!=14 or key[:5]!=[index,width,left,opacity,kernel]:
                        raise ValueError('Fractional control identity changed')
                    if key[9:]!=[width+2*pad+1,64+2*pad+1,left-pad,40-pad,kernel]:
                        raise ValueError('Actual conservative extent or retained property changed')
                    public=left-key[5]
                    if key[5:9]!=[left-public,40-public,width+2*public,64+2*public]:
                        raise ValueError('Public rectangle inconsistent')
                    case={'key':key}
                    for row,stage in zip((rows[0],*rows[2:]),('input','implicit_filtered','implicit_final','explicit_filtered','explicit_final')):
                        values=row[7].split(',')
                        if row[6]!='row' or values[:2]!=[str(index),stage] or len(values)!=322:
                            raise ValueError('Native stage incomplete')
                        case[stage]=unpack(list(map(int,values[2:])))
                    cases.append(case)
    return cases


def score(rows):
    result={'pixels':0,'exact':0,'failures':[]}
    for key,x,actual,native in rows:
        result['pixels']+=1
        if actual==native:result['exact']+=1
        else:result['failures'].append({'key':key,'x':x,'actual':actual,'native':native})
    return result


def analyze(native):
    fresh=decode(native)
    comparisons={stage:score((c['key'],x,a,b) for c in fresh for x,(a,b) in enumerate(zip(c['explicit_'+stage],c['implicit_'+stage]))) for stage in ('filtered','final')}
    explicit=score((c['key'],x,predict(p,int(c['key'][3]),int(c['key'][9]),x-int(c['key'][11])),target)
                   for c in fresh for x,(p,target) in enumerate(zip(c['explicit_filtered'],c['explicit_final'])))
    old=[]
    for c in old_decode(ROOT/'evidence/importer-loud-fail/r62/native'):
        old.append(([c['id'],c['width'],c['left'],c['opacity'],5],c['filtered'],c['final']))
    for c in heldout_decode(ROOT/'evidence/importer-loud-fail/r66/native'):
        old.append((c['key'][:5],c['implicit_filtered'],c['implicit_final']))
    def prior_rows():
        for key,source,target in old:
            pad=math.ceil((key[4]+1)/2);width=key[1]+2*pad+1;origin=key[2]-pad
            for x,(p,q) in enumerate(zip(source,target)):yield key,x,predict(p,key[3],width,x-origin),q
    return {'prior_integer_controls':score(prior_rows()),'new_explicit_model':explicit,
            'new_native_comparisons':comparisons,'conservative_model_admitted':False,'production_admitted':False}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();r=analyze(args.native.resolve());args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'analysis.json').write_text(json.dumps(r,indent=2)+'\n')
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    files=['tools/probes/analyze_conservative_filter_extent.py','tools/probes/flash_filters/filter-conservative-extent.as','tools/probes/analyze_filter_borders.py','tools/probes/native_cxform_candidate.py','evidence/importer-loud-fail/r62/native/native.log','evidence/importer-loud-fail/r66/native/native.log']
    p={'source_sha256':{s:sha(ROOT/s) for s in files},'native_sha256':{s:sha(args.native/s) for s in ('build.json','native.log')},'output_sha256':{'analysis.json':sha(args.output/'analysis.json')},'production_admitted':False}
    (args.output/'provenance.json').write_text(json.dumps(p,indent=2)+'\n')
    print('old',r['prior_integer_controls']['exact'],r['prior_integer_controls']['pixels'])
    print('explicit',r['new_explicit_model']['exact'],r['new_explicit_model']['pixels'])
    print({k:(v['exact'],v['pixels']) for k,v in r['new_native_comparisons'].items()})
    raise SystemExit(1)
