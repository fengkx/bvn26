"""Measure globally fixed x86 rounding modes, retaining all native controls."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import platform
import subprocess

from tools.probes.analyze_cxform_intervals import channel, coefficient_measurements
from tools.probes.analyze_cxform_rejected import measurements, sequence
from tools.probes.analyze_cxform_signed_bounds import controls, EVIDENCE


def analyze(executable, output):
    old,signed = controls()
    groups = {'old':old,'signed':signed}
    unique = sorted({tuple(args) for rows in groups.values() for _,args,_ in rows})
    if any(any(int(v)!=v for v in args) for args in unique):
        raise ValueError('Hardware probe requires consumed integer operands')
    source = ''.join(' '.join(str(int(v)) for v in args)+'\n' for args in unique)
    process = subprocess.run(['arch','-x86_64',str(executable)],input=source,text=True,capture_output=True,check=True)
    lines = process.stdout.splitlines()
    if len(lines)!=len(unique)+1 or not lines[0].startswith('initial '):
        raise ValueError('Incomplete hardware readbacks')
    measured = coefficient_measurements(EVIDENCE/'r41')
    normalization = measurements(EVIDENCE/'r44')
    decoded = {}
    for i,(args,line) in enumerate(zip(unique,lines[1:])):
        fields = line.split()
        if len(fields)!=17 or int(fields[0])!=i or [fields[j] for j in (1,5,9,13)]!=['0000','2000','4000','6000']:
            raise ValueError('Wrong row or rounding-mode readback')
        values = [[int(v) for v in fields[j+1:j+4]] for j in (1,5,9,13)]
        expected = [channel(args,measured[args[1]]['estimate_inverse'],'unit','alpha_first'),
                    sequence(args,normalization['divide'],'alpha_first'),
                    sequence(args,normalization['multiply_rounded'],'alpha_first')]
        if values[0]!=expected:
            raise ValueError(f'Nearest-mode regression at {args}: {values[0]} != {expected}')
        decoded[args] = values
    counts = {name:Counter((tuple(args),target) for _,args,target in rows) for name,rows in groups.items()}
    models = {}
    pair = [((25,49,-129,128,100),12),((23,49,2046,-894,100),11)]
    for mode,mode_name in enumerate(('nearest','down','up','toward_zero')):
        for form,form_name in enumerate(('integer_alpha','normalized_divide','normalized_multiply')):
            scores = {}
            for group,rows in counts.items():
                exact,total,failures = 0,0,[]
                for (args,target),count in rows.items():
                    actual = decoded[args][mode][form]
                    total += count
                    if actual==target:
                        exact += count
                    else:
                        failures.append({'args':args,'native':target,'actual':actual,'count':count})
                scores[group] = {'exact':exact,'total':total,'failures':failures}
            models[mode_name+'/'+form_name] = {'scores':scores,'pair':[
                {'args':args,'native':target,'actual':decoded[args][mode][form]} for args,target in pair]}
    output.mkdir(parents=True,exist_ok=True)
    (output/'inputs.txt.gz').write_bytes(gzip.compress(source.encode(),mtime=0))
    (output/'hardware.txt.gz').write_bytes(gzip.compress(process.stdout.encode(),mtime=0))
    sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
    environment={'host':platform.platform(),'compiler':subprocess.check_output(['clang','--version'],text=True),
        'compile':['clang','-arch','x86_64','-O0','-ffp-contract=off','-frounding-math','tools/probes/cxform_rounding_modes.c','-o',str(executable)],
        'run':['arch','-x86_64',str(executable)],'source_sha256':sha('tools/probes/cxform_rounding_modes.c'),
        'executable_sha256':sha(executable),'input_sha256':hashlib.sha256(source.encode()).hexdigest(),
        'output_sha256':hashlib.sha256(process.stdout.encode()).hexdigest(),'instruction_inference':False}
    (output/'environment.json').write_text(json.dumps(environment,indent=2)+'\n')
    return {'models':models,'nearest_mode_unique_controls_exact':len(unique)*3,
            'unique_inputs':len(unique),'old_constraints':len(old),'signed_constraints':len(signed),
            'candidate_admitted':False,'gpu_advance_allowed':False,'production_admitted':False}


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--executable',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    report = analyze(args.executable,args.output)
    (args.output/'analysis.json.gz').write_bytes(gzip.compress((json.dumps(report,indent=2)+'\n').encode(),mtime=0))
    for name,m in report['models'].items():
        print(name,'pair',[p['actual'] for p in m['pair']],{k:v['exact'] for k,v in m['scores'].items()})
    raise SystemExit(1)
