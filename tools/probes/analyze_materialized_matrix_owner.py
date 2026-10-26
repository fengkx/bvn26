"""Compare actual copied source bytes through native filter APIs and authored boundaries."""
import argparse
from collections import defaultdict,Counter
import gzip
import hashlib
import json
from pathlib import Path
import struct
from tools.probes.analyze_matrix_component_boundaries import decode as pinned_decode
from tools.probes.run_nested_filters import unpack
from tools.probes.build_bound_bitmap_component import ROOT


def decode(native):
    build=json.loads((native/'build.json').read_text())
    for path,digest in [(build['source'],build['source_sha256']),(build['harness_source'],build['harness_sha256'])]:assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest
    path=native/'native.log';raw=path.read_text() if path.exists() else gzip.decompress(path.with_suffix('.log.gz').read_bytes()).decode()
    records=[v.split('|') for v in raw.splitlines() if v.startswith('AIREF|')];assert records[-1][6:]==['done','ok']
    images={};sizes={};clocks=[];properties={};matrices={};materials={};restores={}
    for i,row in enumerate(records):
        assert len(row)==8 and row[1]==build['run_id'] and row[2:4]==[str(i),'0'] and row[5]=='0'
        tick=int(row[4]);kind,value=row[6:];v=value.split(',')
        if kind=='clock':clocks.append({'tick':tick,'path':v[0],'frame':int(v[1])})
        elif kind=='props':assert tick not in properties;properties[tick]=v
        elif kind=='matrix':assert tick not in matrices;matrices[tick]=v
        elif kind=='material':assert tick not in materials;materials[tick]=v
        elif kind=='restore':assert tick not in restores;restores[tick]=v
        elif kind=='size':
            key=(tick,v[0]);assert key not in images;sizes[key]=list(map(int,v[1:]));images[key]=[]
        elif kind=='row':
            key=(tick,v[0]);w,h=sizes[key];pixels=images[key];assert int(v[1])==len(pixels)//w and len(v)==2+w*2
            pixels.extend(unpack(list(map(int,v[2:]))))
        else:assert [kind,value]==['done','ok']
    previous,old,_,pinned_clocks,_,_=pinned_decode(ROOT/'evidence/importer-loud-fail/r195/native/frame3')
    assert build['case']==previous['case'] and clocks==[v for v in pinned_clocks if v['tick']<=8]
    assert build['sample_ticks']==[0,8] and len(images)==10
    expected=[float(format(struct.unpack('<f',struct.pack('<f',v))[0],'.15g')) for v in build['case']['placement']['filters'][0]['matrix']]
    _,_,w,h=build['cache_allocation']
    for tick in (0,8):
        frame=1+tick;assert properties[tick][:3]==[str(frame),'true','1'] and list(map(float,properties[tick][3:]))==expected
        assert restores[tick]==[str(frame),str(frame),'true','1']
        assert materials[tick][:6]==['0',str(w),'0',str(h),'true','1'] and list(map(float,materials[tick][6:]))==expected
        for label in ('authored','cache','source','apply','display'):
            size=[600,400] if label in ('authored','cache') else [w,h]
            assert sizes[(tick,label)]==size and len(images[(tick,label)])==size[0]*size[1]
    return build,images,old,clocks,properties,matrices,materials


def comparison(actual,native,width):
    assert len(actual)==len(native);failures=[];maximum=0
    for i,(p,q) in enumerate(zip(actual,native)):
        maximum=max(maximum,max(abs(a-b) for a,b in zip(p,q)))
        if p!=q:failures.append({'x':i%width,'y':i//width,'actual':p,'native':q})
    return {'samples':len(actual),'exact':len(actual)-len(failures),'max_channel_delta':maximum,'failures':failures}


def analyze(native):
    build,images,old,clocks,props,matrices,materials=decode(native);x,y,w,h=build['cache_allocation'];rows=[];pairs={name:defaultdict(Counter) for name in ('apply','display','authored')}
    for tick in (0,8):
        crop=lambda pixels:[pixels[(y+j)*600+x+i] for j in range(h) for i in range(w)]
        source=images[(tick,'source')];cache=images[(tick,'cache')];authored=images[(tick,'authored')]
        targets={'source_copy':comparison(source,crop(cache),w),'cache_previous':comparison(cache,old[f'{tick}-cache'],600),'authored_previous':comparison(authored,old[f'{tick}-authored'],600),
                 'apply_vs_authored':comparison(images[(tick,'apply')],crop(authored),w),'display_vs_authored':comparison(images[(tick,'display')],crop(authored),w),
                 'apply_vs_display':comparison(images[(tick,'apply')],images[(tick,'display')],w)}
        for label in pairs:
            output=crop(authored) if label=='authored' else images[(tick,label)]
            for before,after in zip(source,output):pairs[label][tuple(before)][tuple(after)]+=1
        rows.append({'tick':tick,'comparisons':targets})
    groups={label:[{'input':list(before),'outputs':[{'rgba':list(after),'count':count} for after,count in sorted(outputs.items())]} for before,outputs in sorted(values.items())] for label,values in pairs.items()}
    return {'rows':rows,'input_output_groups':groups,'clocks_exact':len(clocks),'source_allocation':build['cache_allocation'],
            'properties':{str(k):v for k,v in props.items()},'matrices':{str(k):v for k,v in matrices.items()},'materialized_clip_properties':{str(k):v for k,v in materials.items()},
            'apply_source_explicit':True,'display_internal_allocation_identical_proved':False,'candidate_admitted':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=analyze(a.native)
    a.output.write_text(json.dumps(r,separators=(',',':'))+'\n')
    for row in r['rows']:print(row['tick'],{k:(v['exact'],v['samples'],v['max_channel_delta']) for k,v in row['comparisons'].items()})
    for label,groups in r['input_output_groups'].items():print(label,'ambiguous',sum(len(v['outputs'])>1 for v in groups),'inputs',len(groups))
