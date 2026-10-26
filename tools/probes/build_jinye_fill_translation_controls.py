"""Patch only parsed active-fill translation bits and independently vary draw operands."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import struct
import subprocess
import uuid
import zlib
from tools.probes.build_bound_bitmap_component import ROOT,source_tags
from tools.probes.build_minimal_swf import rect,tag
from tools.probes.build_jinye_sampling_modes import controls as base_controls,source_pixel

HARNESS=Path('tools/probes/flash_filters/jinye-fill-translation-controls.as')


def translation_fields(payload):
    pos=16
    def read(n,signed=False):
        nonlocal pos
        assert pos+n<=len(payload)*8
        result=0
        for _ in range(n):result=(result<<1)|((payload[pos//8]>>(7-pos%8))&1);pos+=1
        return result-(1<<n) if signed and n and result&(1<<(n-1)) else result
    width=read(5);read(width*4);pos=(pos+7)//8*8
    assert read(8)==2;styles=[]
    for _ in range(2):
        offset=pos//8;kind=read(8);assert kind in (65,67)
        low=read(8);bitmap=low+256*read(8)
        if read(1):width=read(5);read(2*width)
        if read(1):width=read(5);read(2*width)
        width=read(5);fields=[]
        for axis in range(2):
            start=pos;value=read(width,True);fields.append({'bit':start,'width':width,'value':value})
        pos=(pos+7)//8*8;styles.append({'mode_byte':offset,'type':kind,'bitmap':bitmap,'translations':fields})
    assert [s['bitmap'] for s in styles]==[65535,55]
    return styles


def changed_tag(payload,raw,axis,delta):
    before=translation_fields(payload);active=before[1];assert active['type']==65
    header=6 if struct.unpack_from('<H',raw)[0]&63==63 else 2;assert raw[header:]==payload
    out=bytearray(raw);out[header+active['mode_byte']]=67
    allowed={8*(header+active['mode_byte'])+6}
    if axis is not None:
        field=active['translations'][axis];width=field['width'];value=field['value']+delta
        assert -(1<<(width-1))<=value<(1<<(width-1))
        encoded=value&((1<<width)-1);start=header*8+field['bit']
        allowed.update(range(start,start+width))
        for i in range(width):
            bit=start+i;mask=1<<(7-bit%8)
            out[bit//8]=(out[bit//8]&~mask)|(((encoded>>(width-1-i))&1)<<(7-bit%8))
    else:assert delta==0
    after=translation_fields(out[header:]);expected=json.loads(json.dumps(before));expected[1]['type']=67
    if axis is not None:expected[1]['translations'][axis]['value']+=delta
    assert after==expected
    changed=[i for i in range(len(raw)*8) if (raw[i//8]>>(7-i%8))&1 != (out[i//8]>>(7-i%8))&1]
    assert set(changed)<=allowed
    return bytes(out),{'header_bytes':header,'before':before,'after':after,'allowed_changed_bits':sorted(allowed),'changed_bits':changed}


def controls():
    graph,bases,_=base_controls();shapes={s['id']:s for s in graph['shapes']}
    variants=[{'id':0,'axis':None,'delta':0}]+[{'id':1+axis*6+i,'axis':axis,'delta':delta} for axis in (0,1) for i,delta in enumerate((-20,-10,-1,1,10,20))]
    draw_controls=[None]+[{'axis':axis,'offset':offset} for axis in (0,1) for offset in (-1/64,0,1/64,15/64,16/64,17/64)]
    cases=[]
    for variant in variants:
        for base in bases:
            fill_matrix=shapes[base['shape']]['bitmap_matrix'].copy();fill=base['fill'].copy()
            if variant['axis'] is not None:
                axis=variant['axis'];name=('translateX','translateY')[axis]
                fill_matrix[name]=str(int(fill_matrix[name])+variant['delta']);fill[4+axis]+=variant['delta']/20
            for draw_id,draw_control in enumerate(draw_controls if variant['id']==0 else [None]):
                draw=base['draw'].copy();quarter=None
                if draw_control is not None:
                    axis=draw_control['axis'];quarter=math.floor(draw[4+axis]*4)/4;draw[4+axis]=quarter+draw_control['offset']
                cases.append({**base,'id':len(cases),'baseline_id':base['id'],'fill_variant':variant['id'],
                              'fill_axis':variant['axis'],'fill_delta':variant['delta'],'fill_matrix':fill_matrix,'fill':fill,
                              'draw_variant':draw_id,'draw_control':draw_control,'quarter_origin':quarter,'draw':draw})
    assert len(cases)==100
    return graph,cases,variants


def build(output,ffdec):
    output=output.resolve()
    if any(p==output or p in output.parents for p in (ROOT/'game',ROOT/'scripts')):raise ValueError('Locked input output path')
    graph,cases,variants=controls();source=ROOT/graph['source']['path'];assert hashlib.sha256(source.read_bytes()).hexdigest()==graph['source']['sha256']
    raw={struct.unpack_from('<H',p)[0]:(p,r) for code,p,r in source_tags(source) if code==2 and struct.unpack_from('<H',p)[0] in (56,57)}
    assert set(raw)=={56,57} and all(hashlib.sha256(r).hexdigest()==graph['raw_tag_sha256'][str(cid)] for cid,(_,r) in raw.items())
    output.mkdir(parents=True,exist_ok=True);fixture={'cases':cases,'variants':variants,'source_graph':graph,'size':[96,96],'source_size':[92,40],'production_admitted':False}
    (output/'fixture.json').write_text(json.dumps(fixture,indent=2)+'\n')
    rgba=[source_pixel(x,y) for y in range(40) for x in range(92)]
    payload=struct.pack('<HBHH',55,5,92,40)+zlib.compress(bytes(c for r,g,b,a in rgba for c in (a,r,g,b)))
    bitmap=struct.pack('<HI',(36<<6)|63,len(payload))+payload;reports=[]
    for variant in variants:
        folder=output/f"fill{variant['id']}";(folder/'game').mkdir(parents=True,exist_ok=True);(folder/'scripts/frame_1').mkdir(parents=True,exist_ok=True)
        shapes={};changes={};wrappers=[];exports=struct.pack('<H',3)+struct.pack('<H',55)+b'sourceBitmap\0'
        for cid,(p,r) in raw.items():shapes[cid],changes[str(cid)]=changed_tag(p,r,variant['axis'],variant['delta'])
        for spec in (c for c in cases if c['fill_variant']==variant['id']):
            fields=changes[str(spec['shape'])]['after'][1]['translations']
            assert [int(spec['fill_matrix'][k]) for k in ('translateX','translateY')]==[field['value'] for field in fields]
        for cid in (56,57):
            wid=60000+cid-56;wrappers.append(tag(39,struct.pack('<HH',wid,1)+tag(26,b'\x06'+struct.pack('<HH',1,cid)+b'\0')+tag(1)+tag(0)))
            exports+=struct.pack('<H',wid)+f'leaf{cid}'.encode()+b'\0'
        body=rect(0,1920,0,1920)+struct.pack('<HH',30*256,1)+bitmap+shapes[56]+shapes[57]+b''.join(wrappers)+tag(56,exports)+tag(12,b'\0')+tag(1)+tag(0)
        (folder/'base.swf').write_bytes(b'FWS'+bytes([8])+struct.pack('<I',len(body)+8)+body)
        subset=[c for c in cases if c['fill_variant']==variant['id']];run='jinye-fill-shift-'+uuid.uuid4().hex[:12]
        script=(ROOT/HARNESS).read_text().replace('RUN',run).replace('CLIPS','[null]').replace('CASES',re.sub(r'"([A-Za-z_]+)":',r'\1:',json.dumps([{k:c[k] for k in ('id','shape','matrix','outer','draw')} for c in subset],separators=(',',':'))))
        (folder/'scripts/frame_1/DoAction.as').write_text(script)
        subprocess.run(['java',f'-Duser.home={folder}','-Djava.awt.headless=true','-jar',str(ffdec),'-importScript',str(folder/'base.swf'),str(folder/'game/main.swf'),str(folder/'scripts')],check=True,stdout=subprocess.DEVNULL)
        after={struct.unpack_from('<H',p)[0]:r for code,p,r in source_tags(folder/'game/main.swf') if code in (2,36) and struct.unpack_from('<H',p)[0] in (55,56,57)}
        assert after=={55:bitmap,**shapes}
        report={'run_id':run,'variant':variant,'case_ids':[c['id'] for c in subset],'source_graph':graph['source'],'changes':changes,
                'original_shape_sha256':{str(cid):hashlib.sha256(r).hexdigest() for cid,(_,r) in raw.items()},'shape_sha256':{str(cid):hashlib.sha256(r).hexdigest() for cid,r in shapes.items()},
                'lossless_tag_sha256':hashlib.sha256(bitmap).hexdigest(),'input_rgba_sha256':hashlib.sha256(bytes(c for p in rgba for c in p)).hexdigest(),
                'harness_source':str(HARNESS),'harness_sha256':hashlib.sha256((ROOT/HARNESS).read_bytes()).hexdigest(),'fixture_sha256':hashlib.sha256((output/'fixture.json').read_bytes()).hexdigest(),
                'ffdec_sha256':hashlib.sha256(ffdec.read_bytes()).hexdigest(),'swf_sha256':hashlib.sha256((folder/'game/main.swf').read_bytes()).hexdigest(),'production_admitted':False}
        (folder/'build.json').write_text(json.dumps(report,indent=2)+'\n');reports.append(report)
    return reports


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--ffdec',type=Path,required=True);a=p.parse_args();print(len(build(a.output,a.ffdec.resolve())))
