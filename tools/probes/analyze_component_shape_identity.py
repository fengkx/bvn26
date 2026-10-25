"""Distinguish a primitive's AVM1 owner alias from its authored placement matrix."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import struct
import xml.etree.ElementTree as ET
from tools.probes.build_component_cache_boundaries import ROOT
from tools.probes.build_bound_bitmap_component import source_tags


def analyze(native):
    build=json.loads((native/'build.json').read_text())
    for path,digest in [(build['source'],build['source_sha256']),(build['harness_source'],build['harness_sha256'])]:
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest
    for name,digest in build['authored_xml_sha256'].items():assert hashlib.sha256((native/name).read_bytes()).hexdigest()==digest
    raw={str(struct.unpack_from('<H',p)[0]):hashlib.sha256(r).hexdigest() for code,p,r in source_tags(ROOT/build['source']) if code in (2,36,39) and struct.unpack_from('<H',p)[0] in (166,276,277)}
    assert raw==build['raw_tag_sha256'] and len(raw)==3
    path=native/'native.log';text=path.read_text() if path.exists() else gzip.decompress(path.with_suffix('.log.gz').read_bytes()).decode()
    events=[line.split('|') for line in text.splitlines() if line.startswith('AIREF|')]
    assert len(events)==6
    values={}
    for i,event in enumerate(events):
        assert event[1]==build['run_id'] and event[2:6]==[str(i),'0','0','0']
        assert event[6] not in values;values[event[6]]=event[7].split(',')
    assert values['identity']==['false','true','false','true']
    parent,owner,primitive=values['paths'];assert parent=='/source' and owner==primitive and owner.startswith(parent+'/')
    assert values['depths']==['1','-16355','-16355']
    matrix=list(map(float,values['matrices']));assert len(matrix)==8 and matrix[:4]==matrix[4:]
    assert values['control']==['true','false',owner+'/control','123'] and values['done']==['ok']
    shape=ET.parse(native/'authored-shape.xml').getroot();wrapper=ET.parse(native/'authored-wrapper.xml').getroot()
    assert shape.get('shapeId')=='276' and wrapper.get('spriteId')=='277' and wrapper.get('frameCount')=='1'
    placements=wrapper.findall('./subTags/item[@type="PlaceObject2Tag"]');assert len(placements)==1
    placement=placements[0];assert placement.get('characterId')=='276' and placement.get('depth')=='1'
    m=placement.find('matrix');fill=shape.find('.//fillStyles/item');fm=fill.find('bitmapMatrix')
    assert fill.get('bitmapId')=='166' and fill.get('fillStyleType')=='65'
    assert [int(m.get(k)) for k in ('translateX','translateY')]==[-17,-10]
    assert [int(fm.get(k)) for k in ('translateX','translateY')]==[17,10]
    return {'native_observations':values,'authored_placement':dict(placement.attrib),'authored_inner_matrix':dict(m.attrib),
            'authored_fill':dict(fill.attrib),'authored_fill_matrix':dict(fm.attrib),
            'primitive_depth_returns_owner':True,'dynamic_movieclip_control_distinct':True,
            'primitive_readback_is_inner_transform':False,'source_derived_input_verified':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=analyze(a.native);a.output.write_text(json.dumps(r,indent=2)+'\n');print('owner alias',r['primitive_depth_returns_owner'])
