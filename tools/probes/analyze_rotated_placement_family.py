"""Verify source placements before reusing an identical bounded live GPU render."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import subprocess
import xml.etree.ElementTree as ET
from PIL import Image
from tools.probes.analyze_yulong_rotated_source import source_leaf,render,ROOT,source_tags
from tools.probes.analyze_component_glow_boundaries import glow
from tools.probes.analyze_jiraiya_filter_boundary import comparison
from tools.importer.import_guards import validate_placement
from tools.importer.visual_filters import compile_filters


def extract(output,ffdec):
    output=output.resolve()
    if any(p==output or p in output.parents for p in (ROOT/'game',ROOT/'scripts')):raise ValueError('Locked source output')
    output.mkdir(parents=True,exist_ok=True);info,_=source_leaf();source=ROOT/info['case']['source']['path'];xml=output/'source.xml'
    command=['java',f'-Duser.home={output}','-Djava.awt.headless=true','-jar',str(ffdec),'-swf2xml',str(source),str(xml)]
    subprocess.run(command,check=True,stdout=subprocess.DEVNULL)
    owner=next(v for v in ET.parse(xml).getroot().find('tags') if v.get('spriteId')=='345')
    (output/'owner.xml').write_text(ET.tostring(owner,encoding='unicode')+'\n')
    raw=next(r for c,p,r in source_tags(source) if c==39 and struct.unpack_from('<H',p)[0]==345)
    metadata={'source':info['case']['source'],'owner_tag_sha256':hashlib.sha256(raw).hexdigest(),'owner_xml_sha256':hashlib.sha256((output/'owner.xml').read_bytes()).hexdigest(),'ffdec_sha256':hashlib.sha256(ffdec.read_bytes()).hexdigest(),'command':command}
    (output/'build.json').write_text(json.dumps(metadata,indent=2)+'\n')


def analyze(source_folder,gpu_folder):
    build=json.loads((source_folder/'build.json').read_text());path=ROOT/build['source']['path']
    assert hashlib.sha256(path.read_bytes()).hexdigest()==build['source']['sha256']
    raw=next(r for c,p,r in source_tags(path) if c==39 and struct.unpack_from('<H',p)[0]==345)
    assert hashlib.sha256(raw).hexdigest()==build['owner_tag_sha256']
    assert hashlib.sha256((source_folder/'owner.xml').read_bytes()).hexdigest()==build['owner_xml_sha256']
    base,texels=source_leaf();cases=json.loads((ROOT/'evidence/importer-loud-fail/r32/components/yulong/cases.json').read_text());cases=[c for c in cases if c['symbol']==base['case']['symbol']];assert len(cases)==5
    placements={};frame=1
    for node in ET.parse(source_folder/'owner.xml').getroot().find('subTags'):
        if node.get('type')=='ShowFrameTag':frame+=1
        elif node.get('type') in ('PlaceObject2Tag','PlaceObject3Tag'):placements[frame,int(node.get('depth'))]=node
    baseline,meta=render(base,texels,0);filtered=glow(baseline,base['case']['placement']['filters'][0]);composed=[[r+96*(256-a)//256,g+96*(256-a)//256,b+96*(256-a)//256,255] for r,g,b,a in filtered]
    provenance=json.loads((gpu_folder/'provenance.json').read_text())
    image=gpu_folder/'final-1.png';assert hashlib.sha256(image.read_bytes()).hexdigest()==provenance['readback_sha256']['final-1.png']
    gpu=list(Image.open(image).convert('RGBA').getdata());rows=[]
    for case in cases:
        p=case['placement'];node=placements[p['placed_frame'],p['depth']];location=f"{case['source']['path']}:DefineSprite_345/frame_{p['placed_frame']}/depth_{p['depth']}"
        validate_placement(node,location)
        expected={'placeFlagHasCharacter','placeFlagHasMatrix','placeFlagHasFilterList','placeFlagHasRatio'}
        assert {k for k,v in node.attrib.items() if k.startswith('placeFlag') and v=='true'}==expected
        assert int(node.get('characterId'))==p['character_id']==case['symbol'] and int(node.get('ratio'))==p['ratio']
        matrix={k:(int(v) if k not in ('type','hasRotate','hasScale') else v) for k,v in node.find('matrix').attrib.items()}
        assert matrix==p['matrix'] and matrix['hasScale']==matrix['hasRotate']=='false'
        assert compile_filters(node.find('surfaceFilterList'),location)==p['filters']==base['case']['placement']['filters']
        assert case['source']==base['case']['source'] and case['source_frame_count']==case['frame_count']==1 and case['samples']==[0,3]
        candidate,cm=render({**base,'case':case},texels,0)
        assert cm['origin']==meta['origin'] and candidate==baseline
        for tick in case['samples']:
            native=ROOT/f"evidence/importer-loud-fail/r21/components/yulong/{case['id']}-{tick:03d}.native.png";target=list(Image.open(native).convert('RGBA').getdata())
            rows.append({'case':case['id'],'tick':tick,'location':location,'effective_origin':cm['origin'],'source_placement':ET.tostring(node,encoding='unicode'),'native_sha256':hashlib.sha256(native.read_bytes()).hexdigest(),'cpu':comparison(composed,target),'gpu':comparison(gpu,target)})
    return {'images':rows,'exact_images':sum(v['gpu']['exact']==v['gpu']['samples'] for v in rows),'shared_input_signature_verified':True,'production_admitted':False,'full_production_suite_rerun':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--gpu',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--ffdec',type=Path);a=p.parse_args()
    if a.ffdec:extract(a.source,a.ffdec.resolve())
    r=analyze(a.source,a.gpu);a.output.write_text(json.dumps(r,indent=2)+'\n');print('original images',r['exact_images'],len(r['images']));raise SystemExit(0 if r['exact_images']==len(r['images']) else 1)
