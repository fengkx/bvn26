"""Native-measured kernel consumption through actual diagnostic FilterGroup nodes."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
from tools.probes.run_native_nested_filters import fixture, ROOT


from tools.probes.run_integer_extent_gpu import cases, compare


def run(godot,output):
    output.mkdir(parents=True,exist_ok=True);expected=cases();base=fixture();actual=[];commands=[]
    for start in range(0,len(expected),64):
        folder=output/str(start);folder.mkdir(exist_ok=True)
        data={**base,'cases':[{k:v for k,v in c.items() if k!='native'} for c in expected[start:start+64]]}
        path=folder/'fixture.json';path.write_text(json.dumps(data)+'\n');rows=folder/'rows.json';rows.unlink(missing_ok=True)
        cmd=[str(godot),'--path',str(ROOT/'godot'),'--rendering-method','gl_compatibility','--quit-after','300','-s','res://tests/consumed_extent_rows.gd','--',str(path),str(rows)]
        commands.append(cmd);p=subprocess.run(cmd,capture_output=True,text=True,timeout=180);log=p.stdout+p.stderr;(folder/'godot.log').write_text(log)
        marker=f"CONSUMED_EXTENT_ROWS_OK cases={len(data['cases'])} production_admitted=false"
        if p.returncode or 'ERROR' in log or marker not in log:raise ValueError('GPU batch failed: '+str(start))
        chunk=json.loads(rows.read_text())
        if [r['id'] for r in chunk]!=list(range(len(data['cases']))):raise ValueError('GPU batch identity changed')
        for row in chunk:row['id']+=start
        actual.extend(chunk);print('batch',start,'complete',flush=True)
    report=compare(expected,actual)
    (output/'rows.json.gz').write_bytes(gzip.compress(json.dumps(actual).encode(),mtime=0))
    (output/'comparison.json').write_text(json.dumps(report,indent=2)+'\n')
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    files=['tools/probes/run_consumed_extent_gpu.py','tools/probes/run_integer_extent_gpu.py','godot/tests/consumed_extent_rows.gd','godot/tests/integer_extent_filter_group.gd','godot/tests/consumed_extent_filter_group.gd','godot/tests/integer_blur.gdshader','godot/tests/native_nested_filter_composite.gdshader','godot/tests/native_cxform.gdshaderinc','godot/filter_group.gd','godot/blend_group.gd','godot/timeline_preview.gd','godot/flash_filter.gdshader']
    provenance={'commands':commands,'source_sha256':{s:sha(ROOT/s) for s in files},'native_sha256':{f'evidence/importer-loud-fail/{r}/native/native.log':sha(ROOT/f'evidence/importer-loud-fail/{r}/native/native.log') for r in ('r62','r66','r68','r69')},'readback_sha256':{'rows.json.gz':sha(output/'rows.json.gz')},'godot_sha256':sha(godot),'production_admitted':False}
    (output/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n');return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--godot',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();r=run(args.godot.resolve(),args.output.resolve());print({k:(v['exact'],v['pixels']) for k,v in r['scores'].items()})
    raise SystemExit(0 if r['passed'] else 1)
