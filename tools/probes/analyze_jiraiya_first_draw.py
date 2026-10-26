"""Reject or support draw-order dependence using independent fresh wrapper instances."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
from PIL import Image
from tools.probes.analyze_jiraiya_filter_boundary import ROOT,decode as boundary_decode,comparison
from tools.probes.run_nested_filters import unpack

LABELS=('first-authored','cleared-0','cleared-1','cleared-2','next-0','next-1','next-2')


def analyze(native,output):
    b=json.loads((native/'build.json').read_text())
    for p,h in [(b['source'],b['source_sha256']),(b['harness_source'],b['harness_sha256'])]:assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h
    p=native/'native.log';text=p.read_text() if p.exists() else gzip.decompress(p.with_suffix('.log.gz').read_bytes()).decode()
    rows=[s.split('|') for s in text.splitlines() if s.startswith('AIREF|')]
    assert len(rows)==2810 and rows[-1][6:]==['done','ok']
    images={k:[] for k in LABELS};props=[]
    for i,row in enumerate(rows):
        assert row[1]==b['run_id'] and row[2:4]==[str(i),'0'] and row[5]=='0'
        if row[6]=='props':props.append(row[7].split(','))
        elif row[6]=='row':
            label,y,values=row[7].split(',',2);assert len(images[label])==int(y)*600
            v=list(map(int,values.split(',')));assert len(v)==1200;images[label].extend(unpack(v))
        else:assert row[6]=='done'
    assert all(len(v)==240000 for v in images.values())
    refs,_,_=boundary_decode(ROOT/'evidence/importer-loud-fail/r93/native')
    scores={};output.mkdir(parents=True,exist_ok=True)
    for label,pixels in images.items():
        reference='authored' if label=='first-authored' else 'cleared'
        scores[label]=comparison(pixels,refs[reference]['rgba'])
        Image.frombytes('RGBA',(600,400),bytes(c for p in pixels for c in p)).save(output/(label+'.png'))
    return {'properties':props,'comparisons':scores,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=analyze(a.native,a.output);(a.output/'analysis.json').write_text(json.dumps(r,separators=(',',':'))+'\n');print({k:(v['exact'],v['samples'],v['max_channel_delta']) for k,v in r['comparisons'].items()})
