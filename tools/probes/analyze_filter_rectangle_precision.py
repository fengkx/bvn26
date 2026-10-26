"""Constrain public filter rectangle arithmetic independently of rendered RGB."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
from tools.probes.run_native_extent_rows import ROOT


def decode(folder, fine=False, half=False):
    build=json.loads((folder/'build.json').read_text())
    if hashlib.sha256((ROOT/build['source']).read_bytes()).hexdigest()!=build['source_sha256']:
        raise ValueError('Native rectangle source changed')
    count=132 if fine else 156;per_center=22 if fine else 26
    events=[s.split('|') for s in (folder/'native.log').read_text().splitlines() if s.startswith('AIREF|')]
    if len(events)!=count+1 or events[-1][6:]!=['done','ok']:
        raise ValueError('Rectangle capture incomplete')
    result=[]
    for i,e in enumerate(events):
        if e[1]!=build['run_id'] or e[2:6]!=[str(i),'0','0','0']:
            raise ValueError('Native rectangle identity/order changed')
        if i==count:break
        fields=e[7].split(',')
        if e[6]!='rect' or len(fields)!=11:
            raise ValueError('Missing rectangle/property fields')
        values=list(map(float,fields))
        if not all(math.isfinite(v) for v in values):raise ValueError('Nonfinite native property')
        index,center,offset,kind,requested,x,y,rx,ry,rw,rh=values
        if index!=i or center!=2+2*(i//per_center)+(0.5 if half else 0) or kind!=i%2:
            raise ValueError('Unexpected center/kind')
        pad=40-rx
        if pad<0 or pad!=int(pad) or [rx,ry,rw,rh]!=[40-pad,40-pad,17+2*pad,64+2*pad]:
            raise ValueError('Malformed native rectangle')
        result.append({'index':i,'center':center,'offset':offset,'kind':int(kind),'requested_text':fields[4],
                       'property_x_text':fields[5],'property_y_text':fields[6],'property':x,'padding':int(pad)})
    return result


def analyze(root):
    f32=lambda v:struct.unpack('<f',struct.pack('<f',v))[0]
    groups={name:decode(root/name,fine=name!='wide',half=name=='half') for name in ('wide','fine','half')}
    scores={kind:{model:{'controls':0,'exact':0,'failures':[]} for model in ('double_input','float32_input')}
            for kind in ('glow','blur')}
    property_count=0
    for group,rows in groups.items():
        for row in rows:
            property_count+=row['requested_text']==row['property_x_text']==row['property_y_text']
            kind='glow' if row['kind']==0 else 'blur'
            for model in ('double_input','float32_input'):
                value=row['property'] if model=='double_input' else f32(row['property'])
                predicted=round((value+1)/2) if kind=='glow' else math.floor(value/2+0.75)
                score=scores[kind][model];score['controls']+=1
                if predicted==row['padding']:score['exact']+=1
                else:score['failures'].append({'capture':group,**row,'predicted_padding':predicted})
    return {'property_text_matches':property_count,'controls':420,'scores':scores,
            'public_rectangle_controls_passed':all(v['double_input']['exact']==210 for v in scores.values()),
            'implicit_extent_model_admitted':False,'production_admitted':False,
            'scope':'Logged property retention and public rectangle behavior only; no ISA or implicit-allocation claim.'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();r=analyze(args.native.resolve());args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'analysis.json').write_text(json.dumps(r,indent=2)+'\n')
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    files=['tools/probes/analyze_filter_rectangle_precision.py']+['tools/probes/flash_filters/filter-rectangle-'+s+'.as' for s in ('precision','fine','half')]
    p={'source_sha256':{s:sha(ROOT/s) for s in files},'native_sha256':{str(s.relative_to(args.native)):sha(s) for folder in ('wide','fine','half') for s in (args.native/folder/'build.json',args.native/folder/'native.log')},'output_sha256':{'analysis.json':sha(args.output/'analysis.json')},'production_admitted':False}
    (args.output/'provenance.json').write_text(json.dumps(p,indent=2)+'\n')
    print('properties',r['property_text_matches'],r['controls']);print({k:{m:v['exact'] for m,v in s.items()} for k,s in r['scores'].items()})
    raise SystemExit(1)
