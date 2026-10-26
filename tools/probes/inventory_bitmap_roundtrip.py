"""Inventory pinned component SWF lossless texels against materialized PNG bytes."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct
import zlib
from PIL import Image
from tools.probes.build_bound_bitmap_component import ROOT, source_tags


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decode_lossless(payload):
    character, format_id, width, height = struct.unpack_from('<HBHH', payload)
    if format_id == 5:
        data = zlib.decompress(payload[7:])
        if len(data) != width*height*4:
            raise ValueError('Lossless byte length mismatch')
        pixels = [[data[i+1], data[i+2], data[i+3], data[i]] for i in range(0,len(data),4)]
    elif format_id == 3:
        count = payload[7]+1
        data = zlib.decompress(payload[8:])
        stride = (width+3)//4*4
        if len(data) != count*4+stride*height:
            raise ValueError('Palette/index byte length mismatch')
        palette = [list(data[i*4:i*4+4]) for i in range(count)]
        indices = data[count*4:]
        if any(indices[y*stride+x] >= count for y in range(height) for x in range(width)):
            raise ValueError('Palette index outside authored color table')
        pixels = [palette[indices[y*stride+x]] for y in range(height) for x in range(width)]
    else:
        raise ValueError(f'Unsupported lossless format {format_id}')
    if any(c > p[3] for p in pixels for c in p[:3]):
        raise ValueError('Non-premultiplied source bytes')
    return character, width, height, pixels


def inventory():
    rows, sources = {}, {}
    for cases_path in sorted((ROOT/'evidence/importer-loud-fail/r21/components').glob('*/cases.json')):
        for case in json.loads(cases_path.read_text()):
            source = case['source']['path']
            assert sha(ROOT/source) == case['source']['sha256']
            timeline_path = ROOT/case['timeline']
            timeline = json.loads(timeline_path.read_text())
            assert timeline['source_swf']['sha256'] == case['source']['sha256']
            definitions = {d['character_id']:d for d in timeline['definitions']}
            asset_path = timeline_path.with_name('assets.json')
            assets = {a['character_id']:a for a in json.loads(asset_path.read_text())['assets']}
            if source not in sources:
                sources[source] = {struct.unpack_from('<H',p)[0]:(code,p) for code,p,_ in source_tags(ROOT/source) if code in (6,20,21,35,36,90)}
            pending, visited = [case['symbol']], set()
            while pending:
                identity = pending.pop()
                if identity in visited:
                    continue
                visited.add(identity)
                if identity not in definitions:
                    raise ValueError(f'{source}: missing definition {identity}')
                definition = definitions[identity]
                pending.extend(definition.get('referenced_character_ids',[]))
                if not definition['type'].startswith('DefineBits'):
                    continue
                key = (source,identity)
                if key in rows:
                    rows[key]['component_ids'].append(case['id'])
                    continue
                code,payload = sources[source][identity]
                row = {'source':source,'source_sha256':case['source']['sha256'],'bitmap':identity,'tag_code':code,
                       'type':definition['type'],'component_ids':[case['id']]}
                rows[key]=row
                if code != 36:
                    row['status']='unmeasured_source_encoding'
                    continue
                if payload[2] not in (3,5):
                    row['status']='unmeasured_lossless_format'
                    row['format']=payload[2]
                    continue
                cid,width,height,raw = decode_lossless(payload)
                assert cid == identity
                if identity not in assets:
                    row['status']='missing_materialized_asset'
                    continue
                asset = assets[identity]
                path = timeline_path.parent/asset['path']
                assert sha(path)==asset['sha256']
                image=Image.open(path).convert('RGBA')
                assert image.size==(width,height)
                png=list(image.getdata())
                assert all(p[3]==q[3] for p,q in zip(png,raw))
                models={
                    'nearest_255':lambda c,a:(c*a+127)//255,
                    'alpha_plus_one_256':lambda c,a:c*(a+1)//256,
                    'external_png_candidate':lambda c,a:c if a==255 else c*a//256,
                }
                row.update({'status':'measured','width':width,'height':height,'texels':len(raw),
                            'png':str(path.relative_to(ROOT)),'png_sha256':sha(path),
                            'raw_rgba_sha256':hashlib.sha256(bytes(c for p in raw for c in p)).hexdigest(), 'format':payload[2],
                            'alpha_histogram':{str(a):n for a,n in sorted(Counter(p[3] for p in raw).items())},'models':{}})
                for name,formula in models.items():
                    exact=maximum=0;failures=[]
                    for i,(p,q) in enumerate(zip(png,raw)):
                        got=[formula(c,p[3]) for c in p[:3]]+[p[3]]
                        delta=max(abs(a-b) for a,b in zip(got,q))
                        exact+=not delta;maximum=max(maximum,delta)
                        if delta:
                            failures.append({'x':i%width,'y':i//width,'png':p,'raw':q,'actual':got})
                    row['models'][name]={'exact':exact,'samples':len(raw),'max_delta':maximum,'failures':failures}
    measured=[r for r in rows.values() if r['status']=='measured']
    summary={name:{'exact_texels':sum(r['models'][name]['exact'] for r in measured),
                   'texels':sum(r['texels'] for r in measured),
                   'exact_bitmaps':sum(r['models'][name]['exact']==r['texels'] for r in measured),
                   'bitmaps':len(measured)} for name in ('nearest_255','alpha_plus_one_256','external_png_candidate')}
    return {'rows':list(rows.values()),'summary':summary,'unmeasured':[r for r in rows.values() if r['status']!='measured'],
            'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();report=inventory()
    args.output.write_text(json.dumps(report,separators=(',',':'))+'\n')
    print(report['summary']);print('unmeasured',len(report['unmeasured']))
