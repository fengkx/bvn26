"""Capture the original Jiraiya shape/bitmap at fractional axis transforms."""
import argparse
import hashlib
import json
import re
from pathlib import Path
import struct
import subprocess
import uuid
import xml.etree.ElementTree as ET
from tools.probes.build_bound_bitmap_component import ROOT, source_tags, bitmap_shape_fill_polygons, rect, tag
from tools.probes.inventory_bitmap_roundtrip import decode_lossless

SOURCE = 'game/fighter/jiraiya.swf'


def build(output, ffdec):
    output=output.resolve()
    if any(p==output or p in output.parents for p in (ROOT/'game',ROOT/'scripts')):
        raise ValueError('Locked inputs cannot be probe output')
    output.mkdir(parents=True,exist_ok=True)
    xml=output/'source.xml'
    subprocess.run(['java',f'-Duser.home={output}','-Djava.awt.headless=true','-jar',str(ffdec),'-swf2xml',str(ROOT/SOURCE),str(xml)],check=True,stdout=subprocess.DEVNULL)
    tags=ET.parse(xml).getroot().find('tags')
    shape=next(t for t in tags if t.get('shapeId')=='274')
    fills=shape.findall('.//fillStyles/item');assert len(fills)==1
    fill=fills[0];matrix=fill.find('bitmapMatrix')
    assert fill.get('fillStyleType')=='65' and fill.get('bitmapId')=='273'
    assert float(matrix.get('scaleX'))==20 and float(matrix.get('scaleY'))==20
    assert float(matrix.get('translateX'))==0 and float(matrix.get('translateY'))==16
    assert not shape.findall('.//lineStyles/item')
    masks=bitmap_shape_fill_polygons(shape)
    assert masks is not None and len(masks)==1 and len(masks[0])==1
    assert set(map(tuple,masks[0][0]))=={(0,0.8),(60,0.8),(60,58.8),(0,58.8)}
    raw={struct.unpack_from('<H',p)[0]:(p,r) for c,p,r in source_tags(ROOT/SOURCE) if c in (2,36) and struct.unpack_from('<H',p)[0] in (273,274)}
    _,width,height,pixels=decode_lossless(raw[273][0]);assert (width,height)==(60,58)
    timeline=json.loads((ROOT/'godot/generated/fighters/jiraiya/timeline.json').read_text())
    digest=hashlib.sha256((ROOT/SOURCE).read_bytes()).hexdigest();assert timeline['source_swf']['sha256']==digest
    case=next(c for c in json.loads((ROOT/'evidence/importer-loud-fail/r21/components/jiraiya/cases.json').read_text()) if c['symbol']==275)
    m=case['placement']['matrix']
    sx=round(m['scaleX']*65536)/65536;sy=round(m['scaleY']*65536)/65536
    cases=[{'sx':1,'sy':1,'tx':4,'ty':4},{'sx':1,'sy':1,'tx':4,'ty':3.2},
           {'sx':1,'sy':1,'tx':4.25,'ty':4.2},{'sx':sx,'sy':sy,'tx':4,'ty':4},
           {'sx':sx,'sy':sy,'tx':4.25,'ty':4.5},
           {'sx':sx,'sy':sy,'tx':case['normalization']['x']+m['translateX']/20,
            'ty':case['normalization']['y']+m['translateY']/20}]
    fixture={'source':SOURCE,'source_sha256':digest,'shape_id':274,'bitmap_id':273,'width':width,'height':height,
             'pixels_premultiplied':pixels,'fill_masks':masks,'fill':dict(fill.attrib),'fill_matrix':dict(matrix.attrib),
             'raw_tag_sha256':{str(k):hashlib.sha256(r).hexdigest() for k,(_,r) in raw.items()},
             'cases':cases,'target_size':[384,256],'production_admitted':False}
    (output/'fixture.json').write_text(json.dumps(fixture,indent=2)+'\n')
    (output/'shape.xml').write_text(ET.tostring(shape,encoding='unicode')+'\n')
    run='jiraiya-bitmap-r89-'+uuid.uuid4().hex[:12]
    script='''stop();var seq=0;
function emit(k,v){trace("AIREF|RUN|"+(seq++)+"|0|0|0|"+k+"|"+v);}
var mc=_root.attachMovie("leaf","leaf",1);var cases=CASES;
for(var i=0;i<cases.length;i++){var c=cases[i];var matrix=new flash.geom.Matrix(c.sx,0,0,c.sy,c.tx,c.ty);
 emit("case",[i,matrix.a,matrix.d,matrix.tx,matrix.ty].join(","));
 var b=new flash.display.BitmapData(384,256,true,0);b.draw(mc,matrix);
 var black=new flash.display.BitmapData(384,256,false,0);black.draw(b);
 for(var y=0;y<256;y++){var row=[];for(var x=0;x<384;x++)row.push(b.getPixel32(x,y),black.getPixel32(x,y));emit("row",i+","+y+","+row.join(","));}
 b.dispose();black.dispose();}
emit("done","ok");fscommand("quit");
'''.replace('RUN',run).replace('CASES',re.sub(r'"([a-z_]+)":',r'\1:',json.dumps(cases)))
    (output/'scripts/frame_1').mkdir(parents=True,exist_ok=True);(output/'game').mkdir(exist_ok=True)
    (output/'scripts/frame_1/DoAction.as').write_text(script)
    wrapper=struct.pack('<HH',60000,1)+tag(26,b'\x06'+struct.pack('<HH',1,274)+b'\0')+tag(1)+tag(0)
    body=rect(0,7680,0,5120)+struct.pack('<HH',30*256,1)+raw[273][1]+raw[274][1]+tag(39,wrapper)+tag(56,struct.pack('<HH',1,60000)+b'leaf\0')+tag(12,b'\0')+tag(1)+tag(0)
    (output/'base.swf').write_bytes(b'FWS'+bytes([8])+struct.pack('<I',len(body)+8)+body)
    subprocess.run(['java',f'-Duser.home={output}','-Djava.awt.headless=true','-jar',str(ffdec),'-importScript',str(output/'base.swf'),str(output/'game/main.swf'),str(output/'scripts')],check=True,stdout=subprocess.DEVNULL)
    after={struct.unpack_from('<H',p)[0]:r for c,p,r in source_tags(output/'game/main.swf') if c in (2,36) and struct.unpack_from('<H',p)[0] in (273,274)}
    assert all(after[k]==r for k,(_,r) in raw.items())
    report={'run_id':run,'source':SOURCE,'source_sha256':digest,'raw_tags_preserved':True,
            'fixture_sha256':hashlib.sha256((output/'fixture.json').read_bytes()).hexdigest(),
            'outputs_sha256':{'game/main.swf':hashlib.sha256((output/'game/main.swf').read_bytes()).hexdigest()},
            'ffdec_sha256':hashlib.sha256(ffdec.read_bytes()).hexdigest()}
    (output/'build.json').write_text(json.dumps(report,indent=2)+'\n');return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--ffdec',type=Path,required=True)
    args=p.parse_args();print(json.dumps(build(args.output,args.ffdec),indent=2))
