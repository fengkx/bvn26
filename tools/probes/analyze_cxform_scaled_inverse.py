"""Construct normalized inverse from integer alpha; never fit coefficients."""
import argparse
from collections import Counter
import gzip
import json
from pathlib import Path
from tools.probes.analyze_cxform_intervals import coefficient_measurements, f32
from tools.probes.analyze_cxform_rejected import measurements
from tools.probes.analyze_cxform_signed_bounds import controls, EVIDENCE


def evaluate(args, normalizer, inverse, form):
    c,a,m,d,op = args
    source = normalizer[c][0] if c else 0.0
    normalized_inverse = f32(inverse[a]*255)
    if form=='source_first':
        value = f32(f32(f32(source*normalized_inverse)*f32(m/256))+f32(d/255))
    elif form=='gain_first':
        value = f32(f32(source*f32(normalized_inverse*f32(m/256)))+f32(d/255))
    else:
        raise ValueError('Unknown global operation order')
    return int(f32(f32(max(0,min(1,value))*a)*f32((op*256//100)/256)))


def analyze():
    measured = coefficient_measurements(EVIDENCE/'r41')
    normalization = measurements(EVIDENCE/'r44')
    old,signed = controls()
    counts = {name:Counter((tuple(args),target) for _,args,target in rows)
              for name,rows in {'old':old,'signed':signed}.items()}
    pair = [((25,49,-129,128,100),12),((23,49,2046,-894,100),11)]
    models = {}
    for construction in ('estimate_inverse','rounded_inverse'):
        inverse = {a:v[construction] for a,v in measured.items()}
        for mode,table in normalization.items():
            for form in ('source_first','gain_first'):
                scores = {}
                for group,rows in counts.items():
                    exact,total,failures = 0,0,[]
                    for (args,target),count in rows.items():
                        actual = evaluate(args,table,inverse,form)
                        total += count
                        if actual==target:
                            exact += count
                        else:
                            failures.append({'args':args,'native':target,'actual':actual,'count':count})
                    scores[group] = {'exact':exact,'total':total,'failures':failures}
                models[construction+'/'+mode+'/'+form] = {'scores':scores,
                    'pair':[{'args':args,'native':target,'actual':evaluate(args,table,inverse,form)} for args,target in pair]}
    return {'models':models,'old_constraints':len(old),'signed_constraints':len(signed),
            'old_bounds_retained_not_reinterpreted':True,
            'candidate_admitted':False,'gpu_advance_allowed':False,'production_admitted':False}


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    report = analyze()
    args.output.write_bytes(gzip.compress((json.dumps(report,indent=2)+'\n').encode(),mtime=0))
    for name,m in report['models'].items():
        print(name,'pair',[p['actual'] for p in m['pair']],{k:v['exact'] for k,v in m['scores'].items()})
    raise SystemExit(1)
