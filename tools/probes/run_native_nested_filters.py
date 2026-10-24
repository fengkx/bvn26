"""Run the admitted CPU arithmetic through the pinned production-buffer diagnostic."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from tools.probes.run_nested_filters import ROOT, SIZES, cases, decode, compare
from tools.probes.native_cxform_candidate import construction


def fixture():
    root = ROOT/'evidence/importer-loud-fail/r58'
    raw = (root/'analysis.json.gz').read_bytes()
    provenance = json.loads((root/'provenance.json').read_text())
    if hashlib.sha256(raw).hexdigest()!=provenance['output_sha256']['analysis.json.gz']:
        raise ValueError('CPU admission evidence changed')
    import gzip
    report = json.loads(gzip.decompress(raw))
    if not report['cpu_arithmetic_passed'] or not report['gpu_advance_allowed']:
        raise ValueError('CPU arithmetic prerequisites do not pass')
    _,reciprocals,_ = construction()
    return {'production_admitted':False,'cpu_arithmetic_passed':True,'cases':cases(),
            'native_reciprocals':[0.0]+[reciprocals[a] for a in range(1,256)]}


def run(godot,native,output):
    output.mkdir(parents=True,exist_ok=True)
    references = decode(native)
    path = output/'fixture.json'
    path.write_text(json.dumps(fixture())+'\n')
    for stage in SIZES:
        (output/(stage+'.png')).unlink(missing_ok=True)
    (output/'buffers.json').unlink(missing_ok=True)
    command = [str(godot),'--path',str(ROOT/'godot'),'--rendering-method','gl_compatibility',
               '--quit-after','300','-s','res://tests/native_nested_filter_diagnostic.gd','--',str(path),str(output)]
    result = subprocess.run(command,capture_output=True,text=True,timeout=180)
    log = result.stdout+result.stderr
    (output/'godot.log').write_text(log)
    if (result.returncode or 'ERROR' in log or 'NESTED_FILTER_DIAGNOSTIC_OK cases=48' not in log or
            'NATIVE_CXFORM_BINDINGS_OK sprites=336 groups=96 production_admitted=false' not in log):
        raise ValueError('Actual FilterGroup/native arithmetic diagnostic failed')
    records = json.loads((output/'buffers.json').read_text())
    expected = []
    for spec in cases():
        profile = spec['key'][1]
        expected.append({'case':spec['key'][0],'production_admitted':False,'groups':[
            {'size':[12,12],'origin':[3,3],'passes':[[12,12]]*(3 if profile==0 else 2)},
            {'size':[18,18],'origin':[1,1],'passes':[[18,18]]*(2 if profile==0 else 3)}]})
    if records!=expected:
        raise ValueError('Production allocation, padding or filter order changed')
    report = compare(references,output)
    (output/'comparison.json').write_text(json.dumps(report,indent=2)+'\n')
    files = ['tools/probes/run_native_nested_filters.py','tools/probes/run_nested_filters.py',
             'tools/probes/native_cxform_candidate.py','godot/tests/native_cxform.gdshaderinc',
             'godot/tests/native_nested_filter_composite.gdshader','godot/tests/native_nested_filter_diagnostic.gd',
             'godot/tests/nested_filter_diagnostic.gd','godot/tests/nested_filter_preview.gd',
             'godot/tests/nested_buffer_diagnostic.gd','godot/tests/normal_composition.gdshaderinc',
             'godot/timeline_preview.gd','godot/filter_group.gd','godot/blend_group.gd','godot/flash_filter.gdshader']
    sha = lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    provenance = {'command':command,'production_admitted':False,'godot_sha256':sha(godot),
        'source_sha256':{p:sha(ROOT/p) for p in files},
        'native_sha256':{p:sha(native/p) for p in ('build.json','native.log')},
        'readback_sha256':{p:sha(output/p) for p in [*(s+'.png' for s in SIZES),'buffers.json','fixture.json']}}
    (output/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    return report


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('godot','native','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    args = parser.parse_args()
    report = run(args.godot.resolve(),args.native.resolve(),args.output.resolve())
    print(json.dumps({k:v for k,v in report.items() if k!='rows'}))
    raise SystemExit(0 if report['passed'] else 1)
