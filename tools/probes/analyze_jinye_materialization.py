"""Measure source-local raster boundaries without admitting explicit cache equivalence."""
import argparse
from fractions import Fraction as Q
import gzip
import hashlib
import json
from pathlib import Path
from tools.probes.build_bound_bitmap_component import ROOT
from tools.probes.analyze_bitmap_cache_support_local import events as old_events
from tools.probes.run_nested_filters import unpack
from tools.probes.analyze_jinye_leaf_boundaries import decode as old_leaf
from tools.probes.run_jinye_wrapper_cpu import render_leaf,save,coverage
from tools.probes.jinye_jpeg_source import decode as decode_source
from tools.probes.run_nearest_matrix_family import measure
from tools.probes.build_jinye_materialization import allocation_for


def decode(native):
    fixture=json.loads((native/'fixture.json').read_text());build=json.loads((native/'build.json').read_text())
    assert hashlib.sha256((native/'fixture.json').read_bytes()).hexdigest()==build['fixture_sha256']
    assert hashlib.sha256((ROOT/build['harness_source']).read_bytes()).hexdigest()==build['harness_sha256']
    assert hashlib.sha256((ROOT/fixture['source']['path']).read_bytes()).hexdigest()==fixture['source']['sha256']
    path=native/'native.log';text=path.read_text() if path.exists() else gzip.decompress(path.with_suffix('.log.gz').read_bytes()).decode()
    records=[line.split('|') for line in text.splitlines() if line.startswith('AIREF|')];assert len(records)==1843 and records[-1][6:]==['done','ok']
    old_fixture,_,old_matrices=old_leaf(ROOT/'evidence/importer-loud-fail/r221/native')
    assert fixture['cases']==old_fixture['cases'][:1] and fixture['shapes']==old_fixture['shapes']
    assert fixture['raw_tag_sha256']==old_fixture['raw_tag_sha256'] and fixture['source']==old_fixture['source']
    expected_bounds,polygon=allocation_for(fixture['cases'][0],next(s for s in fixture['shapes'] if s['id']==56))
    assert fixture['local_allocation']==expected_bounds and fixture['local_polygon']==[[str(v) for v in p] for p in polygon]
    x,y,w,h=fixture['local_allocation'];spec=fixture['cases'][0]
    labels=['source','0-direct','0-local','0-materialized','1-direct','1-local','1-materialized'];images={};matrices=[];props=[];allocations=[];seconds=[];active=None
    for i,event in enumerate(records):
        assert event[1]==build['run_id'] and event[2:6]==[str(i),'0','0','0'];kind,payload=event[6:];v=payload.split(',')
        if kind=='image':
            if active is not None:assert len(active['pixels'])==active['size'][0]*active['size'][1]
            label=v[0];assert label==labels[len(images)] and v[3]=='true'
            size=[92,40] if label=='source' else [w,h] if label.endswith('-local') else [600,400]
            assert list(map(int,v[1:3]))==size
            active={'size':size,'pixels':[],'raw':[]};images[label]=active
        elif kind=='row':
            assert active is not None;ww,hh=active['size'];yy=int(v[0]);assert len(v)==1+2*ww and len(active['pixels'])==yy*ww and 0<=yy<hh
            words=list(map(int,v[1:]));assert all(-(1<<31)<=n<(1<<32) for n in words)
            active['pixels'].extend(unpack(words));active['raw'].extend([[(p>>s)&255 for s in (16,8,0,24)] for p in words[::2]])
        elif kind=='matrix':
            assert not matrices and len(v)==22;actual=list(map(float,v));assert actual[:18]==[float(format(n,'.15g')) for n in spec['matrix']+spec['outer']+spec['draw']];assert actual[18:]==old_matrices[0][19:];matrices.append(actual)
        elif kind=='props':assert v==[str(len(props)),'true' if len(props) else 'false','0','1'];props.append(v)
        elif kind=='allocation':
            assert int(v[0])==len(allocations) and list(map(int,v[1:5]))==[x,y,w,h]
            local=spec['matrix'].copy();local[4]-=x;local[5]-=y
            assert list(map(float,v[5:]))==[float(format(n,'.15g')) for n in local];allocations.append(list(map(float,v)))
        elif kind=='second':
            assert v[:2]==[str(len(seconds)),'true' if len(seconds) else 'false'];values=list(map(float,v[2:]));assert len(values)==16
            assert values[:12]==[1,0,0,1,x,y]+spec['outer'];assert values[12:]==[x,y,x+w,y+h];seconds.append(v)
        else:assert kind=='done'
    assert list(images)==labels and len(props)==len(allocations)==len(seconds)==2
    assert all(len(im['pixels'])==im['size'][0]*im['size'][1] for im in images.values())
    old=old_events(ROOT/'evidence/importer-loud-fail/r220/jpeg/native');source=[]
    for kind,data in old[1:-1]:assert kind=='row';source.extend(unpack(list(map(int,data.split(',')[1:]))))
    assert images['source']['pixels']==source and len(source)==3680
    return fixture,images,{'matrix':matrices,'properties':props,'allocation':allocations,'materialized_properties':seconds}


def run(native,dump,output):
    output.mkdir(parents=True,exist_ok=True);fixture,images,readbacks=decode(native)
    _,old,_=old_leaf(ROOT/'evidence/importer-loud-fail/r221/native');baseline=[]
    old_path=ROOT/'evidence/importer-loud-fail/r221/native/native.log.gz';old_rows=gzip.decompress(old_path.read_bytes()).decode().splitlines();raw_baselines=[]
    for line in old_rows:
        parts=line.split('|')
        if len(parts)!=8 or parts[0]!='AIREF':continue
        if parts[6]=='case':raw_baselines.append([])
        elif parts[6]=='row':
            values=list(map(int,parts[7].split(',')))[1:]
            raw_baselines[-1].extend([[(v>>s)&255 for s in (16,8,0,24)] for v in values[::2]])
    for mode in (0,1):
        row=measure(images[f'{mode}-direct']['pixels'],old[mode]['pixels'],600);assert not row['failures']
        raw=measure(images[f'{mode}-direct']['raw'],raw_baselines[mode],600);assert not raw['failures'];row['raw_rgba']=raw;baseline.append(row)
    metadata,source=decode_source(dump,output/'decoded');assert source==images['source']['pixels']
    pinned=json.loads((ROOT/'evidence/importer-loud-fail/r220/jpeg/analysis/summary.json').read_text());assert metadata['plane_sha256']==pinned['bitmap']['plane_sha256']
    spec=fixture['cases'][0];shape=next(s for s in fixture['shapes'] if s['id']==56);x,y,w,h=fixture['local_allocation']
    local_spec={**spec,'outer':[1,0,0,1,0,0],'draw':[1,0,0,1,-x,-y]}
    candidate,geometry=render_leaf(source,local_spec,shape,(w,h));save(output/'source-local-candidate.png',candidate,(w,h))
    rows=[]
    for mode in (0,1):
        target=images[f'{mode}-local']['pixels'];measurement=measure(candidate,target,w)
        polygon=[list(map(Q,p)) for p in geometry['polygon']]
        from tools.probes.analyze_jinye_smooth_leaf import inside
        partitions={'interior':[],'edge':[],'outside':[]}
        for i,(a,b) in enumerate(zip(candidate,target)):
            xx,yy=i%w,i//w
            interior=all(inside(p,polygon) for p in ((xx,yy),(xx+1,yy),(xx+1,yy+1),(xx,yy+1)))
            key='interior' if interior else 'edge' if coverage(polygon,xx,yy)>0 else 'outside'
            partitions[key].append((a,b))
        stats={key:{'samples':len(v),'exact':sum(a==b for a,b in v),'changed_nonzero_alpha':sum(a!=b and bool(a[3] or b[3]) for a,b in v)} for key,v in partitions.items()}
        rows.append({'cached':bool(mode),'candidate_local':measurement,'geometry_partition':stats,
                     'native_direct_vs_materialized':measure(images[f'{mode}-materialized']['pixels'],images[f'{mode}-direct']['pixels'],600)})
    result={'direct_baselines':baseline,'source_decoder':metadata,'source_readbacks_exact':3680,'local_allocation':fixture['local_allocation'],
            'readbacks':readbacks,'local_geometry':geometry,'rows':rows,'native_local_cache_pair':measure(images['0-local']['pixels'],images['1-local']['pixels'],w),
            'materialization_equals_native_cache':False,'candidate_admitted':False,'gpu_advance_allowed':False,'production_admitted':False}
    (output/'report.json').write_text(json.dumps(result,separators=(',',':'))+'\n');return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--dump',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=run(a.native,a.dump.resolve(),a.output);print([(x['candidate_local']['exact'],x['candidate_local']['samples'],x['candidate_local']['max_channel_delta']) for x in r['rows']]);raise SystemExit(1)
