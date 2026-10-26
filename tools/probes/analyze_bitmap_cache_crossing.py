"""Retain geometric-origin counterexamples on fractional bounds and held-out scale families."""
import argparse
from collections import Counter
import json
from pathlib import Path
from tools.probes.analyze_bitmap_cache_origin import analyze as base_analyze


def analyze(native):
    result=base_analyze(native,1152,1200,4,128)
    keys=result['properties'];breakdown={}
    for name,score in result['models'].items():
        counts=Counter((keys[r['case']][2],keys[r['case']][4]) for r in score['failures'])
        breakdown[name]={'max_channel_delta':max((abs(a-b) for r in score['failures'] for a,b in zip(r['actual'],r['native'])),default=0),
                         'scale_outer_failures':[{'scale':s,'outer_translation':t,'different_pixels':n} for (s,t),n in sorted(counts.items())]}
    result['breakdown']=breakdown
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=analyze(a.native);a.output.write_text(json.dumps(r,separators=(',',':'))+'\n');print({k:(s['exact'],s['samples'],r['breakdown'][k]['max_channel_delta']) for k,s in r['models'].items()})
