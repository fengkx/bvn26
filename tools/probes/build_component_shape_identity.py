"""Preserve the original component while testing AVM1 primitive-depth identity."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import uuid
import struct
import xml.etree.ElementTree as ET
from tools.probes.build_bound_bitmap_component import source_tags
from tools.probes.build_component_cache_boundaries import build,ROOT

HARNESS=Path('tools/probes/flash_filters/component-shape-identity.as')


def create(output,ffdec):
    report=build(ROOT/'evidence/importer-loud-fail/r21/components/jiraiya/cases.json','jiraiya-342-766-29',output,ffdec)
    native=output.resolve()/'components/jiraiya'
    run='shape-identity-'+uuid.uuid4().hex[:12]
    script=(ROOT/HARNESS).read_text().replace('RUN',run)
    (native/'scripts/frame_1/DoAction.as').write_text(script)
    subprocess.run(['java',f'-Duser.home={output.resolve()}','-Djava.awt.headless=true','-jar',str(ffdec),'-importScript',str(native/'base.swf'),str(native/'game/main.swf'),str(native/'scripts')],check=True,stdout=subprocess.DEVNULL)
    report.update(run_id=run,harness_source=str(HARNESS),harness_sha256=hashlib.sha256((ROOT/HARNESS).read_bytes()).hexdigest(),outputs_sha256={'game/main.swf':hashlib.sha256((native/'game/main.swf').read_bytes()).hexdigest()})
    xml=output.resolve()/'source.xml'
    subprocess.run(['java',f'-Duser.home={output.resolve()}','-Djava.awt.headless=true','-jar',str(ffdec),'-swf2xml',str(ROOT/report['source']),str(xml)],check=True,stdout=subprocess.DEVNULL)
    tags=ET.parse(xml).getroot().find('tags')
    shape=next(t for t in tags if t.get('shapeId')=='276')
    wrapper=next(t for t in tags if t.get('spriteId')=='277')
    for name,node in [('authored-shape.xml',shape),('authored-wrapper.xml',wrapper)]:
        (native/name).write_text(ET.tostring(node,encoding='unicode')+'\n')
    report['authored_xml_sha256']={name:hashlib.sha256((native/name).read_bytes()).hexdigest() for name in ('authored-shape.xml','authored-wrapper.xml')}
    report['raw_tag_sha256']={str(struct.unpack_from('<H',payload)[0]):hashlib.sha256(raw).hexdigest() for code,payload,raw in source_tags(ROOT/report['source']) if code in (2,36,39) and struct.unpack_from('<H',payload)[0] in (166,276,277)}
    (native/'build.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--ffdec',type=Path,required=True)
    a=p.parse_args();print(json.dumps(create(a.output,a.ffdec.resolve()),indent=2))
