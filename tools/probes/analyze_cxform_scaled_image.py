"""Compare complete post-scaled hardware images with sequence-specific bounds."""
import argparse
from bisect import bisect_left, bisect_right
import gzip
import hashlib
import json
from pathlib import Path
from tools.probes.analyze_cxform_intervals import coefficient_measurements, f32, float_bits
from tools.probes.analyze_cxform_signed_bounds import EVIDENCE

DOMAINS = ((0x3f800000,0x437f0000),(0x437f0000,0x477e0100),
           (0x3b800000,0x3f800000),(0x3b800000,0x3f800000))
NAMES = ('integer_scaled','product_scaled_twice','quotient_divide_multiply','estimated_normalizer_scaled')
CONSTRUCTIONS = ('estimate_inverse','estimate_product','estimate_quotient','estimated_normalizer')


def decode(text, form):
    first,last = DOMAINS[form]
    lines = text.splitlines()
    header = lines[0].split()
    if header[:6]!=['form',str(form),'domain',f'{first:08x}',f'{last:08x}','csr'] or int(header[6],16)&0x6000:
        raise ValueError('Wrong post-scale domain or mode')
    runs,expected = [],first
    for line in lines[1:-1]:
        start,end,value = (int(v,16) for v in line.split())
        if start!=expected or end<start or end>last or (runs and value>=runs[-1][2]):
            raise ValueError('Missing, overlapping, reordered or nondecreasing run')
        runs.append((start,end,value))
        expected=end+1
    if expected!=last+1 or lines[-1]!=f'done {last-first+1} rises 0':
        raise ValueError('Incomplete post-scaled image')
    return runs


def analyze(directory):
    root = EVIDENCE/'r55'
    raw = (root/'analysis.json.gz').read_bytes()
    pin = json.loads((root/'provenance.json').read_text())['output_sha256']['analysis.json.gz']
    if hashlib.sha256(raw).hexdigest()!=pin:
        raise ValueError('Pinned bounds changed')
    bounds = json.loads(gzip.decompress(raw))
    measured = coefficient_measurements(EVIDENCE/'r41')
    images = {}
    for form,name in enumerate(NAMES):
        runs = decode((directory/f'hardware-{form}.txt').read_text(),form)
        starts = [v[0] for v in runs]
        for a in range(1,256):
            value = (float(a),f32(a*255),f32(a/255),f32(a*measured[255]['estimate_inverse']))[form]
            bits = float_bits(value)
            index = bisect_right(starts,bits)-1
            run = runs[index]
            expected = float_bits(f32(measured[a][CONSTRUCTIONS[form]]*255))
            if not run[0]<=bits<=run[1] or run[2]!=expected:
                raise ValueError(f'Independent measured-construction regression: {name} alpha{a}')
        outputs = sorted(v[2] for v in runs)
        models = {}
        for mode,model in bounds['models'].items():
            rows = {}
            for alpha,b in model['intervals'].items():
                lo,hi = b['low_bits'],b['high_bits']
                rows[alpha] = {'low_bits':lo,'high_bits':hi,
                    'reachable_output_count':bisect_right(outputs,hi)-bisect_left(outputs,lo),
                    'lower_witness':b['lower_witness'],'upper_witness':b['upper_witness']}
            models[mode] = {'alphas':rows,'unreachable_alphas':[int(a) for a,v in rows.items() if not v['reachable_output_count']]}
        first,last = DOMAINS[form]
        images[name] = {'domain_bits':[first,last],'input_count':last-first+1,'runs':len(runs),
                        'old_construction_controls_exact':255,'models':models}
    return {'images':images,'coefficients_selected':False,'hardware_instruction_inference':False,
            'candidate_admitted':False,'gpu_advance_allowed':False,'production_admitted':False}


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--hardware',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    report = analyze(args.hardware)
    args.output.write_bytes(gzip.compress((json.dumps(report,indent=2)+'\n').encode(),mtime=0))
    for name,image in report['images'].items():
        print(name,image['input_count'],image['runs'],
              {k:v['unreachable_alphas'] for k,v in image['models'].items()})
    raise SystemExit(1)
