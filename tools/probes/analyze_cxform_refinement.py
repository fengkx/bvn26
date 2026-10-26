"""Reject fixed Newton reciprocal constructions against signed and old controls.

Construction definitions never read feasibility endpoints or output pixels. Each
float32 operation is explicit; this does not assert Flash uses Newton refinement.
"""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path

from tools.probes.analyze_cxform_intervals import channel, coefficient_measurements, f32, float_bits
from tools.probes.analyze_cxform_rejected import measurements
from tools.probes.analyze_cxform_signed_bounds import controls, EVIDENCE


def refine(value, seed, form):
    if form=='product':
        return f32(seed*f32(2.0-f32(value*seed)))
    if form=='residual':
        return f32(seed+f32(seed*f32(1.0-f32(value*seed))))
    raise ValueError('Unknown independently defined refinement')


def constructions():
    measured = coefficient_measurements(EVIDENCE/'r41')
    normal = measurements(EVIDENCE/'r44')
    result = {}
    for form in ('product','residual'):
        for count in (1,2):
            table = {}
            for a in range(1,256):
                r = measured[a]['estimate_inverse']
                for _ in range(count):
                    r = refine(float(a),r,form)
                table[a] = r
            result[f'integer_{form}_{count}'] = table
        for mode,values in normal.items():
            table = {}
            for a in range(1,256):
                normalized,seed = values[a]
                refined = refine(normalized,seed,form)
                table[a] = f32(refined*values[1][0])
            result[f'normalized_{mode}_{form}'] = table
    return result


def load_bounds():
    root = EVIDENCE/'r48'
    raw = (root/'analysis.json.gz').read_bytes()
    pin = json.loads((root/'provenance.json').read_text())['output_sha256']['analysis.json.gz']
    if hashlib.sha256(raw).hexdigest()!=pin:
        raise ValueError('Pinned signed bounds changed')
    return json.loads(gzip.decompress(raw))


def analyze():
    tables = constructions()
    old = load_bounds()
    previous,signed = controls()
    groups = {'old':previous,'signed':signed}
    counts = {name:Counter((tuple(args),target) for _,args,target in rows) for name,rows in groups.items()}
    witness = old['models']['unit/alpha_first']['combined_intervals']['49']['upper_witness']
    pair = [((25,49,-129,128,100),12),(tuple(witness['args']),witness['native_channel'])]
    report = {}
    for name,table in tables.items():
        models = {}
        for space in ('unit','normalized','byte'):
            coefficients = {a:r if space=='unit' else f32(r*255) for a,r in table.items()}
            for order in ('alpha_first','opacity_first','joint'):
                key = space+'/'+order
                model = old['models'][key]
                bound_group = 'combined_intervals' if 'combined_intervals' in model else 'green_intervals'
                bounds = model[bound_group]
                outside = [int(a) for a,b in bounds.items() if not b['low_bits']<=float_bits(coefficients[int(a)])<=b['high_bits']]
                scores = {}
                for group,rows in counts.items():
                    exact,total,failures = 0,0,[]
                    for (args,target),count in rows.items():
                        actual = channel(args,coefficients[args[1]],space,order)
                        total += count
                        if actual==target:
                            exact += count
                        else:
                            failures.append({'args':args,'native':target,'actual':actual,'count':count})
                    scores[group] = {'exact':exact,'total':total,'failures':failures}
                models[key] = {'bounds_used':bound_group,'outside_alphas':outside,'scores':scores,
                               'pair':[{'args':args,'native':target,
                                        'actual':channel(args,coefficients[args[1]],space,order)} for args,target in pair]}
        report[name] = {'coefficients_bits':{a:float_bits(v) for a,v in table.items()},'models':models}
    return {'constructions':report,'older_upper_witness':witness,
            'old_constraints':len(previous),'signed_constraints':len(signed),
            'candidate_admitted':False,'gpu_advance_allowed':False,'production_admitted':False}


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    result = analyze()
    args.output.write_bytes(gzip.compress((json.dumps(result,indent=2)+'\n').encode(),mtime=0))
    for name,v in result['constructions'].items():
        m = v['models']['unit/alpha_first']
        print(name,'pair',[(p['native'],p['actual']) for p in m['pair']],
              'outside',len(m['outside_alphas']),'scores',{k:s['exact'] for k,s in m['scores'].items()})
    raise SystemExit(1)
