"""Actual allocated filter rows against independent paired native stage captures."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from tools.probes.run_native_nested_filters import fixture, ROOT
from tools.probes.run_nested_filters import unpack


def decode(native):
    build = json.loads((native/'build.json').read_text())
    if hashlib.sha256((ROOT/build['source']).read_bytes()).hexdigest() != build['source_sha256']:
        raise ValueError('Native source hash changed')
    events = [line.split('|') for line in (native/'native.log').read_text().splitlines() if line.startswith('AIREF|')]
    if len(events)!=161 or events[-1][6:]!=['done','ok']:
        raise ValueError('Incomplete native extent stages')
    for i, row in enumerate(events):
        if row[1]!=build['run_id'] or row[2:6]!=[str(i),'0','0','0']:
            raise ValueError('Native run identity or order changed')
    cases=[]
    for width in (15,16,17,18,19,20,31,32,33,64):
        for left in (40,41):
            for opacity in (100,50):
                index=len(cases);rows=events[index*4:index*4+4]
                expected=[index,width,left,opacity,left-3,37,width+6,70]
                if rows[1][6]!='case' or list(map(int,rows[1][7].split(',')))!=expected:
                    raise ValueError('Native rectangle identity mismatch')
                case={'id':index,'width':width,'left':left,'opacity':opacity,'rect':expected[4:]}
                for row,stage in zip((rows[0],rows[2],rows[3]),('input','filtered','final')):
                    values=row[7].split(',')
                    if row[6]!='row' or values[:2]!=[str(index),stage] or len(values)!=322:
                        raise ValueError('Native stage missing or reordered')
                    case[stage]=unpack(list(map(int,values[2:])))
                cases.append(case)
    return cases


def compare(native, actual):
    if len(actual)!=len(native):
        raise ValueError('GPU cases missing')
    scores={}
    for stage in ('input','filtered','final'):
        failures=[]
        for a,b in zip(actual,native):
            if a['id']!=b['id'] or a['rect']!=b['rect'] or len(a[stage])!=160 or any(len(p)!=4 for p in a[stage]):
                raise ValueError('GPU allocation or row extent changed')
            for x,(p,q) in enumerate(zip(a[stage],b[stage])):
                if p!=q:failures.append({'id':b['id'],'x':x,'gpu':p,'native':q})
        scores[stage]={'pixels':6400,'exact':6400-len(failures),'failures':failures}
    return {'scores':scores,'passed':all(not v['failures'] for v in scores.values()),'production_admitted':False}


def run(godot,native,output):
    output.mkdir(parents=True,exist_ok=True)
    cases=decode(native);data=fixture();data['cases']=[{k:v for k,v in c.items() if k not in ('input','filtered','final')} for c in cases]
    path=output/'fixture.json';path.write_text(json.dumps(data)+'\n')
    rows=output/'rows.json';rows.unlink(missing_ok=True)
    cmd=[str(godot),'--path',str(ROOT/'godot'),'--rendering-method','gl_compatibility','--quit-after','300','-s','res://tests/native_extent_rows.gd','--',str(path),str(rows)]
    p=subprocess.run(cmd,capture_output=True,text=True,timeout=180);log=p.stdout+p.stderr;(output/'godot.log').write_text(log)
    if p.returncode or 'ERROR' in log or 'NATIVE_EXTENT_ROWS_OK cases=40 stages=120' not in log:raise ValueError('GPU extent render failed')
    report=compare(cases,json.loads(rows.read_text()));(output/'comparison.json').write_text(json.dumps(report,indent=2)+'\n')
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    sources=['tools/probes/run_native_extent_rows.py','tools/probes/flash_filters/filter-extent-rows.as','godot/tests/native_extent_rows.gd','godot/tests/native_extent_filter_group.gd','godot/tests/native_nested_filter_composite.gdshader','godot/tests/native_cxform.gdshaderinc','godot/filter_group.gd','godot/blend_group.gd','godot/timeline_preview.gd']
    provenance={'command':cmd,'source_sha256':{s:sha(ROOT/s) for s in sources},'native_sha256':{s:sha(native/s) for s in ('native.log','build.json')},'readback_sha256':{s:sha(output/s) for s in ('fixture.json','rows.json')},'godot_sha256':sha(godot),'production_admitted':False}
    (output/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n');return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('godot','native','output'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();report=run(args.godot.resolve(),args.native.resolve(),args.output.resolve())
    print({k:(v['exact'],v['pixels']) for k,v in report['scores'].items()})
    raise SystemExit(0 if report['passed'] else 1)
