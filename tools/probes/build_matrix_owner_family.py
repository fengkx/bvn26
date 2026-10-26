"""Capture pinned owner states with explicitly local synthetic wrapper identifiers."""
import argparse
import hashlib
import json
from pathlib import Path
from tools.probes.build_matrix_component_boundaries import build as build_one
from tools.probes.build_bound_bitmap_component import ROOT


def build(cases_path,output,ffdec):
    output=output.resolve()
    if any(p==output or p in output.parents for p in (ROOT/'game',ROOT/'scripts')):raise ValueError('Locked input output path')
    pinned=json.loads(cases_path.read_text());results=[]
    for state in (2,3):
        original=next(v for v in pinned if v['id']==f'main-298-{state}-1')
        # Each isolated SWF owns a new diagnostic wrapper60000. The original
        # family used60001/60002 only to avoid collisions in its combined SWF.
        case={**original,'wrapper_symbol':60000}
        folder=output/f'frame{state}';folder.mkdir(parents=True,exist_ok=True)
        input_path=folder/'isolated-case.json';input_path.write_text(json.dumps([case],indent=2)+'\n')
        report=build_one(input_path,case['id'],folder,ffdec)
        assert {k:v for k,v in report['case'].items() if k!='wrapper_symbol'}=={k:v for k,v in original.items() if k!='wrapper_symbol'}
        report.update({'pinned_cases_source':str(cases_path.resolve().relative_to(ROOT)),
                       'pinned_cases_sha256':hashlib.sha256(cases_path.read_bytes()).hexdigest(),
                       'original_synthetic_wrapper_symbol':original['wrapper_symbol'],
                       'isolated_synthetic_wrapper_symbol':60000})
        (folder/'components/main/build.json').write_text(json.dumps(report,indent=2)+'\n');results.append(report)
    return results


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cases',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--ffdec',type=Path,required=True);a=p.parse_args()
    for report in build(a.cases,a.output,a.ffdec.resolve()):print(report['case']['id'],report['run_id'])
