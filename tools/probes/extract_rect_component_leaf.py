"""Extract a fail-closed, source-pinned single-rectangle visual diagnostic leaf."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import xml.etree.ElementTree as ET
from tools.probes.build_bound_bitmap_component import ROOT,source_tags,bitmap_shape_fill_polygons
from tools.probes.inventory_bitmap_roundtrip import decode_lossless
from tools.importer.import_guards import validate_placement
from tools.probes.rect_mask_binding import canonical_rect_mask


def extract(cases_path,case_id,output,ffdec):
    output=output.resolve()
    if any(p==output or p in output.parents for p in (ROOT/'game',ROOT/'scripts')):raise ValueError('Locked input output path')
    matches=[c for c in json.loads(cases_path.read_text()) if c['id']==case_id]
    if len(matches)!=1:raise ValueError('Missing/ambiguous case')
    case=matches[0];source=ROOT/case['source']['path']
    assert hashlib.sha256(source.read_bytes()).hexdigest()==case['source']['sha256']
    if case['source_frame_count']!=1 or case['frame_count']!=1:raise ValueError('Diagnostic requires a static source wrapper')
    if set(case['placement'])-{'depth','character_id','ratio','matrix','placed_frame','filters'}:raise ValueError('Outer placement field outside bounded visual diagnostic')
    output.mkdir(parents=True,exist_ok=True);xml=output/'source.xml'
    subprocess.run(['java',f'-Duser.home={output}','-Djava.awt.headless=true','-jar',str(ffdec),'-swf2xml',str(source),str(xml)],check=True,stdout=subprocess.DEVNULL)
    tags=ET.parse(xml).getroot().find('tags');wrapper=next(t for t in tags if t.get('spriteId')==str(case['symbol']))
    children=list(wrapper.find('subTags'))
    placements=[t for t in children if t.get('type') in ('PlaceObject2Tag','PlaceObject3Tag')]
    if len(placements)!=1 or wrapper.get('frameCount')!='1':raise ValueError('Unproven wrapper graph')
    # The complete wrapper XML is retained. Audio blocks, actions and extra display operations reject.
    if any(t.get('type') not in ('PlaceObject2Tag','PlaceObject3Tag','ShowFrameTag','SoundStreamHead2Tag') for t in children):raise ValueError('Uncompiled wrapper tag in visual diagnostic')
    placement=placements[0];validate_placement(placement,f"{case['source']['path']}:DefineSprite_{case['symbol']}/frame_1")
    if placement.get('depth')!='1' or any(value=='true' and key.startswith('placeFlag') and key not in ('placeFlagHasCharacter','placeFlagHasMatrix') for key,value in placement.attrib.items()):raise ValueError('Placement fields outside bounded visual diagnostic')
    inner=placement.find('matrix')
    if inner is None or inner.get('hasRotate')=='true' or inner.get('hasScale')=='true':raise ValueError('Inner affine outside translated-leaf domain')
    shape_id=int(placement.get('characterId'));shape=next(t for t in tags if t.get('shapeId')==str(shape_id))
    fills=shape.findall('.//fillStyles/item')
    if len(fills)!=1 or fills[0].get('fillStyleType')!='65' or shape.findall('.//lineStyles/item'):raise ValueError('Unproven fill/stroke')
    fill=fills[0];matrix=fill.find('bitmapMatrix');bitmap_id=int(fill.get('bitmapId'))
    if float(matrix.get('scaleX',1))!=20 or float(matrix.get('scaleY',1))!=20 or any(float(matrix.get(k,0)) for k in ('rotateSkew0','rotateSkew1')):raise ValueError('Unproven bitmap fill affine')
    raw={struct.unpack_from('<H',p)[0]:(code,p,r) for code,p,r in source_tags(source) if code in (2,36,39) and struct.unpack_from('<H',p)[0] in (bitmap_id,shape_id,case['symbol'])}
    if len(raw)!=3 or raw[bitmap_id][0]!=36:raise ValueError('Unproven source encoding')
    identity,width,height,pixels=decode_lossless(raw[bitmap_id][1]);assert identity==bitmap_id
    masks=bitmap_shape_fill_polygons(shape);fx=float(matrix.get('translateX',0))/20;fy=float(matrix.get('translateY',0))/20
    canonical_rect_mask({'width':width,'height':height,'fill_matrix':dict(matrix.attrib),'fill_masks':masks})
    fixture={'source':case['source']['path'],'source_sha256':case['source']['sha256'],'case':case,'shape_id':shape_id,'bitmap_id':bitmap_id,'width':width,'height':height,'pixels_premultiplied':pixels,'fill':dict(fill.attrib),'fill_matrix':dict(matrix.attrib),'fill_masks':masks,'inner_matrix':dict(inner.attrib),'raw_tag_sha256':{str(k):hashlib.sha256(r).hexdigest() for k,(_,_,r) in raw.items()},'wrapper_xml':ET.tostring(wrapper,encoding='unicode'),'shape_xml':ET.tostring(shape,encoding='unicode'),'production_admitted':False}
    (output/'fixture.json').write_text(json.dumps(fixture,separators=(',',':'))+'\n')
    report={'case':case_id,'source_sha256':case['source']['sha256'],'fixture_sha256':hashlib.sha256((output/'fixture.json').read_bytes()).hexdigest(),'ffdec_sha256':hashlib.sha256(ffdec.read_bytes()).hexdigest(),'production_admitted':False}
    (output/'build.json').write_text(json.dumps(report,indent=2)+'\n');return fixture


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cases',type=Path,required=True);p.add_argument('--case',required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--ffdec',type=Path,required=True)
    a=p.parse_args();r=extract(a.cases,a.case,a.output,a.ffdec.resolve());print('source leaf',r['shape_id'],r['bitmap_id'],r['width'],r['height'])
