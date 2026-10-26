"""Check explicit removal/Stop frame states against pinned original native clocks."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import struct
from tools.probes.build_bound_bitmap_component import ROOT,source_tags


def analyze(fixture):
    case=fixture['case'];path=ROOT/case['source']['path'];assert hashlib.sha256(path.read_bytes()).hexdigest()==case['source']['sha256']
    tags={str(struct.unpack_from('<H',p)[0]):(c,p,r) for c,p,r in source_tags(path) if c in (2,20,21,35,36,39,90)}
    for cid,digest in fixture['raw_tag_sha256'].items():assert hashlib.sha256(tags[cid][2]).hexdigest()==digest
    frame=1;predicted=[]
    for tick in range(101):
        state=fixture['frames'][frame-1];predicted.append({'tick':tick,'frame':frame,'shape_id':state['shape_id']})
        if state['playing_after_actions']:frame=frame%len(fixture['frames'])+1
    folder=ROOT/'evidence/importer-loud-fail/r21/components'/path.stem
    clocks=json.loads((folder/'clocks.json').read_text());cases=json.loads((ROOT/'evidence/importer-loud-fail/r32/components'/path.stem/'cases.json').read_text());rows=[]
    for c in cases:
        if c['symbol']!=case['symbol']:continue
        values=[v for v in clocks if v['path']==c['id']+'/'+str(c['placement']['depth'])]
        assert len(values)==101 and [v['tick'] for v in values]==list(range(101))
        rows.append({'case':c['id'],'samples':101,'exact':sum(a['frame']==b['frame'] for a,b in zip(values,predicted))})
    return {'source':case['source'],'frames':fixture['frames'],'actions':fixture['actions'],'native_clocks':rows,'leaves':[{'shape_id':v['shape_id'],'bitmap_id':v['bitmap_id'],'size':[v['width'],v['height']],'smooth_sampling':v['smooth_sampling'],'encoding_tag':tags[str(v['bitmap_id'])][0],'lossless_format':tags[str(v['bitmap_id'])][1][2],'sampler_admitted':False} for v in fixture['leaves'].values()],'empty_frames':[i+1 for i,v in enumerate(fixture['frames']) if v['shape_id'] is None],'diagnostic_clock_exact':all(v['exact']==v['samples'] for v in rows),'production_admitted':False,'full_as_ownership_proved':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--fixture',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();data=a.fixture.read_bytes();fixture=json.loads(gzip.decompress(data) if a.fixture.suffix=='.gz' else data);r=analyze(fixture);a.output.write_text(json.dumps(r,indent=2)+'\n');print(r['native_clocks']);raise SystemExit(0 if r['diagnostic_clock_exact'] else 1)
