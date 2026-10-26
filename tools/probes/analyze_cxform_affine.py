"""Test fixed precomputed-affine operation orders, without fitted reciprocals."""
import argparse
from collections import Counter
import gzip
import json

from tools.probes.analyze_cxform_intervals import coefficient_measurements, f32, float_bits
from tools.probes.analyze_cxform_refinement import load_bounds
from tools.probes.analyze_cxform_signed_bounds import controls, EVIDENCE


def affine(args, reciprocal, form):
    c,a,m,d,op = args
    gain = f32(reciprocal*f32(m/256))
    bias = f32(d/255)
    opacity = f32((op*256//100)/256)
    if form=='unit_gain':
        value = max(0,min(1,f32(f32(c*gain)+bias)))
        return int(f32(f32(value*a)*opacity))
    if form=='premultiplied_gain':
        gain,bias = f32(gain*a),f32(bias*a)
        value = max(0,min(a,f32(f32(c*gain)+bias)))
        return int(f32(value*opacity))
    raise ValueError('Unknown fixed affine operation order')


def analyze():
    measured = coefficient_measurements(EVIDENCE/'r41')
    old = load_bounds()
    previous,signed = controls()
    rows = {'old':previous,'signed':signed}
    counts = {name:Counter((tuple(args),target) for _,args,target in group) for name,group in rows.items()}
    witness = old['models']['unit/alpha_first']['combined_intervals']['49']['upper_witness']
    pair = [((25,49,-129,128,100),12),(tuple(witness['args']),witness['native_channel'])]
    models = {}
    for name in measured[1]:
        table = {a:v[name] for a,v in measured.items()}
        # Old bounds describe the old operation order only, never this affine path.
        outside_old = [int(a) for a,b in old['models']['unit/alpha_first']['combined_intervals'].items()
                       if not b['low_bits']<=float_bits(table[int(a)])<=b['high_bits']]
        for form in ('unit_gain','premultiplied_gain'):
            scores = {}
            for group,samples in counts.items():
                exact,total,failures = 0,0,[]
                for (args,target),count in samples.items():
                    actual = affine(args,table[args[1]],form)
                    total += count
                    if actual==target:
                        exact += count
                    else:
                        failures.append({'args':args,'native':target,'actual':actual,'count':count})
                scores[group] = {'exact':exact,'total':total,'failures':failures}
            models[name+'/'+form] = {'scores':scores,
                'pair':[{'args':args,'native':target,'actual':affine(args,table[args[1]],form)} for args,target in pair],
                'original_order_outside_alphas':outside_old}
    return {'models':models,'original_order_bounds_are_not_affine_bounds':True,
            'old_constraints':len(previous),'signed_constraints':len(signed),
            'candidate_admitted':False,'gpu_advance_allowed':False,'production_admitted':False}


if __name__=='__main__':
    from pathlib import Path
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    report = analyze()
    args.output.write_bytes(gzip.compress((json.dumps(report,indent=2)+'\n').encode(),mtime=0))
    for name,model in report['models'].items():
        print(name,'pair',[v['actual'] for v in model['pair']],
              'scores',{k:v['exact'] for k,v in model['scores'].items()})
    raise SystemExit(1)
