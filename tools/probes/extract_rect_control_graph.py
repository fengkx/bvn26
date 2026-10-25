"""Compile bounded rectangle removal and Stop bytecode into explicit diagnostic frame states."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import xml.etree.ElementTree as ET
from tools.probes.build_bound_bitmap_component import ROOT,source_tags,bitmap_shape_fill_polygons
from tools.probes.inventory_bitmap_roundtrip import decode_lossless
from tools.probes.rect_mask_binding import canonical_rect_mask
from tools.importer.import_guards import validate_placement


def extract(xml,cases_path,case_id):
    matches=[c for c in json.loads(cases_path.read_text()) if c['id']==case_id];assert len(matches)==1;case=matches[0]
    source=ROOT/case['source']['path'];assert hashlib.sha256(source.read_bytes()).hexdigest()==case['source']['sha256']
    tags=ET.parse(xml).getroot().find('tags');wrapper=next(t for t in tags if t.get('spriteId')==str(case['symbol']))
    frames=[];placements=[];active=None;matrix=None;playing=True;actions=[]
    for tag in wrapper.find('subTags'):
        kind=tag.get('type');location=f"{case['source']['path']}:DefineSprite_{case['symbol']}/frame_{len(frames)+1}"
        if kind=='SoundStreamHead2Tag':
            if int(tag.get('streamSoundSampleCount'))!=0:raise ValueError(location+': Unproven audio stream')
        elif kind in ('PlaceObject2Tag','PlaceObject3Tag'):
            validate_placement(tag,f"{case['source']['path']}:DefineSprite_{case['symbol']}/frame_{len(frames)+1}")
            if tag.get('depth')!='1' or any(v=='true' and k.startswith('placeFlag') and k not in ('placeFlagHasCharacter','placeFlagHasMatrix','placeFlagMove') for k,v in tag.attrib.items()):raise ValueError(location+': Unconsumed placement fields')
            if tag.get('placeFlagHasCharacter')!='true':raise ValueError(location+': Unproven move-only placement')
            if active is None and tag.get('placeFlagMove')=='true':raise ValueError(location+': Move without source instance')
            if active is not None and tag.get('placeFlagMove')!='true':raise ValueError(location+': Unexpected new placement')
            if tag.find('matrix') is not None:matrix=dict(tag.find('matrix').attrib)
            if matrix is None or matrix.get('hasScale')=='true' or matrix.get('hasRotate')=='true':raise ValueError(location+': Unproven inner affine')
            active=int(tag.get('characterId'));placements.append({'frame':len(frames)+1,'xml':ET.tostring(tag,encoding='unicode')})
        elif kind=='RemoveObject2Tag':
            if tag.get('depth')!='1' or active is None:raise ValueError(location+': unowned removal')
            placements.append({'frame':len(frames)+1,'xml':ET.tostring(tag,encoding='unicode')})
            active=None;matrix=None
        elif kind=='DoActionTag':
            bytecode=bytes.fromhex(tag.get('actionBytes',''))
            # Decode a bounded AVM1 instruction grammar, never a source-hash exception.
            if not bytecode or bytecode[-1]!=0:raise ValueError(location+': unterminated action block')
            for offset,opcode in enumerate(bytecode[:-1]):
                if opcode!=7:raise ValueError(f'{location}: unsupported action opcode0x{opcode:02x} at byte{offset}')
                actions.append({'frame':len(frames)+1,'offset':offset,'operation':'stop'})
                playing=False
        elif kind=='ShowFrameTag':
            frames.append({'shape_id':active,'inner_matrix':dict(matrix) if matrix else None,'playing_after_actions':playing})
        else:raise ValueError(location+': uncompiled animated wrapper tag: '+kind)
    assert len(frames)==int(wrapper.get('frameCount'))==case['frame_count']==case['source_frame_count']
    raw={struct.unpack_from('<H',p)[0]:(code,p,r) for code,p,r in source_tags(source) if code in (2,20,21,35,36,39,90)}
    leaves={};ids={case['symbol']}
    for sid in sorted({f['shape_id'] for f in frames if f['shape_id'] is not None}):
        location=f"{case['source']['path']}:DefineShape_{sid}"
        shape=next(t for t in tags if t.get('shapeId')==str(sid));styles=shape.findall('./shapes/fillStyles/fillStyles/item');masks=bitmap_shape_fill_polygons(shape)
        if shape.findall('.//lineStyles/item') or masks is None or len(masks)!=len(styles):raise ValueError(location+': Unproven fill/stroke graph')
        counts=[0]*len(styles);active_styles=[0,0]
        for record in shape.findall('./shapes/shapeRecords/item'):
            kind=record.get('type')
            if kind=='StyleChangeRecord':
                if record.get('stateNewStyles')=='true' or record.get('stateLineStyle')=='true':raise ValueError(location+': Dynamic style/stroke')
                for i in range(2):
                    if record.get('stateFillStyle'+str(i))=='true':active_styles[i]=int(record.get('fillStyle'+str(i)))
                assert all(0<=v<=len(styles) for v in active_styles)
            elif kind=='StraightEdgeRecord':
                for v in active_styles:
                    if v:counts[v-1]+=1
            elif kind=='EndShapeRecord':break
            else:raise ValueError(location+': Unproven curve')
        used=[i for i,v in enumerate(counts) if v];assert len(used)==1;i=used[0];assert counts[i]==4
        assert all(not masks[j] for j in range(len(styles)) if j!=i)
        fill=styles[i];m=fill.find('bitmapMatrix');bid=int(fill.get('bitmapId'))
        if fill.get('fillStyleType') not in ('65','67'):raise ValueError(f"{case['source']['path']}:DefineShape_{sid}: unsupported fill type{fill.get('fillStyleType')}")
        if float(m.get('scaleX',1))!=20 or float(m.get('scaleY',1))!=20 or any(float(m.get(k,0)) for k in ('rotateSkew0','rotateSkew1')):raise ValueError(location+': Unproven bitmap affine')
        if raw[bid][0]!=36:raise ValueError(f"{case['source']['path']}:DefineShape_{sid}/bitmap_{bid}: unproven image encoding tag{raw[bid][0]}")
        cid,w,h,pixels=decode_lossless(raw[bid][1]);assert cid==bid
        leaf={'case':case,'shape_id':sid,'bitmap_id':bid,'width':w,'height':h,'pixels_premultiplied':pixels,'fill':dict(fill.attrib),'smooth_sampling':fill.get('fillStyleType')=='65','sampler_admitted':False,'fill_matrix':dict(m.attrib),'fill_masks':[masks[i]],'authored_fill_table':[{'style':dict(f.attrib),'matrix':dict(f.find('bitmapMatrix').attrib),'directed_edge_count':count,'contours':mask} for f,count,mask in zip(styles,counts,masks)],'shape_xml':ET.tostring(shape,encoding='unicode')}
        canonical_rect_mask(leaf);leaves[str(sid)]=leaf;ids.update((sid,bid))
    return {'case':case,'frames':frames,'placements':placements,'actions':actions,'leaves':leaves,'wrapper_xml':ET.tostring(wrapper,encoding='unicode'),'raw_tag_sha256':{str(i):hashlib.sha256(raw[i][2]).hexdigest() for i in sorted(ids)},'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--xml',type=Path,required=True);p.add_argument('--cases',type=Path,required=True);p.add_argument('--case',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=extract(a.xml,a.cases,a.case);a.output.write_text(json.dumps(r,separators=(',',':'))+'\n');print('source frames',len(r['frames']),'leaves',[(k,v['bitmap_id'],v['width'],v['height']) for k,v in r['leaves'].items()])
