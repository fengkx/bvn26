#!/usr/bin/env python3
"""Native explicit nested filter buffers vs actual production FilterGroup diagnostics."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.probes.nested_composition import inputs

SIZES = {'child_input':12, 'child_filter':12, 'parent_input':18, 'parent_filter':18, 'final':24}


def cases():
    rows = []
    for profile in range(2):
        for alpha in (0,128,255):
            for child in (25,100):
                for parent in (50,100):
                    for cx in (0,1):
                        key = [len(rows),profile,alpha,child,parent,cx]
                        rows.append({'key':key,'inputs':inputs([key[0],0,alpha,child,parent])})
    return rows


def unpack(values):
    if len(values)%2 or any(not -2**31 <= n < 2**32 for n in values):
        raise ValueError('Invalid native packed pixels')
    result = []
    for i in range(0,len(values),2):
        a,b = values[i:i+2]
        if (b>>24)&255 != 255:
            raise ValueError('Black readback must be opaque')
        result.append([(b>>s)&255 for s in (16,8,0)]+[(a>>24)&255])
    return result


def decode(native):
    build = json.loads((native/'build.json').read_text())
    if hashlib.sha256((ROOT/build['source']).read_bytes()).hexdigest() != build['source_sha256']:
        raise ValueError('Native source changed')
    events = []
    for line in (native/'native.log').read_text().splitlines():
        p = line.split('|')
        if p[:2] != ['AIREF',build['run_id']]:
            continue
        if len(p)!=8 or p[2:6] != [str(len(events)),'0','0','0']:
            raise ValueError('Malformed or reordered native event')
        events.append(p[6:])
    cursor = 0
    rows = []
    def take(kind):
        nonlocal cursor
        if cursor >= len(events) or events[cursor][0]!=kind:
            raise ValueError('Missing or unexpected native event')
        value = events[cursor][1];cursor+=1
        return value
    for spec in cases():
        if list(map(int,take('case').split(','))) != spec['key']:
            raise ValueError('Unexpected case identity')
        values = list(map(int,take('inputs').split(',')))
        if values[0]!=spec['key'][0] or unpack(values[1:])!=list(spec['inputs'].values()):
            raise ValueError('Source pixel mismatch')
        record = {}
        for stage,size in SIZES.items():
            pixels = []
            for y in range(size):
                fields = take('row').split(',')
                if fields[:3] != [str(spec['key'][0]),stage,str(y)]:
                    raise ValueError('Unexpected stage/coordinate')
                row = unpack(list(map(int,fields[3:])))
                if len(row)!=size:
                    raise ValueError('Native buffer width mismatch')
                pixels.extend(row)
            record[stage] = pixels
        rows.append(record)
    if take('done')!='ok' or cursor!=len(events):
        raise ValueError('Missing or duplicate completion')
    return rows


def compare(native, output):
    if len(native)!=48:
        raise ValueError('Missing reference cases')
    reports = []
    for stage,size in SIZES.items():
        image = Image.open(output/(stage+'.png')).convert('RGBA')
        if image.size!=(size,size*48):
            raise ValueError('Unexpected readback dimensions')
        pixels = [list(p) for p in image.getdata()]
        for spec,ref in zip(cases(),native):
            index = spec['key'][0];actual=pixels[index*size*size:(index+1)*size*size]
            errors=[];maximum=[0]*4
            for at,(a,b) in enumerate(zip(ref[stage],actual)):
                delta=[abs(x-y) for x,y in zip(a,b)]
                maximum=[max(x,y) for x,y in zip(maximum,delta)]
                if any(delta):errors.append({'x':at%size,'y':at//size,'native':a,'actual':b})
            reports.append({'key':spec['key'],'stage':stage,'pixels':size*size,'exact':size*size-len(errors),
                            'max_channel_delta':maximum,'failures':errors})
    return {'passed':all(r['exact']==r['pixels'] for r in reports),'production_admitted':False,
            'pixels':sum(r['pixels'] for r in reports),'exact':sum(r['exact'] for r in reports),'rows':reports}


def run(godot,native,output):
    output.mkdir(parents=True,exist_ok=True)
    references=decode(native)
    fixture=output/'fixture.json';fixture.write_text(json.dumps({'production_admitted':False,'cases':cases()})+'\n')
    for stage in SIZES:(output/(stage+'.png')).unlink(missing_ok=True)
    (output/'buffers.json').unlink(missing_ok=True)
    command=[str(godot),'--path',str(ROOT/'godot'),'--rendering-method','gl_compatibility','--quit-after','300',
             '-s','res://tests/nested_filter_diagnostic.gd','--',str(fixture),str(output)]
    result=subprocess.run(command,capture_output=True,text=True,timeout=180)
    log=result.stdout+result.stderr;(output/'godot.log').write_text(log)
    if result.returncode or 'ERROR' in log or 'NESTED_FILTER_DIAGNOSTIC_OK cases=48' not in log:
        raise ValueError('Actual FilterGroup diagnostic failed to render cleanly')
    records=json.loads((output/'buffers.json').read_text())
    expected=[]
    for spec in cases():
        profile=spec['key'][1]
        expected.append({'case':spec['key'][0],'production_admitted':False,'groups':[
            {'size':[12,12],'origin':[3,3],'passes':[[12,12]]*(3 if profile==0 else 2)},
            {'size':[18,18],'origin':[1,1],'passes':[[18,18]]*(2 if profile==0 else 3)}]})
    if records!=expected:
        raise ValueError('Unexpected FilterGroup allocation or pass order: '+str(records[0]))
    report=compare(references,output)
    (output/'comparison.json').write_text(json.dumps(report,indent=2)+'\n')
    files=['tools/probes/run_nested_filters.py','godot/tests/nested_filter_preview.gd',
           'godot/tests/nested_filter_diagnostic.gd','godot/tests/nested_filter_composite.gdshader',
           'godot/tests/nested_buffer_diagnostic.gd','godot/tests/normal_composition.gdshaderinc',
           'godot/timeline_preview.gd','godot/filter_group.gd','godot/blend_group.gd','godot/flash_filter.gdshader']
    provenance={'command':command,'production_admitted':False,'godot_sha256':hashlib.sha256(godot.read_bytes()).hexdigest(),
                'source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files},
                'native_sha256':{p:hashlib.sha256((native/p).read_bytes()).hexdigest() for p in ('build.json','native.log')},
                'readback_sha256':{p:hashlib.sha256((output/p).read_bytes()).hexdigest() for p in [*(s+'.png' for s in SIZES),'buffers.json']}}
    (output/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('godot','native','output'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();report=run(args.godot.resolve(),args.native.resolve(),args.output.resolve())
    print(json.dumps({k:v for k,v in report.items() if k!='rows'}))
    raise SystemExit(0 if report['passed'] else 1)
