"""Hold original nearest geometry fixed while independently varying encoding and alpha."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import uuid
import zlib
from tools.probes.build_nearest_component_input import build as original_build
from tools.probes.build_bound_bitmap_component import ROOT, source_tags
from tools.probes.build_minimal_swf import tag
from tools.probes.inventory_bitmap_roundtrip import decode_lossless

HARNESS=Path('tools/probes/flash_filters/indexed-nearest-cache.as')


def build(output,ffdec,axis,alpha):
    assert axis in ('x','y') and alpha in ('opaque','original')
    report=original_build(output,ffdec)
    fixture=json.loads((output/'fixture.json').read_text());original=fixture['leaf']['pixels_premultiplied']
    source=[]
    for y in range(200):
        for x in range(137):
            a=255 if alpha=='opaque' else original[y*137+x][3]
            source.append(([x,0,73,a] if axis=='x' else [0,y,73,a]) if a else [0,0,0,0])
    palette=list(dict.fromkeys(map(tuple,source)));assert len(palette)<=256
    lookup={p:i for i,p in enumerate(palette)};indices=bytearray()
    for y in range(200):
        indices.extend(lookup[tuple(p)] for p in source[y*137:(y+1)*137]);indices.extend(b'\0'*3)
    payload=struct.pack('<HBHHB',281,3,137,200,len(palette)-1)+zlib.compress(bytes(c for p in palette for c in p)+indices)
    assert decode_lossless(payload)==(281,137,200,source)
    run='indexed-nearest-cache-'+uuid.uuid4().hex[:12]
    script=(ROOT/HARNESS).read_text().replace('RUN',run).replace('TRANSFORM',json.dumps(fixture['cases'][1],separators=(',',':')))
    (output/'scripts/frame_1/DoAction.as').write_text(script)
    subprocess.run(['java',f'-Duser.home={output}','-Djava.awt.headless=true','-jar',str(ffdec),'-importScript',str(output/'base.swf'),str(output/'game/main.swf'),str(output/'scripts')],check=True,stdout=subprocess.DEVNULL)
    path=output/'game/main.swf';before=path.read_bytes();body=before[8:] if before[:3]==b'FWS' else zlib.decompress(before[8:]);offset=(5+4*(body[0]>>3)+7)//8+4
    records=list(source_tags(path));targets=[i for i,(code,p,_) in enumerate(records) if code==36 and struct.unpack_from('<H',p)[0]==281];assert len(targets)==1;target=targets[0]
    changed=body[:offset]+b''.join(tag(36,payload) if i==target else record[2] for i,record in enumerate(records));path.write_bytes(b'FWS'+before[3:4]+struct.pack('<I',len(changed)+8)+changed)
    after=list(source_tags(path));assert [r[2] for i,r in enumerate(after) if i!=target]==[r[2] for i,r in enumerate(records) if i!=target]
    fixture['synthetic_source']={'axis':axis,'alpha':alpha,'pixels_premultiplied':source,'palette':palette,'format':3,'unchanged_other_tags':len(records)-1}
    (output/'fixture.json').write_text(json.dumps(fixture,separators=(',',':'))+'\n')
    report.update({'run_id':run,'raw_tags_preserved':False,'shape_and_other_tags_preserved':True,'synthetic_bitmap':281,
                   'harness_source':str(HARNESS),'harness_sha256':hashlib.sha256((ROOT/HARNESS).read_bytes()).hexdigest(),
                   'builder_source':str(Path(__file__).resolve().relative_to(ROOT)),'builder_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                   'fixture_sha256':hashlib.sha256((output/'fixture.json').read_bytes()).hexdigest(),
                   'outputs_sha256':{'game/main.swf':hashlib.sha256(path.read_bytes()).hexdigest()}})
    (output/'build.json').write_text(json.dumps(report,indent=2)+'\n');return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--ffdec',type=Path,required=True);a=p.parse_args()
    for axis in ('x','y'):
        for alpha in ('opaque','original'):
            folder=a.output.resolve()/(axis+'-'+alpha);build(folder,a.ffdec.resolve(),axis,alpha);print(folder,flush=True)
