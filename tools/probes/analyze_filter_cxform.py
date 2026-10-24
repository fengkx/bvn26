"""Rejected byte-CXFORM hypothesis: scalar success cannot admit nested filters."""
import argparse
import hashlib
import json
from pathlib import Path
from tools.probes.run_nested_filters import cases, decode, unpack
from tools.probes.normal_composition import over


def candidate(pixel, opacity):
    alpha = pixel[3]
    straight = [c*255//alpha if alpha else 0 for c in pixel[:3]]
    color = [max(0,min(255,c*m//256+d)) for c,m,d in zip(straight,(128,192,256),(8,0,-4))]
    alpha = alpha*(opacity*256//100)//256
    return [c*(alpha+1)//256 for c in color]+[alpha]


def scalar_rows(directory):
    build=json.loads((directory/'build.json').read_text())
    if hashlib.sha256(Path(build['source']).read_bytes()).hexdigest()!=build['source_sha256']:
        raise ValueError('Scalar source hash mismatch')
    expected=[[c,a,o] for c in range(4) for a in (0,1,2,7,63,128,254,255) for o in (25,50,100)]
    rows=[];done=False
    for line in (directory/'native.log').read_text().splitlines():
        p=line.split('|')
        if p[:2]!=['AIREF',build['run_id']]:continue
        if len(p)!=8 or done or p[2:6]!=[str(len(rows)),'0','0','0']:
            raise ValueError('Missing/reordered scalar event')
        if p[6:] == ['done','ok']:
            done=True;continue
        if p[6]!='cx' or len(rows)>=len(expected):raise ValueError('Unexpected scalar event')
        v=list(map(int,p[7].split(',')))
        if len(v)!=8 or v[:4]!=[len(rows),*expected[len(rows)]]:raise ValueError('Scalar identity mismatch')
        source,native=unpack(v[4:]);got=candidate(source,v[3])
        rows.append({'key':v[:4],'source':source,'native':native,'candidate':got})
    if not done or len(rows)!=96:raise ValueError('Incomplete scalar capture')
    return rows


def analyze(scalar,nested):
    rows=scalar_rows(scalar);failures=[];count=0
    for spec,ref in zip(cases(),decode(nested)):
        if not spec['key'][5]:continue
        for y in range(12):
            for x in range(12):
                source=ref['child_filter'][y*12+x]
                got=over(spec['inputs']['middle'],candidate(source,spec['key'][3]))
                native=ref['parent_input'][(y+3)*18+x+3]
                count+=1
                if got!=native:
                    failures.append({'key':spec['key'],'x':x,'y':y,'source':source,'native':native,'candidate':got})
    return {'production_admitted':False,'candidate_admitted':False,
            'scalar':{'samples':96,'exact':sum(r['candidate']==r['native'] for r in rows),'rows':rows},
            'nested':{'samples':count,'exact':count-len(failures),
                      'max_delta':max((abs(a-b) for f in failures for a,b in zip(f['native'],f['candidate'])),default=0),
                      'failures':failures}}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('scalar','nested','output'):p.add_argument('--'+name,type=Path,required=True)
    args=p.parse_args();result=analyze(args.scalar,args.nested)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:{a:b for a,b in v.items() if a not in ('rows','failures')} if isinstance(v,dict) else v for k,v in result.items()}))
    raise SystemExit(0 if result['nested']['exact']==result['nested']['samples'] else 1)
