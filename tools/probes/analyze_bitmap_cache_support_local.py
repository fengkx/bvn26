"""Read consumed local geometry independently before applying the unchanged support rule."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
from tools.probes.analyze_bitmap_cache_support_grid import ROOT,separate_bounds
from tools.probes.analyze_bitmap_cache_support_heldout import analyze as heldout


def events(native):
    build=json.loads((native/'build.json').read_text())
    assert hashlib.sha256((ROOT/build['source']).read_bytes()).hexdigest()==build['source_sha256']
    path=native/'native.log'
    text=path.read_text() if path.exists() else gzip.decompress(path.with_suffix('.log.gz').read_bytes()).decode()
    result=[]
    for line in text.splitlines():
        if not line.startswith('AIREF|'):continue
        row=line.split('|');assert row[1]==build['run_id'] and row[2:6]==[str(len(result)),'0','0','0']
        result.append(row[6:])
    assert result[-1]==['done','ok']
    return result


def analyze(native):
    old=ROOT/'evidence/importer-loud-fail/r117/native';reference=heldout(old)
    original=events(old);fresh=events(native)
    assert len(fresh)==4329
    assert [r for r in fresh if r[0]!='local']==original
    local=[list(map(float,r[1].split(','))) for r in fresh if r[0]=='local'];assert len(local)==960
    bounds=[];consumption=[]
    for c,v in zip(reference['cases'],local):
        i,minimum,width,scale,inner,outer,state,*_=c['key']
        assert v[0]==i and v[1]==minimum and v[5:]==[0,8]
        predicted_local=[math.trunc(minimum*20)/20,math.trunc((minimum+width)*20)/20]
        consumption.append({'case':int(i),'predicted':predicted_local,'native':v[3:5],'exact':predicted_local==v[3:5]})
        if state:
            predicted=separate_bounds(v[3],v[4]-v[3],scale,inner,outer)
            bounds.append({'case':int(i),'predicted':predicted,'native':c['support'],'exact':predicted==c['support']})
    return {'local_readbacks':local,'consumption':consumption,'bounds':bounds,
            'unchanged_native_event_count':len(original),'unchanged_row_pixels':960*800,
            'source_cache_initializer_admitted':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=analyze(a.native);a.output.write_text(json.dumps(r,separators=(',',':'))+'\n')
    for name in ('consumption','bounds'):print(name,sum(v['exact'] for v in r[name]),len(r[name]))
