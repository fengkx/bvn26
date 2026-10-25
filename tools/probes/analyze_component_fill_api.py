"""Compare native SWF-tag and AS fill boundaries only after source-byte/property verification."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
from PIL import Image
from tools.probes.analyze_jiraiya_filter_boundary import ROOT,comparison
from tools.probes.run_nested_filters import unpack


def analyze(native,output=None):
    build=json.loads((native/'build.json').read_text())
    for path,digest in [(build['source'],build['source_sha256']),(build['harness_source'],build['harness_sha256']),(build['fixture_source'],build['fixture_sha256'])]:assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest
    fixture=json.loads((ROOT/build['fixture_source']).read_text());leaf=fixture['leaves']['8'];assert fixture['case']==build['case']
    p=native/'native.log';text=p.read_text() if p.exists() else gzip.decompress(p.with_suffix('.log.gz').read_bytes()).decode();events=[line.split('|') for line in text.splitlines() if line.startswith('AIREF|')]
    assert len(events)==2475 and events[-1][6:]==['done','ok'];source=[];images={};matrices=[];props=[];fills=[]
    for i,row in enumerate(events):
        assert row[1]==build['run_id'] and row[2:6]==[str(i),'0','0','0'];kind,payload=row[6:]
        if kind=='source':
            values=list(map(int,payload.split(',')));assert values[0]==len(source)//35 and len(values)==71;source.extend(unpack(values[1:]))
        elif kind=='fill':fills.append(list(map(float,payload.split(','))))
        elif kind=='matrix':
            label,values=payload.split(',',1);matrices.append({'label':label,'values':list(map(float,values.split(',')))})
        elif kind=='props':props.append(payload.split(','))
        elif kind=='row':
            label,y,values=payload.split(',',2);pixels=images.setdefault(label,[]);assert len(pixels)==int(y)*600;v=list(map(int,values.split(',')));assert len(v)==1200;pixels.extend(unpack(v))
        else:assert kind=='done'
    assert source==leaf['pixels_premultiplied'] and len(source)==2275
    assert len(images)==6 and all(len(v)==240000 for v in images.values())
    assert fills==[[1,0,0,1,16.6,-8.15]]
    assert [v['label'] for v in matrices]==['tag','as']
    assert matrices[0]['values']==matrices[1]['values']
    expected=[]
    for label in ('tag','as'):
        frame='1' if label=='tag' else '0'
        expected.extend([[label+'-authored',frame,'true','1','0','10','1'],[label+'-clear',frame,'false','0'],[label+'-cache',frame,'true','0']])
    assert props==expected
    scores={};prior={};cpu={};pins=json.loads((ROOT/'evidence/importer-loud-fail/r141/provenance.json').read_text())['evidence_sha256']
    for kind in ('authored','clear','cache'):
        scores[kind]=comparison(images['as-'+kind],images['tag-'+kind])
        path=ROOT/'evidence/importer-loud-fail/r141/images'/f'0-{kind}.png';assert hashlib.sha256(path.read_bytes()).hexdigest()==pins[f'images/0-{kind}.png']
        prior[kind]=comparison(images['tag-'+kind],list(Image.open(path).convert('RGBA').getdata()))
    for label in ('tag','as'):
        path=ROOT/'evidence/importer-loud-fail/r142/images/0-cache.png'
        cpu[label]=comparison(list(Image.open(path).convert('RGBA').getdata()),images[label+'-cache'])
    if output:
        output.mkdir(parents=True,exist_ok=True)
        for name,pixels in images.items():Image.frombytes('RGBA',(600,400),bytes(c for p in pixels for c in p)).save(output/f'{name}.png')
    return {'source_pixels_exact':2275,'fill_properties':fills,'matrices':matrices,'filter_properties':props,'api_comparisons':scores,'prior_tag_reference':prior,'unchanged_cpu_cache':cpu,'api_equivalence_verified':all(v['exact']==v['samples'] for v in scores.values()),'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=analyze(a.native,a.output);(a.output/'analysis.json').write_text(json.dumps(r,separators=(',',':'))+'\n')
    for name,values in [('api',r['api_comparisons']),('prior',r['prior_tag_reference']),('cpu',r['unchanged_cpu_cache'])]:
        for k,v in values.items():print(name,k,v['exact'],v['samples'],v['max_channel_delta'])
