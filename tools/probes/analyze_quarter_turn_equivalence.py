"""Compare fixed quarter-turn fill transforms with independently materialized texel permutations."""
import argparse
import json
from pathlib import Path
from tools.probes.analyze_bitmap_cache_support_local import events
from tools.probes.run_nested_filters import unpack
from tools.probes.analyze_jiraiya_filter_boundary import comparison


def decode(native):
    rows=events(native)
    assert len(rows)==14418
    source=[];rotated={};cases=[]
    for kind,payload in rows:
        values=payload.split(',')
        if kind=='source':
            assert int(values[0])==len(source)//4 and len(values)==9
            source.extend(unpack(list(map(int,values[1:]))))
        elif kind=='rotated':
            turn,y=map(int,values[:2]);width=3 if turn%2 else 4
            pixels=rotated.setdefault(turn,[])
            assert y==len(pixels)//width and len(values)==2+2*width
            pixels.extend(unpack(list(map(int,values[2:]))))
        elif kind=='case':
            assert int(values[0])==len(cases) and len(values)==16
            cases.append({'key':values,'pixels':[]})
        elif kind=='row':
            pixels=cases[-1]['pixels'];assert int(values[0])==len(pixels)//32 and len(values)==65
            pixels.extend(unpack(list(map(int,values[1:]))))
        else:assert [kind,payload]==['done','ok']
    assert len(source)==12 and len(cases)==576 and all(len(c['pixels'])==768 for c in cases)
    for turn in range(4):
        expected=[None]*12;width=3 if turn%2 else 4
        for y in range(3):
            for x in range(4):
                xx,yy=((x,y),(2-y,x),(3-x,2-y),(y,3-x))[turn]
                expected[yy*width+xx]=source[y*4+x]
        assert rotated[turn]==expected,'Materialized source bytes changed'
    return source,rotated,cases


def analyze(native):
    source,rotated,cases=decode(native);pairs=[];groups={}
    for a,b in zip(cases[::2],cases[1::2]):
        ka,kb=a['key'],b['key'];turn=int(ka[1]);assert ka[2]=='0' and kb[2]=='1'
        assert ka[1:2]+ka[3:10]==kb[1:2]+kb[3:10]
        expected=[(1,0,0,1,0,0),(0,1,-1,0,3,0),(-1,0,0,-1,4,3),(0,-1,1,0,0,4)][turn]
        assert list(map(float,ka[10:]))==list(expected)
        assert list(map(float,kb[10:]))==[1,0,0,1,0,0]
        result=comparison(a['pixels'],b['pixels'])
        differences=[{'x':i%32,'y':i//32,'matrix':p,'permuted':q} for i,(p,q) in enumerate(zip(a['pixels'],b['pixels'])) if p!=q]
        pairs.append({'matrix_key':ka,'permuted_key':kb,**result,'differences':differences})
        group=groups.setdefault(f'turn{turn}-cache{ka[3]}',{'pairs':0,'exact_pairs':0,'pixels':0,'exact_pixels':0,'max_channel_delta':0})
        group['pairs']+=1;group['exact_pairs']+=not differences;group['pixels']+=768;group['exact_pixels']+=result['exact'];group['max_channel_delta']=max(group['max_channel_delta'],max(result['max_channel_delta']))
    return {'source_pixels':source,'rotated_pixels':rotated,'groups':groups,'pairs':pairs,'permutation_bytes_exact':48,'quarter_turn_equivalence_admitted':all(not p['differences'] for p in pairs),'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=analyze(a.native);a.output.write_text(json.dumps(r,separators=(',',':'))+'\n');print(json.dumps(r['groups'],indent=2))
