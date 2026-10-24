"""Independent alpha/width controls for the rejected universal CXFORM model."""
import argparse
import hashlib
import json
from pathlib import Path
from tools.probes.run_nested_filters import unpack
from tools.probes.nested_composition import rgba


def fixed_cx(pixel, opacity):
    alpha=pixel[3]
    reciprocal=65280//alpha if alpha else 0
    straight=[c*reciprocal//256 for c in pixel[:3]]
    straight=[max(0,min(255,c*m//256+d)) for c,m,d in zip(straight,(128,192,256),(8,0,-4))]
    alpha=alpha*(opacity*256//100)//256
    return [c*(alpha+1)//256 for c in straight]+[alpha]


def events(directory, kind, identities):
    build=json.loads((directory/'build.json').read_text())
    if hashlib.sha256(Path(build['source']).read_bytes()).hexdigest()!=build['source_sha256']:
        raise ValueError('Control source changed')
    rows=[];done=False
    for line in (directory/'native.log').read_text().splitlines():
        p=line.split('|')
        if p[:2]!=['AIREF',build['run_id']]:continue
        if len(p)!=8 or done or p[2:6]!=[str(len(rows)),'0','0','0']:
            raise ValueError('Malformed/reordered control capture')
        if p[6:]==['done','ok']:
            done=True;continue
        if p[6]!=kind or len(rows)>=len(identities):raise ValueError('Unexpected control event')
        v=list(map(int,p[7].split(',')));identity=identities[len(rows)]
        if v[:len(identity)]!=identity:raise ValueError('Control identity changed')
        rows.append(v)
    if not done or len(rows)!=len(identities):raise ValueError('Incomplete controls')
    return rows


def analyze(root):
    identities=[]
    for color in range(4):
        for alpha in range(256):
            for opacity in (25,50,100):identities.append([len(identities),color,alpha,opacity])
    dense=events(root/'dense','cx',identities);scores={}
    failures=[]
    for row in dense:
        if len(row)!=8:raise ValueError('Invalid scalar payload')
        source,native=unpack(row[4:]);actual=fixed_cx(source,row[3])
        if actual!=native:failures.append({'key':row[:4],'actual':actual,'native':native})
    scores['dense']={'pixels':len(dense),'exact':len(dense)-len(failures),'failures':failures}
    identities=[]
    for width in (1,3,4,7,8,12,15,16,17,18,31,32,33):
        for origin in (0,1,3):
            for alpha in (7,93,135,231):
                for opacity in (25,50,100):identities.append([len(identities),width,origin,alpha,opacity])
    for name in ('spans','varied'):
        rows=events(root/name,'span',identities);pixels=0;failures=[]
        for row in rows:
            index,width,origin,alpha,opacity=row[:5]
            if len(row)!=7+(width+origin+2)*2:raise ValueError('Invalid span extent')
            if unpack(row[5:7])!=[rgba(0x46c4ec,alpha)]:raise ValueError('Span input mismatch')
            native=unpack(row[7:])
            for x,pixel in enumerate(native):
                source=rgba(0xff8001 if name=='varied' and (x-origin)%2 else 0x46c4ec,alpha)
                actual=fixed_cx(source,opacity) if origin<=x<origin+width else [0]*4
                pixels+=1
                if actual!=pixel:failures.append({'key':row[:5],'x':x,'actual':actual,'native':pixel})
        scores[name]={'cases':len(rows),'pixels':pixels,'exact':pixels-len(failures),'failures':failures}
    return {'production_admitted':False,'candidate_admitted':False,
            'scope':'Independent controls only; universal model rejected by nested final images. No span selector admitted.',
            'scores':scores}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();result=analyze(args.root);args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:{a:b for a,b in v.items() if a!='failures'} for k,v in result['scores'].items()}))
    raise SystemExit(0 if all(r['pixels']==r['exact'] for r in result['scores'].values()) else 1)
