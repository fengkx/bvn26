"""Discriminate implicit authored filter input from explicitly materialized bitmap bytes."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
from PIL import Image
from tools.probes.analyze_jiraiya_filter_boundary import ROOT,decode as reference,comparison
from tools.probes.analyze_blur_kernel_heldout import render
from tools.probes.run_nested_filters import unpack

LABELS=('authored','input','apply','bitmap-input','bitmap-filter','input-after')


def decode(native):
    b=json.loads((native/'build.json').read_text())
    for p,h in [(b['source'],b['source_sha256']),(b['harness_source'],b['harness_sha256'])]:assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h
    p=native/'native.log';text=p.read_text() if p.exists() else gzip.decompress(p.with_suffix('.log.gz').read_bytes()).decode()
    rows=[s.split('|') for s in text.splitlines() if s.startswith('AIREF|')]
    assert len(rows)==2402 and rows[-1][6:]==['done','ok']
    images={k:[] for k in LABELS}
    for i,row in enumerate(rows):
        assert row[1]==b['run_id'] and row[2:6]==[str(i),'0','0','0']
        if i==0:assert row[6:]==['props','1,15,0,3,15,0,3']
        elif row[6]=='row':
            label,y,values=row[7].split(',',2);assert len(images[label])==int(y)*600
            v=list(map(int,values.split(',')));assert len(v)==1200;images[label].extend(unpack(v))
        else:assert row[6]=='done'
    assert all(len(v)==240000 for v in images.values())
    return images


def integer_blur(pixels):
    channels=[]
    for k in range(4):
        image=[[pixels[y*600+x][k] for x in range(600)] for y in range(400)]
        out=render(image,15.,0.,3,'grouped');channels.append([v for row in out for v in row])
    return [list(v) for v in zip(*channels)]


def analyze(native,output):
    images=decode(native);old,_,_=reference(ROOT/'evidence/importer-loud-fail/r93/native')
    candidate=integer_blur(images['input']);scores={
        'authored_vs_pinned':comparison(images['authored'],old['authored']['rgba']),
        'input_vs_pinned':comparison(images['input'],old['cleared']['rgba']),
        'materialized_input':comparison(images['bitmap-input'],images['input']),
        'input_not_mutated':comparison(images['input-after'],images['input'])}
    for label in ('apply','bitmap-filter','authored'):
        scores['integer_vs_'+label]=comparison(candidate,images[label])
    scores['apply_vs_authored']=comparison(images['apply'],images['authored'])
    scores['bitmap_filter_vs_authored']=comparison(images['bitmap-filter'],images['authored'])
    output.mkdir(parents=True,exist_ok=True)
    for name,pixels in {**images,'integer-candidate':candidate}.items():
        Image.frombytes('RGBA',(600,400),bytes(c for p in pixels for c in p)).save(output/(name+'.png'))
    return {'comparisons':scores,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=analyze(a.native,a.output);(a.output/'analysis.json').write_text(json.dumps(r,separators=(',',':'))+'\n');print({k:(v['exact'],v['samples'],v['max_channel_delta']) for k,v in r['comparisons'].items()})
