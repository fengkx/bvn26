"""Combine bounded nearest sampling and geometry coverage on complete source leaf images."""
import argparse
from pathlib import Path
import json
from tools.probes.analyze_nearest_component_input import decode
from tools.probes.analyze_affine_heldout import inverse_signed
from tools.probes.analyze_affine_rounded_footprint import indices
from tools.probes.analyze_affine_scan_translation import vertices, fixed_scan


def analyze(native):
    fixture, source, cases = decode(native)
    leaf = fixture['leaf']
    assert leaf['fill']['fillStyleType'] == '67' and leaf['smooth_sampling'] is False
    assert leaf['fill_masks'] == [[[[137.0,0.0],[137.0,200.0],[0.0,200.0],[0.0,0.0]]]]
    rows = []
    for case in cases:
        key = case['key']
        co = inverse_signed(['0']*5 + key[3:15])
        counts = fixed_scan(vertices(['0']*3+['137','200']+key[3:15]), 0, 0, 600, 400, 16, 'trunc')
        scores = {name: {'samples': 0, 'exact': 0, 'max_channel_delta': 0, 'failures': []}
                  for name in ('clamp', 'clear')}
        outside = []
        for i, count in enumerate(counts):
            x,y = i%600,i//600
            actual = {'clamp':[0]*4, 'clear':[0]*4}
            if count:
                ix,iy = indices(co,x,y,'ties_even')
                clamped = source[max(0,min(199,iy))*137+max(0,min(136,ix))]
                actual['clamp'] = [v*count//16 for v in clamped]
                if 0<=ix<137 and 0<=iy<200:
                    actual['clear'] = actual['clamp']
                else:
                    outside.append({'x':x,'y':y,'source_indices':[ix,iy], 'coverage_count':count,
                                    'clamped_texel':clamped,'native':case['pixels'][i]})
            for name, pixel in actual.items():
                expected=case['pixels'][i];score=scores[name]
                score['samples']+=1;score['exact']+=pixel==expected
                score['max_channel_delta']=max(score['max_channel_delta'],max(abs(p-q) for p,q in zip(pixel,expected)))
                if pixel!=expected:score['failures'].append({'x':x,'y':y,'actual':pixel,'native':expected})
        rows.append({'epoch':key[1],'case':key[2],'matrix_properties':key[3:15],
                     'scores':scores,'out_of_source_footprints':outside,
                     'outside_nonzero_native':sum(bool(v['native'][3]) for v in outside)})
    return {'source_texels_exact':len(source),'raw_source_metadata_preserved':True,'rows':rows,
            'scope':'complete untinted nearest leaf only; wrapper filters/CXFORM excluded',
            'complete_wrapper_admitted':False,'production_admitted':False,'full_production_suite_rerun':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    r=analyze(a.native);a.output.write_text(json.dumps(r,separators=(',',':'))+'\n')
    for v in r['rows']:
        print(v['epoch'],v['case'],[(k,s['exact'],s['samples']) for k,s in v['scores'].items()],len(v['out_of_source_footprints']),v['outside_nonzero_native'])
