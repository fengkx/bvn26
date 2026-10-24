"""Fixed offset normalization must satisfy pure-offset and signed/old controls."""
import argparse
from collections import Counter
import gzip
import json
from pathlib import Path

from tools.probes.analyze_cxform_intervals import coefficient_measurements, f32
from tools.probes.analyze_cxform_refinement import load_bounds
from tools.probes.analyze_cxform_signed_bounds import controls, EVIDENCE


def evaluate(args, reciprocal, offset_reciprocal, form):
    c,a,m,d,op = args
    bias = f32(d*offset_reciprocal)
    opacity = f32((op*256//100)/256)
    if form=='source_first':
        value = f32(f32(f32(c*reciprocal)*f32(m/256))+bias)
    elif form=='unit_gain':
        value = f32(f32(c*f32(reciprocal*f32(m/256)))+bias)
    elif form=='premultiplied_gain':
        gain = f32(f32(reciprocal*f32(m/256))*a)
        value = max(0,min(a,f32(f32(c*gain)+f32(bias*a))))
        return int(f32(value*opacity))
    else:
        raise ValueError('Unknown fixed source operation order')
    return int(f32(f32(max(0,min(1,value))*a)*opacity))


def analyze():
    measured = coefficient_measurements(EVIDENCE/'r41')
    bounds = load_bounds()
    old,signed = controls()
    pure = [(key,args,target) for key,args,target in old if key[0]=='zero' and key[-1]==1]
    if len(pure)!=3840 or any(args[0]!=0 for _,args,_ in pure):
        raise ValueError('Independent pure-offset controls omitted or changed')
    counts = {name:Counter((tuple(args),target) for _,args,target in rows)
              for name,rows in {'old':old,'signed':signed,'pure_offset_green':pure}.items()}
    witness = bounds['models']['unit/alpha_first']['combined_intervals']['49']['upper_witness']
    pair = [((25,49,-129,128,100),12),(tuple(witness['args']),witness['native_channel'])]
    offsets = {'rounded':f32(1/255),'measured_estimate':measured[255]['estimate_inverse']}
    models = {}
    for name in measured[1]:
        for mode,bias_reciprocal in offsets.items():
            for form in ('source_first','unit_gain','premultiplied_gain'):
                scores = {}
                for group,rows in counts.items():
                    exact,total,failures = 0,0,[]
                    for (args,target),count in rows.items():
                        actual = evaluate(args,measured[args[1]][name],bias_reciprocal,form)
                        total += count
                        if actual==target:
                            exact += count
                        else:
                            failures.append({'args':args,'native':target,'actual':actual,'count':count})
                    scores[group] = {'exact':exact,'total':total,'failures':failures}
                models[name+'/'+mode+'/'+form] = {'scores':scores,
                    'pair':[{'args':args,'native':target,'actual':evaluate(args,measured[args[1]][name],bias_reciprocal,form)} for args,target in pair]}
    return {'models':models,'old_constraints':len(old),'signed_constraints':len(signed),
            'pure_offset_green_controls':len(pure),'old_bounds_retained_not_reinterpreted':True,
            'candidate_admitted':False,'gpu_advance_allowed':False,'production_admitted':False}


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    report = analyze()
    args.output.write_bytes(gzip.compress((json.dumps(report,indent=2)+'\n').encode(),mtime=0))
    for name,m in report['models'].items():
        print(name,'pair',[v['actual'] for v in m['pair']],
              'scores',{k:v['exact'] for k,v in m['scores'].items()})
    raise SystemExit(1)
