"""Amplify common reciprocal differences without selecting fitted coefficients."""
import argparse
import copy
import gzip
import hashlib
import json
from pathlib import Path

from tools.probes.analyze_cxform_alpha import ROOT, capture_rows
from tools.probes.analyze_cxform_intervals import (
    CONSTRUCTIONS, OPACITIES, channel, coefficient_measurements, constraints, f32,
)
from tools.probes.analyze_cxform_identity import membership, read_previous
from tools.probes.nested_composition import rgba
from tools.probes.run_nested_filters import unpack

ALPHAS = (146,197,206,244)
GAINS = (2,4,8)


def read_samples(directory):
    identities = []
    for a in ALPHAS:
        for gain in GAINS:
            for adjacent in (-1,0,1):
                for offset in (-1,0,1):
                    for op in OPACITIES:
                        identities.append([len(identities),a,gain*256+adjacent,-(gain-1)*128+offset,op])
    samples = []
    for row in capture_rows(directory,identities):
        index,a,m,d,op = row[:5]
        for x in range(32):
            source,native = unpack(row[5+x*4:9+x*4])
            expected = rgba((117<<16)|((120+x%16)<<8)|240,a)
            if source!=expected:
                raise ValueError('Amplified source readback changed')
            if native[3]!=a*(op*256//100)//256:
                raise ValueError('Amplified alpha changed')
            # Check the actual premultiplied input, not the requested RGB value.
            numerator = source[1]*m*255+d*a*256
            if not 0<numerator<a*256*255:
                raise ValueError('Probe reaches green clamping')
            if not 0<native[1]<native[3]:
                raise ValueError('Native output reaches green clamping')
            samples.append((index,x,source,native,m,d,op))
    return samples


def previous_report():
    read_previous()  # Check the r41 evidence on which r42 depends as well.
    root = ROOT/'evidence/importer-loud-fail/r42'
    provenance = json.loads((root/'provenance.json').read_text())
    raw = (root/'analysis.json.gz').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=provenance['output_sha256']['analysis.json.gz']:
        raise ValueError('Pinned r42 intervals changed')
    return json.loads(gzip.decompress(raw))


def intersect(old, added):
    result = copy.deepcopy(old)
    for value in result.values():
        for field in ('lower_witness','upper_witness'):
            if value[field]:
                value[field]['key'] = ['r42',*value[field]['key']]
    for a,value in added.items():
        current = result.setdefault(str(a),copy.deepcopy(value))
        for bound,witness,better in (('low_bits','lower_witness',int.__gt__),
                                     ('high_bits','upper_witness',int.__lt__)):
            if better(value[bound],current[bound]):
                current[bound],current[witness] = value[bound],value[witness]
    return result


def analyze(root):
    rows = read_samples(root/'native')
    previous = previous_report()
    measured = coefficient_measurements(ROOT/'evidence/importer-loud-fail/r41')
    green,combined = [],[]
    for i,x,p,n,m,d,op in rows:
        for ch,mul,offset in ((0,128,8),(1,m,d),(2,256,-4)):
            sample = (['amplified',i,x,ch],(p[ch],p[3],mul,offset,op),n[ch])
            combined.append(sample)
            if ch==1:
                green.append(sample)
    reports = {}
    for space in ('unit','normalized','byte'):
        for order in ('alpha_first','opacity_first','joint'):
            key = space+'/'+order
            old = previous['green_intersections'][key]['intervals']
            merged = intersect(old,constraints(green,space,order))
            report = {'green_intervals':merged,
                      'empty_green_alphas':[a for a,v in merged.items() if v['low_bits']>v['high_bits']]}
            if order=='alpha_first':
                old = previous['combined_intersections'][space]['intervals']
                merged = intersect(old,constraints(combined,space,order))
                report.update(combined_intervals=merged,
                              total_constraints=previous['combined_intersections'][space]['total_constraints']+len(combined),
                              empty_combined_alphas=[a for a,v in merged.items() if v['low_bits']>v['high_bits']],
                              tightened_alphas=[a for a,v in merged.items() if (v['low_bits'],v['high_bits'])!=(old[a]['low_bits'],old[a]['high_bits'])],
                              membership=membership(merged,measured,space))
            scores = {}
            for name in CONSTRUCTIONS:
                failures = []
                maximum = 0
                for location,args,target in green:
                    coefficient = measured[args[1]][name]
                    if space!='unit':
                        coefficient = f32(coefficient*255)
                    actual = channel(args,coefficient,space,order)
                    if actual!=target:
                        maximum = max(maximum,abs(actual-target))
                        failures.append({'key':location,'args':list(args),'native':target,'actual':actual})
                scores[name] = {'samples':len(green),'exact':len(green)-len(failures),
                                'max_delta':maximum,'failures':failures}
            report['independent_constructions'] = scores
            reports[key] = report
    return {'pixels':len(rows),'new_rgb_constraints':len(combined),'models':reports,
            'candidate_admitted':False,'gpu_advance_allowed':False,'production_admitted':False,
            'scope':'Fixed transforms and routing; intervals constrain but never supply rendered coefficients.'}


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    report = analyze(args.root)
    args.output.write_bytes(gzip.compress((json.dumps(report,indent=2)+'\n').encode(),mtime=0))
    for key,model in report['models'].items():
        print(key,'empty',model['empty_green_alphas'],model.get('empty_combined_alphas'),
              'tightened',model.get('tightened_alphas'),
              'exact',{k:v['exact'] for k,v in model['independent_constructions'].items()})
    raise SystemExit(1)
