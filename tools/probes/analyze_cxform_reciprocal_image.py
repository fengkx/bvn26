"""Reject unreachable reciprocal outputs without fitting an input or coefficient."""
import argparse
from bisect import bisect_left, bisect_right
import gzip
import hashlib
import json
from pathlib import Path
from tools.probes.analyze_cxform_signed_bounds import EVIDENCE


def decode(text):
    lines = text.splitlines()
    header = lines[0].split()
    if header[:3]!=['domain','3b800000','3f800000'] or header[3]!='csr' or int(header[4],16)&0x6000:
        raise ValueError('Unexpected fixed domain or rounding-mode readback')
    expected = 0x3b800000
    runs = []
    for line in lines[1:-1]:
        start,end,value = (int(v,16) for v in line.split())
        if start!=expected or end<start or end>0x3f800000:
            raise ValueError('Missing, overlapping or reordered hardware run')
        if runs and value>=runs[-1][2]:
            raise ValueError('Nondecreasing hardware transition')
        runs.append((start,end,value))
        expected=end+1
    if expected!=0x3f800001 or lines[-1]!='done 67108865 rises 0':
        raise ValueError('Incomplete exhaustive hardware measurement')
    return runs


def analyze(text):
    runs = decode(text)
    raw = (EVIDENCE/'r55/analysis.json.gz').read_bytes()
    pin = json.loads((EVIDENCE/'r55/provenance.json').read_text())['output_sha256']['analysis.json.gz']
    if hashlib.sha256(raw).hexdigest()!=pin:
        raise ValueError('Sequence-specific bounds changed')
    bounds = json.loads(gzip.decompress(raw))
    outputs = sorted(v[2] for v in runs)
    models = {}
    for mode,model in bounds['models'].items():
        rows = {}
        for alpha,b in model['intervals'].items():
            lo,hi = b['low_bits'],b['high_bits']
            count = bisect_right(outputs,hi)-bisect_left(outputs,lo)
            rows[alpha] = {'low_bits':lo,'high_bits':hi,'reachable_output_count':count,
                           'lower_witness':b['lower_witness'],'upper_witness':b['upper_witness']}
        models[mode] = {'alphas':rows,'unreachable_alphas':[int(a) for a,v in rows.items() if not v['reachable_output_count']]}
    return {'input_count':67108865,'output_runs':len(runs),'domain_bits':[0x3b800000,0x3f800000],
            'models':models,'hardware_instruction_inference':False,'coefficients_selected':False,
            'candidate_admitted':False,'gpu_advance_allowed':False,'production_admitted':False}


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--hardware',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    report = analyze(args.hardware.read_text())
    args.output.write_bytes(gzip.compress((json.dumps(report,indent=2)+'\n').encode(),mtime=0))
    print('runs',report['output_runs'])
    for name,m in report['models'].items():
        print(name,'unreachable',len(m['unreachable_alphas']),m['unreachable_alphas'],
              'alpha49',m['alphas']['49']['reachable_output_count'])
    raise SystemExit(1)
