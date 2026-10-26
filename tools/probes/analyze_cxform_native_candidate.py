"""Validate the static byte-domain candidate without enabling production."""
import argparse
from collections import Counter
import gzip
import json
from pathlib import Path
from unittest.mock import patch

from tools.probes.analyze_cxform_signed_bounds import controls, EVIDENCE
from tools.probes import analyze_cxform_rows as prior
from tools.probes.analyze_cxform_alpha import alpha_samples, extent_samples
from tools.probes.native_cxform_candidate import channel, pixel, bounded, construction


def analyze():
    old,signed = controls()
    scores = {}
    for name,rows in (('old',old),('signed',signed)):
        counts = Counter((tuple(args),target) for _,args,target in rows)
        failures = []
        for (args,target),count in counts.items():
            actual = channel(args)
            if actual!=target:
                failures.append({'args':args,'native':target,'actual':actual,'count':count})
        scores[name] = {'channels':len(rows),'exact':len(rows)-sum(v['count'] for v in failures),'failures':failures}
    original = prior.long_cx
    def injected(source,opacity,reciprocals,estimated=True):
        return pixel(source,opacity) if estimated else original(source,opacity,reciprocals,False)
    # Reuse the immutable pinned harness; retain its original negative control.
    with patch.object(prior,'long_cx',injected):
        regressions = prior.analyze(EVIDENCE/'r39',EVIDENCE/'r38')
    if prior.long_cx is not original:
        raise ValueError('Diagnostic injection escaped its scope')
    alpha = prior.score((key,bounded(p,op,32,key[1]),native) for key,p,native,op in alpha_samples(EVIDENCE/'r40/alpha'))
    opacity = prior.score((key,bounded(p,op,32,key[1]),native) for key,p,native,op in alpha_samples(EVIDENCE/'r40/opacity',(1,33,67,99)))
    extents = list(extent_samples(EVIDENCE/'r40/extents'))
    geometry = {}
    for intersection in (False,True):
        for a in (135,197):
            pairs = []
            for key,p,native,alpha_value,op,width,start,tx in extents:
                if alpha_value!=a:
                    continue
                x = key[1]
                lo,hi = max(0,start,tx),min(640,start+width,tx+600)
                left,length = (lo,hi-lo) if intersection else (start,width)
                actual = bounded(p,op,length,x-left) if lo<=x<hi else [0]*4
                pairs.append((key,actual,native))
            geometry[('intersection_' if intersection else 'clip_only_')+str(a)] = prior.score(pairs)
    passed = (all(v['exact']==v['channels'] for v in scores.values()) and regressions['cpu_hypothesis_passed']
              and all(v['exact']==v['pixels'] for v in (alpha,opacity,geometry['intersection_135'],geometry['intersection_197'])))
    return {'scores':scores,'prior_regressions':regressions,'all_alpha':alpha,'nonbinary_opacity':opacity,
            'geometry':geometry,'construction_witnesses':construction()[2],
            'cpu_arithmetic_passed':passed,'candidate_admitted':passed,'gpu_advance_allowed':passed,
            'execution_routing_verified':False,'production_admitted':False,
            'scope':'Bounded behavioral arithmetic gate only; no executed Flash instruction claim.'}


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    report = analyze()
    args.output.write_bytes(gzip.compress((json.dumps(report,indent=2)+'\n').encode(),mtime=0))
    print('native controls',{k:(v['exact'],v['channels']) for k,v in report['scores'].items()})
    print('prior',{k:(v['exact'],v['pixels']) for k,v in report['prior_regressions']['scores'].items()})
    print('all alpha',report['all_alpha']['exact'],report['all_alpha']['pixels'])
    print('opacity',report['nonbinary_opacity']['exact'],report['nonbinary_opacity']['pixels'])
    print('geometry',{k:(v['exact'],v['pixels']) for k,v in report['geometry'].items()})
    print('CPU',report['cpu_arithmetic_passed'],'GPU permitted',report['gpu_advance_allowed'])
    raise SystemExit(0 if report['cpu_arithmetic_passed'] else 1)
