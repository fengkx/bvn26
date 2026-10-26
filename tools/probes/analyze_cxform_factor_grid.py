"""Exhaust the predefined measured factorization grid, never select by alpha."""
import argparse
from collections import Counter
import gzip
import json
from pathlib import Path

from tools.probes.analyze_cxform_intervals import coefficient_measurements, CONSTRUCTIONS
from tools.probes.analyze_cxform_rejected import measurements
from tools.probes.analyze_cxform_scaled_inverse import evaluate
from tools.probes.analyze_cxform_signed_bounds import controls, EVIDENCE


def analyze():
    measured = coefficient_measurements(EVIDENCE/'r41')
    normalization = measurements(EVIDENCE/'r44')
    old,signed = controls()
    counts = {name:Counter((tuple(args),target) for _,args,target in rows)
              for name,rows in {'old':old,'signed':signed}.items()}
    sites = [((25,49,-129,128,100),12),((23,49,2046,-894,100),11),
             ((31,33,256,-4,33),9),((32,33,191,1,100),23)]
    models = {}
    for construction in CONSTRUCTIONS:
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
                models[construction+'/'+mode+'/'+form] = {'scores':scores,'sites':[
                    {'args':args,'native':target,'actual':evaluate(args,table,inverse,form)} for args,target in sites]}
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
        print(name,'sites',[p['actual'] for p in m['sites']],{k:v['exact'] for k,v in m['scores'].items()})
    raise SystemExit(1)
