"""Expand enclosing source ShapeBounds without altering any fill or mask bytes."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import uuid
import zlib
from tools.probes.build_bound_bitmap_component import ROOT
from tools.probes.build_minimal_swf import rect,tag
from tools.probes.build_jinye_source_factorization import controls as old_controls
from tools.probes.build_jinye_sampling_modes import source_pixel
from tools.probes.jinye_source_factorization_tags import parse
from tools.probes.jinye_factorization_tags import Reader

HARNESS=Path('tools/probes/flash_filters/jinye-bounds-controls.as')


def expand(raw,side,amount):
    parsed=parse(raw);reader=Reader(raw[6:]);reader.ui16();width=reader.bits(5);fields=[]
    for _ in range(4):
        bit=48+reader.pos;value=reader.bits(width,True);fields.append({'bit':bit,'width':width,'value':value})
    assert [f['value'] for f in fields]==parsed['bounds_twips']
    result=bytearray(raw);allowed=[];bounds=parsed['bounds_twips'].copy()
    if side is not None:
        assert side in range(4) and amount>0
        delta=-amount if side in (0,2) else amount;bounds[side]+=delta;field=fields[side]
        assert -(1<<(width-1))<=bounds[side]<(1<<(width-1))
        encoded=bounds[side]&((1<<width)-1);allowed=list(range(field['bit'],field['bit']+width))
        for i,bit in enumerate(allowed):
            mask=1<<(7-bit%8);result[bit//8]=(result[bit//8]&~mask)|(((encoded>>(width-1-i))&1)<<(7-bit%8))
    else:assert amount==0
    changed=[i for i in range(len(raw)*8) if ((raw[i//8]^result[i//8])>>(7-i%8))&1]
    assert set(changed)<=set(allowed) and len(result)==len(raw)
    assert bounds[0]<=parsed['bounds_twips'][0] and bounds[1]>=parsed['bounds_twips'][1] and bounds[2]<=parsed['bounds_twips'][2] and bounds[3]>=parsed['bounds_twips'][3]
    return bytes(result),{'side':side,'amount_twips':amount,'fields':fields,'before':parsed['bounds_twips'],'after':bounds,'allowed_changed_bits':allowed,'changed_bits':changed}


def controls():
    old=old_controls();bases=[old['cases'][6],old['cases'][18]]
    shapes=[s for s in old['shapes'] if s['factor_id']==-1]
    variants=[{'id':0,'side':None,'amount':0}]+[{'id':1+side*3+i,'side':side,'amount':amount} for side in range(4) for i,amount in enumerate((1,20,80))]
    cases=[];tags={}
    for v in variants:
        tags[v['id']]={}
        for base in bases:
            shape=next(s for s in shapes if s['source_shape']==base['source_shape'])
            raw,proof=expand(bytes.fromhex(shape['raw_tag_hex']),v['side'],v['amount'])
            tags[v['id']][base['shape']]=raw
            cases.append({**base,'id':len(cases),'baseline_case':base['id'],'variant':v['id'],'bounds_patch':proof,'raw_tag_sha256':hashlib.sha256(raw).hexdigest()})
    return {'cases':cases,'variants':variants,'shapes':shapes,'source_graph':old['source_graph'],'source_size':[92,40],'size':[256,256],'production_admitted':False},tags


def build(output,ffdec):
    output=output.resolve()
    if any(p==output or p in output.parents for p in (ROOT/'game',ROOT/'scripts')):raise ValueError('Locked input output path')
    fixture,tags=controls();output.mkdir(parents=True,exist_ok=True);(output/'fixture.json').write_text(json.dumps(fixture,indent=2)+'\n')
    rgba=[source_pixel(x,y) for y in range(40) for x in range(92)]
    payload=struct.pack('<HBHH',55,5,92,40)+zlib.compress(bytes(c for r,g,b,a in rgba for c in (a,r,g,b)))
    bitmap=struct.pack('<HI',(36<<6)|63,len(payload))+payload;reports=[]
    for variant in fixture['variants']:
        folder=output/f"bounds{variant['id']}";(folder/'game').mkdir(parents=True,exist_ok=True);(folder/'scripts/frame_1').mkdir(parents=True,exist_ok=True)
        shapes=tags[variant['id']];wrappers=[];exports=struct.pack('<H',3)+struct.pack('<H',55)+b'sourceBitmap\0'
        for cid in shapes:
            wid=60000+cid-56;wrappers.append(tag(39,struct.pack('<HH',wid,1)+tag(26,b'\x06'+struct.pack('<HH',1,cid)+b'\0')+tag(1)+tag(0)))
            exports+=struct.pack('<H',wid)+f'leaf{cid}'.encode()+b'\0'
        body=rect(0,5120,0,5120)+struct.pack('<HH',30*256,1)+bitmap+b''.join(shapes.values())+b''.join(wrappers)+tag(56,exports)+tag(12,b'\0')+tag(1)+tag(0)
        (folder/'base.swf').write_bytes(b'FWS'+bytes([8])+struct.pack('<I',len(body)+8)+body)
        run='jinye-bounds-'+uuid.uuid4().hex[:12];subset=[c for c in fixture['cases'] if c['variant']==variant['id']]
        runtime=[{k:c[k] for k in ('id','shape','matrix','outer','draw')} for c in subset]
        script=(ROOT/HARNESS).read_text().replace('RUN',run).replace('CLIPS','[null]').replace('CASES',re.sub(r'"([A-Za-z_]+)":',r'\1:',json.dumps(runtime,separators=(',',':'))))
        (folder/'scripts/frame_1/DoAction.as').write_text(script)
        subprocess.run(['java',f'-Duser.home={folder}','-Djava.awt.headless=true','-jar',str(ffdec),'-importScript',str(folder/'base.swf'),str(folder/'game/main.swf'),str(folder/'scripts')],check=True,stdout=subprocess.DEVNULL)
        from tools.probes.build_bound_bitmap_component import source_tags
        after={struct.unpack_from('<H',p)[0]:r for code,p,r in source_tags(folder/'game/main.swf') if code in (2,36) and struct.unpack_from('<H',p)[0] in (55,56,57)}
        assert after=={55:bitmap,**shapes}
        report={'run_id':run,'variant':variant['id'],'case_ids':[c['id'] for c in subset],'fixture_sha256':hashlib.sha256((output/'fixture.json').read_bytes()).hexdigest(),
                'raw_tags_unchanged_by_import':True,'shape_sha256':{str(cid):hashlib.sha256(raw).hexdigest() for cid,raw in shapes.items()},
                'lossless_tag_sha256':hashlib.sha256(bitmap).hexdigest(),'input_rgba_sha256':hashlib.sha256(bytes(c for p in rgba for c in p)).hexdigest(),
                'harness_source':str(HARNESS),'harness_sha256':hashlib.sha256((ROOT/HARNESS).read_bytes()).hexdigest(),
                'ffdec_sha256':hashlib.sha256(ffdec.read_bytes()).hexdigest(),'swf_sha256':hashlib.sha256((folder/'game/main.swf').read_bytes()).hexdigest(),'production_admitted':False}
        (folder/'build.json').write_text(json.dumps(report,indent=2)+'\n');reports.append(report)
    return reports


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--ffdec',type=Path,required=True);a=p.parse_args();print(len(build(a.output,a.ffdec.resolve())))
