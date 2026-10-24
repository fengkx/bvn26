"""Fixed-source multiplier/offset brackets; never splice locally matching paths."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

from tools.probes.analyze_cxform_adjacent import SITES, previous_report, read_native as read_adjacent
from tools.probes.analyze_cxform_alpha import capture_rows
from tools.probes.analyze_cxform_intervals import coefficient_measurements
from tools.probes.analyze_cxform_rejected import (
    EVIDENCE, measurements, old_samples, read_native as read_rejected, rgb, sequence,
)
from tools.probes.cxform_control_analysis import evaluate
from tools.probes.run_nested_filters import unpack
from tools.probes.nested_composition import rgba

MULTIPLIER_DELTAS = (-2,-1,0,1,2)
OFFSET_DELTAS = (-256,-1,0,1,256)


def prior():
    previous_report()
    root = EVIDENCE/'r45'
    raw = (root/'analysis.json.gz').read_bytes()
    provenance = json.loads((root/'provenance.json').read_text())
    if hashlib.sha256(raw).hexdigest()!=provenance['output_sha256']['analysis.json.gz']:
        raise ValueError('Pinned r45 evidence changed')
    return json.loads(gzip.decompress(raw))


def sources():
    old = prior()
    normal = measurements(EVIDENCE/'r44')
    selected = {}
    # Diagnostic case selection is frozen to prior failures, not a rendering rule.
    for v in old['targets']:
        _,_,m,d,op = SITES[v['site']]
        args = (v['source'][1],v['alpha'],m,d,op)
        failed = any(sequence(args,table,'alpha_first')!=v['native'][1] for table in normal.values())
        if failed or v['delta_green']==0:
            selected.setdefault((v['site'],tuple(v['source'])),v)
    return list(selected.values())


def read_native(directory):
    adjacent,_ = read_adjacent(EVIDENCE/'r45/native')
    reference = {(i,x):(p,n) for i,x,p,n,m,d,op in adjacent}
    identities = []
    for v in sources():
        site,a,dg,ref = v['site'],v['alpha'],v['delta_green'],v['key'][0]
        _,_,m,d,op = SITES[site]
        for dm in MULTIPLIER_DELTAS:
            for dd in OFFSET_DELTAS:
                identities.append([len(identities),ref,site,a,dg,m+dm,d*256+dd,op])
    samples,targets,clipping = [],[],[]
    centered = 0
    for row in capture_rows(directory,identities):
        i,ref,site,a,dg,m,d256,op = row[:8]
        for x in range(32):
            p,n = unpack(row[8+x*4:12+x*4])
            expected,baseline = reference[ref,x]
            if p!=expected:
                raise ValueError('Fixed premultiplied source changed')
            if n[3]!=a*(op*256//100)//256:
                raise ValueError('Bracket alpha changed')
            if (m,d256)==(SITES[site][2],SITES[site][3]*256):
                if n!=baseline:
                    raise ValueError('Centered transform changed')
                centered += 1
            numerator = p[1]*m*255+d256*a
            clipped = not 0<numerator<a*256*255
            if clipped:
                clipping.append([i,x])
            samples.append((i,x,p,n,m,d256/256,op))
            if x==SITES[site][1]:
                targets.append({'key':[i,x],'reference':[ref,x],'site':site,'source':p,'native':n,
                                'multiplier':m,'offset_256':d256,'opacity':op,'clipped':clipped})
    return samples,targets,clipping,centered


def read_offset_controls(directory):
    identities = []
    for a in (49,51,135,204,255):
        for d in (-513,-512,-511,-257,-256,-255,-1,0,1,255,256,257,511,512,513):
            identities.append([len(identities),a,d,d])
    samples = []
    outputs = {}
    for row in capture_rows(directory,identities):
        i,a,d,property_value = row[:4]
        for x in range(32):
            p,n = unpack(row[4+x*4:8+x*4])
            if p!=rgba(0x7580f0,a) or n[3]!=a:
                raise ValueError('Offset control input/alpha changed')
            outputs[a,d,x] = n
            samples.append((i,x,p,n,256,d/256,100))
    failures = []
    for (a,d,x),n in outputs.items():
        integer_native = outputs[a,int(d/256)*256,x]
        if n!=integer_native:
            failures.append({'alpha':a,'offset_256':d,'x':x,'native':n,'integer_native':integer_native})
    return samples,{'pixels':len(samples),'property_fraction_preserved':True,
                    'truncation_exact':len(samples)-len(failures),'failures':failures}


def truncate_offsets(samples):
    return [(key,(*args[:3],int(args[3]),args[4]),target) for key,args,target in samples]


def analyze(root):
    old = prior()
    rows,targets,clipping,centered = read_native(root/'native')
    rejected,_ = read_rejected(EVIDENCE/'r44/native')
    adjacent,_ = read_adjacent(EVIDENCE/'r45/native')
    previous = list(old_samples())+list(rgb(rejected,'r44'))+list(rgb(adjacent,'r45'))
    if len(previous)!=1101888:
        raise ValueError('Old controls omitted')
    offsets,offset_report = read_offset_controls(root/'offset')
    added = list(rgb(rows,'brackets'))+list(rgb(offsets,'offset'))
    keys = {tuple(v['key']) for v in targets}
    target_samples = [v for v in added if v[0][0]=='brackets' and v[0][-1]==1 and tuple(v[0][1:3]) in keys]
    result = evaluate(old,added,previous,target_samples,
                      coefficient_measurements(EVIDENCE/'r41'),measurements(EVIDENCE/'r44'),'r45')
    adjusted = evaluate(old,truncate_offsets(added),truncate_offsets(previous),truncate_offsets(target_samples),
                        coefficient_measurements(EVIDENCE/'r41'),measurements(EVIDENCE/'r44'),'r45')
    result['truncated_offset_candidate'] = adjusted
    result['offset_controls'] = offset_report
    result.update(pixels=len(rows),target_pixels=len(targets),targets=targets,
                  sources=len(sources()),clipping=clipping,centered_exact=centered)
    return result


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    report = analyze(args.root)
    args.output.write_bytes(gzip.compress((json.dumps(report,indent=2)+'\n').encode(),mtime=0))
    print({k:report[k] for k in ('pixels','target_pixels','sources','centered_exact')})
    print('clipping',len(report['clipping']))
    for key,v in report['models'].items():
        print(key,'empty',v['empty_green_intervals'],v.get('empty_combined_intervals'),
              {n:m['inside'] for n,m in v.get('membership_combined_intervals',{}).items()})
    for key,v in report['direct_sequences'].items():
        print(key,{n:{k:q for k,q in m.items() if k!='failures'} for n,m in v.items()},
              'target',report['target_sequences'][key]['exact'])
    print('offset_controls',report['offset_controls'])
    for key,v in report['truncated_offset_candidate']['models'].items():
        print('truncated',key,'empty',v['empty_green_intervals'],v.get('empty_combined_intervals'))
    for key,v in report['truncated_offset_candidate']['target_sequences'].items():
        print('truncated target',key,v['exact'])
    raise SystemExit(1)
