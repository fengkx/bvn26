"""Measure explicit authored-filter mutation without assuming property readbacks invalidate caches."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
from PIL import Image
from tools.probes.analyze_jiraiya_bitmap_binding import ROOT
from tools.probes.run_nested_filters import unpack

LABELS=('authored','cleared','child-draw','reassigned','next-frame')


def decode(native):
    build=json.loads((native/'build.json').read_text())
    assert hashlib.sha256((ROOT/build['source']).read_bytes()).hexdigest()==build['source_sha256']
    assert hashlib.sha256((ROOT/build['harness_source']).read_bytes()).hexdigest()==build['harness_sha256']
    path=native/'native.log';text=path.read_text() if path.exists() else gzip.decompress(path.with_suffix('.log.gz').read_bytes()).decode()
    events=[s.split('|') for s in text.splitlines() if s.startswith('AIREF|')]
    assert len(events)==4006 and events[-1][6:]==['done','ok']
    props=[];images={k:{'rgba':[],'gray':[]} for k in LABELS};composed=None
    for i,row in enumerate(events):
        assert row[1]==build['run_id'] and row[2:4]==[str(i),'0'] and row[5]=='0'
        kind,value=row[6:]
        if kind=='props':props.append(value.split(','))
        elif kind=='composed':assert composed is None;composed=list(map(float,value.split(',')))
        elif kind in ('row','gray'):
            label,y,values=value.split(',',2);v=list(map(int,values.split(',')));y=int(y)
            key='rgba' if kind=='row' else 'gray';output=images[label][key];assert len(output)==y*600
            if key=='rgba':assert len(v)==1200;output.extend(unpack(v))
            else:
                assert len(v)==600
                output.extend([[(p>>s)&255 for s in (16,8,0)]+[255] for p in v])
        else:assert kind=='done'
    assert all(len(v)==240000 for image in images.values() for v in image.values())
    assert [r[0] for r in props]==['authored','cleared','reassigned','next-frame']
    assert composed==[1.23333740234375,0,0,1.24481201171875,262.999878,162.9046024]
    return images,props,composed


def comparison(actual,native):
    assert len(actual)==len(native)
    failures=[{'x':i%600,'y':i//600,'actual':a,'native':list(b)} for i,(a,b) in enumerate(zip(actual,native)) if list(a)!=list(b)]
    maxima=[max((abs(r['actual'][k]-r['native'][k]) for r in failures),default=0) for k in range(4)]
    return {'samples':len(native),'exact':len(native)-len(failures),'max_channel_delta':maxima,'failures':failures}


def historical_input_inventory():
    rows=[]
    for path in sorted((ROOT/'evidence/importer-loud-fail/r22/raster-inputs').glob('*/*.native.png')):
        old=ROOT/'evidence/importer-loud-fail/r21/components'/path.parent.name/path.name
        a,b=Image.open(path).convert('RGB'),Image.open(old).convert('RGB')
        assert a.size==b.size==(600,400)
        rows.append({'input_reference':str(path.relative_to(ROOT)),'filtered_reference':str(old.relative_to(ROOT)),
                     'input_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'filtered_sha256':hashlib.sha256(old.read_bytes()).hexdigest(),
                     'different_pixels':sum(x!=y for x,y in zip(a.getdata(),b.getdata()))})
    assert len(rows)==54
    return rows


def analyze(native,output):
    images,props,composed=decode(native);output.mkdir(parents=True,exist_ok=True)
    for label,channels in images.items():
        for kind,pixels in channels.items():
            im=Image.frombytes('RGBA',(600,400),bytes(c for p in pixels for c in p));im.save(output/(label+'-'+kind+'.png'))
    ref=Image.open(ROOT/'evidence/importer-loud-fail/r21/components/jiraiya/jiraiya-342-766-27-000.native.png').convert('RGBA')
    scores={'authored_vs_pinned':comparison(images['authored']['gray'],list(ref.getdata()))}
    for label in LABELS[1:]:
        scores[label+'_vs_authored']=comparison(images[label]['rgba'],images['authored']['rgba'])
    scores['cleared_vs_child_draw']=comparison(images['cleared']['rgba'],images['child-draw']['rgba'])
    scores['next_frame_vs_cleared']=comparison(images['next-frame']['rgba'],images['cleared']['rgba'])
    leaf=Image.new('RGBA',(600,400));leaf.paste(Image.open(ROOT/'evidence/importer-loud-fail/r92/gpu/case-5.png'),(0,0))
    scores['child_draw_vs_r92_leaf']=comparison(images['child-draw']['rgba'],list(leaf.getdata()))
    return {'properties':props,'composed_matrix':composed,'comparisons':scores,'historical_input_inventory':historical_input_inventory(),'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=analyze(a.native,a.output);(a.output/'analysis.json').write_text(json.dumps(r,separators=(',',':'))+'\n');print({k:(s['exact'],s['samples'],s['max_channel_delta']) for k,s in r['comparisons'].items()})
