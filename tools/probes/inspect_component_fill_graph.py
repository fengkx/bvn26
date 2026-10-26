"""Retain complete source fill slots and prove edge ownership before widening a sampler."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import xml.etree.ElementTree as ET
from tools.probes.build_bound_bitmap_component import ROOT,source_tags,bitmap_shape_fill_polygons
from tools.probes.inventory_bitmap_roundtrip import decode_lossless


def inspect(cases_path,case_id,output,ffdec):
    output=output.resolve()
    if any(p==output or p in output.parents for p in (ROOT/'game',ROOT/'scripts')):raise ValueError('Locked input output path')
    matches=[c for c in json.loads(cases_path.read_text()) if c['id']==case_id];assert len(matches)==1;case=matches[0]
    source=ROOT/case['source']['path'];assert hashlib.sha256(source.read_bytes()).hexdigest()==case['source']['sha256']
    output.mkdir(parents=True,exist_ok=True);xml=output/'source.xml'
    command=['java',f'-Duser.home={output}','-Djava.awt.headless=true','-jar',str(ffdec),'-swf2xml',str(source),str(xml)]
    subprocess.run(command,check=True,stdout=subprocess.DEVNULL)
    tags=ET.parse(xml).getroot().find('tags');wrapper=next(t for t in tags if t.get('spriteId')==str(case['symbol']))
    placements=wrapper.findall('./subTags/item[@type="PlaceObject2Tag"]');assert len(placements)==1
    shape_id=int(placements[0].get('characterId'));shape=next(t for t in tags if t.get('shapeId')==str(shape_id))
    styles=shape.findall('./shapes/fillStyles/fillStyles/item');counts=[0]*len(styles);active=[0,0];records=[]
    for node in shape.findall('./shapes/shapeRecords/item'):
        record=dict(node.attrib);records.append(record);kind=record['type']
        if kind=='StyleChangeRecord':
            if record.get('stateNewStyles')=='true':raise ValueError('Unproven dynamic style table')
            for i in range(2):
                if record.get('stateFillStyle'+str(i))=='true':active[i]=int(record['fillStyle'+str(i)])
            assert all(0<=v<=len(styles) for v in active)
        elif kind=='StraightEdgeRecord':
            for style in active:
                if style:counts[style-1]+=1
        elif kind=='EndShapeRecord':break
        else:raise ValueError('Unproven edge record: '+kind)
    assert records[-1]['type']=='EndShapeRecord'
    masks=bitmap_shape_fill_polygons(shape)
    if masks is None or len(masks)!=len(styles):raise ValueError('Unresolved original contour mapping')
    raw={struct.unpack_from('<H',p)[0]:(code,p,r) for code,p,r in source_tags(source) if code in (2,36,39)}
    fills=[]
    for index,(style,count,mask) in enumerate(zip(styles,counts,masks),1):
        matrix=style.find('bitmapMatrix');entry={'index':index,'style':dict(style.attrib),'matrix':dict(matrix.attrib),'directed_edge_count':count,'contours':mask}
        if count:
            code,payload,_=raw[int(style.get('bitmapId'))]
            if code!=36:raise ValueError('Unproven active source encoding')
            cid,width,height,pixels=decode_lossless(payload);entry['bitmap']={'id':cid,'width':width,'height':height,'raw_rgba_sha256':hashlib.sha256(bytes(v for p in pixels for v in p)).hexdigest()}
            a=float(matrix.get('scaleX',1))/20;b=float(matrix.get('rotateSkew0',0))/20;c=float(matrix.get('rotateSkew1',0))/20;d=float(matrix.get('scaleY',1))/20;tx=float(matrix.get('translateX',0))/20;ty=float(matrix.get('translateY',0))/20
            entry['transformed_bitmap_corners']=[[a*x+c*y+tx,b*x+d*y+ty] for x,y in [(0,0),(width,0),(width,height),(0,height)]]
            assert mask==[entry['transformed_bitmap_corners']]
        fills.append(entry)
    for name,node in [('shape.xml',shape),('wrapper.xml',wrapper)]: (output/name).write_text(ET.tostring(node,encoding='unicode')+'\n')
    ids=[shape_id,case['symbol']]+[int(v['style']['bitmapId']) for v in fills if v['directed_edge_count']]
    return {'case':case,'shape_id':shape_id,'fills':fills,'shape_records':records,'raw_tag_sha256':{str(i):hashlib.sha256(raw[i][2]).hexdigest() for i in ids},'ffdec_sha256':hashlib.sha256(ffdec.read_bytes()).hexdigest(),'export_command':command,'requires_quarter_turn_sampler':any(v['directed_edge_count'] and float(v['matrix'].get('scaleX',1))==0 and float(v['matrix'].get('scaleY',1))==0 and float(v['matrix'].get('rotateSkew0',0))*float(v['matrix'].get('rotateSkew1',0))==-400 for v in fills),'source_derived_input_verified':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cases',type=Path,required=True);p.add_argument('--case',required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--ffdec',type=Path,required=True)
    a=p.parse_args();r=inspect(a.cases,a.case,a.output,a.ffdec.resolve());(a.output/'analysis.json').write_text(json.dumps(r,indent=2)+'\n');print([(v['index'],v['directed_edge_count'],v.get('bitmap')) for v in r['fills']])
