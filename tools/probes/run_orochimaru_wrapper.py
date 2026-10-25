"""Bind source JPEG planes to the bounded nearest-fill wrapper; references compare only."""
import argparse
from fractions import Fraction
import hashlib
import gzip
import json
from pathlib import Path
import struct
import subprocess
import xml.etree.ElementTree as ET
import zlib
from PIL import Image
from tools.probes.build_bound_bitmap_component import ROOT, source_tags, bitmap_shape_fill_polygons
from tools.probes.analyze_jpeg_row_partitions import routed_rgb
from tools.probes.rect_mask_binding import canonical_rect_mask
from tools.probes.analyze_affine_cache_support import bounds
from tools.probes.analyze_affine_cache_coordinates import local_translation
from tools.probes.analyze_affine_heldout import inverse_signed
from tools.probes.analyze_affine_rounded_footprint import prepare
from tools.probes.analyze_affine_scan_translation import vertices, fixed_scan
from tools.probes.run_nearest_matrix_family import measure


def source_fixture(dump, output):
    inventory = json.loads((ROOT/'evidence/importer-loud-fail/r209/orochimaru.json').read_text())
    source = ROOT/inventory['source']['path']
    assert hashlib.sha256(source.read_bytes()).hexdigest() == inventory['source']['sha256']
    raw = {struct.unpack_from('<H', p)[0]: (code, p, tag) for code, p, tag in source_tags(source) if code in (2,35,39)}
    assert {str(i): hashlib.sha256(raw[i][2]).hexdigest() for i in (340,341,342)} == inventory['raw_tag_sha256']
    code, payload, _ = raw[340]
    assert code == 35
    length = struct.unpack_from('<I', payload, 2)[0]
    jpeg, alpha = payload[6:6+length], zlib.decompress(payload[6+length:])
    assert len(alpha) == 186*378 and set(alpha) == {0,255}
    assert jpeg.count(b'\xff\xd9\xff\xd8') == 1
    seam = jpeg.index(b'\xff\xd9\xff\xd8')
    assert seam == 572 and seam < jpeg.index(b'\xff\xc0')
    output.mkdir(parents=True, exist_ok=True)
    path = output/'source.jpg'; path.write_bytes(jpeg[:seam]+jpeg[seam+4:])
    for scale in (1,2):
        folder = output/f'scale{scale}'; folder.mkdir(exist_ok=True)
        result = subprocess.run([str(dump),str(path),str(folder),str(scale)], capture_output=True, check=True)
        (folder/'decode.log').write_bytes(result.stderr)
    paths = [output/'scale1/c0.pgm',output/'scale2/c1.pgm',output/'scale2/c2.pgm']
    planes = [Image.open(p) for p in paths]
    assert all(p.size == (186,378) and p.mode == 'L' for p in planes)
    pinned = json.loads(gzip.decompress((ROOT/'evidence/importer-loud-fail/r217/summary.json.gz').read_bytes()))['rows'][0]['plane_sha256']
    assert [hashlib.sha256(p.read_bytes()).hexdigest() for p in paths] == pinned
    pixels = [routed_rgb(v,i%186,186,8)+[alpha[i]] if alpha[i] else [0]*4
              for i,v in enumerate(zip(*(p.getdata() for p in planes)))]
    assert len(pixels) == 186*378
    shape = ET.fromstring(inventory['shape_xml']); wrapper = ET.fromstring(inventory['wrapper_xml'])
    styles = shape.findall('./shapes/fillStyles/fillStyles/item'); assert len(styles) == 1
    fill = styles[0]; matrix = fill.find('bitmapMatrix')
    assert fill.get('fillStyleType') == '67' and fill.get('bitmapId') == '340'
    assert float(matrix.get('scaleX')) == float(matrix.get('scaleY')) == 20
    assert not shape.findall('.//lineStyles/item')
    tags = wrapper.findall('./subTags/item')
    assert [t.get('type') for t in tags] == ['SoundStreamHead2Tag','PlaceObject2Tag','ShowFrameTag']
    assert int(tags[0].get('streamSoundSampleCount')) == 0
    placement = tags[1]
    assert placement.get('depth') == '1' and placement.get('characterId') == '341'
    assert all(v != 'true' or k in ('placeFlagHasCharacter','placeFlagHasMatrix') for k,v in placement.attrib.items() if k.startswith('placeFlag'))
    inner = dict(placement.find('matrix').attrib)
    assert inner.get('hasScale') == inner.get('hasRotate') == 'false'
    leaf = {'width':186,'height':378,'fill':dict(fill.attrib),'fill_matrix':dict(matrix.attrib),
            'fill_masks':bitmap_shape_fill_polygons(shape),'inner_matrix':inner}
    canonical_rect_mask(leaf)
    return {**leaf,'source':inventory['source'],'raw_tag_sha256':inventory['raw_tag_sha256'],
            'plane_sha256':[hashlib.sha256(p.read_bytes()).hexdigest() for p in paths],
            'pixels_premultiplied':pixels,'production_admitted':False}


def sampling(case, leaf):
    placement = case['placement']['matrix']; norm = case['normalization']
    assert placement.get('hasRotate') == placement.get('hasScale') == 'false'
    assert case['placement']['filters'] == [{'type':'BLURFILTER','blurX':0.0,'blurY':20.0,'passes':1}]
    inner = leaf['inner_matrix']; scale = Fraction(str(norm['scale']))
    # Preserve the two authored translations and the draw transform separately in metadata.
    tx = Fraction(int(placement['translateX'])+int(inner['translateX']),20)*scale
    ty = Fraction(int(placement['translateY'])+int(inner['translateY']),20)*scale
    key = ['0','0','0','186','378',str(scale),'0','0',str(scale),str(tx),str(ty),'1','0','0','1',str(norm['x']),str(norm['y'])]
    allocation = bounds(key,'separate'); origin = allocation[:2]; width,height = allocation[2:]
    translation = local_translation(key,origin,'baseline')
    local = key.copy(); local[9:11] = list(map(str,translation)); local[15:17] = ['0','0']
    counts = fixed_scan(vertices(local),0,0,width,height,16,'trunc')
    fixed = prepare(tuple(inverse_signed(local)),'ties_even')
    packed = bytearray(width*height*32); coordinates = bytearray(width*height*16)
    for i,count in enumerate(counts):
        if not count: continue
        x,y = i%width,i//width
        for axis,(a,b,t,offset,_) in enumerate(fixed):
            assert all(-2**31+65536 < v < 2**31-65536 for v in (a*x,b*y,a*x+b*y,a*x+b*y+t,a*x+b*y+t+offset))
            for slot,value in enumerate((a,b,t,offset)):
                struct.pack_into('<i',packed,i*32+(axis*4+slot)*4,value)
        struct.pack_into('<4f',coordinates,i*16,x,y,0,count)
    return {'key':key,'local_key':local,'origin':origin,'size':[width,height],
            'x_bounds':[origin[0],origin[0]+width],'y_bounds':[origin[1],origin[1]+height],
            'local_size':[width,height],'filters':case['placement']['filters']},packed,coordinates


def fixture(dump, output):
    leaf = source_fixture(dump,output/'decoded')
    cases = json.loads((ROOT/'evidence/importer-loud-fail/r32/components/orochimaru/cases.json').read_text())
    inventory = json.loads((ROOT/'evidence/importer-loud-fail/r209/orochimaru.json').read_text())
    assert cases == inventory['cases']
    specs = []
    for case in cases:
        spec,packed,coordinates = sampling(case,leaf)
        folder = output/case['id']; folder.mkdir(exist_ok=True)
        (folder/'source.rgba').write_bytes(bytes(v for p in leaf['pixels_premultiplied'] for v in p))
        (folder/'coefficients.bin').write_bytes(packed); (folder/'coordinates.bin').write_bytes(coordinates)
        specs.append({**spec,'folder':case['id'],'case':case})
    result = {'leaf':{k:v for k,v in leaf.items() if k != 'pixels_premultiplied'},'cases':specs,'production_admitted':False}
    (output/'fixture.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


def compare_boundaries(output, native):
    from tools.probes.analyze_component_cache_boundaries import decode
    fixture = json.loads((output/'fixture.json').read_text()); rows=[]
    for spec in fixture['cases']:
        build, images, _, _, _ = decode(native/spec['folder']/'components/orochimaru')
        assert build['case'] == spec['case']
        x,y = spec['origin']; w,h = spec['size']
        for name, target_name, padding in [('local.png','cache',0),('input-0.png','cache',10),('filtered-0.png','authored',10)]:
            image=Image.open(output/spec['folder']/name).convert('RGBA')
            assert image.size == (w,h+2*padding)
            assert 0 <= x < x+w <= 600 and 0 <= y-padding < y+h+padding <= 400
            target=[images['1-'+target_name][(y+j-padding)*600+x+i] for j in range(h+2*padding) for i in range(w)]
            rows.append({'case':spec['folder'],'boundary':name,**measure(list(image.getdata()),target,w)})
    return {'boundaries':rows,'boundaries_exact':all(r['exact']==r['samples'] for r in rows),'production_admitted':False}


def compare(output):
    fixture = json.loads((output/'fixture.json').read_text()); rows=[]
    for spec in fixture['cases']:
        image = Image.open(output/spec['folder']/'final-0.png').convert('RGBA')
        for tick in spec['case']['samples']:
            path = ROOT/f'evidence/importer-loud-fail/r21/components/orochimaru/{spec["folder"]}-{tick:03d}.native.png'
            native = Image.open(path).convert('RGBA'); assert image.size == native.size == (600,400)
            rows.append({'case':spec['folder'],'tick':tick,'native_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),**measure(list(image.getdata()),list(native.getdata()),600)})
    return {'images':rows,'exact_images':sum(v['exact']==v['samples'] for v in rows),'production_admitted':False}



def provenance(output, dump, godot, native):
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    files = ['tools/probes/run_orochimaru_wrapper.py','godot/tests/orochimaru_wrapper_live.gd',
             'godot/tests/affine_component_coverage.gdshader','godot/tests/live_rect_cache_filter.gd',
             'godot/tests/grouped_blur_filter_group.gd','godot/tests/integer_blur.gdshader',
             'godot/tests/nested_integer_composite.gdshader','godot/filter_group.gd',
             'tools/probes/jpeg_scaled_planes.c','tools/probes/analyze_jpeg_row_partitions.py']
    result = {'source_sha256':{p:sha(ROOT/p) for p in files},'godot_sha256':sha(godot),
              'jpeg_dump_sha256':sha(dump),'native_root':str(native),
              'readback_sha256':{str(p.relative_to(output)):sha(p) for p in output.rglob('*')
                                 if p.is_file() and p.name!='provenance.json'},
              'production_admitted':False}
    (output/'provenance.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


def run(dump,godot,output,native=None):
    output.mkdir(parents=True,exist_ok=True); fixture(dump,output)
    command = [str(godot),'--path',str(ROOT/'godot'),'--rendering-method','gl_compatibility','--quit-after','1200','-s',str(ROOT/'godot/tests/orochimaru_wrapper_live.gd'),'--',str(output/'fixture.json'),str(output)]
    result = subprocess.run(command,capture_output=True,text=True,timeout=300); log=result.stdout+result.stderr
    (output/'godot.log').write_text(log)
    if result.returncode or 'ERROR' in log or 'OROCHIMARU_WRAPPER_LIVE_OK cases=5' not in log:
        raise ValueError('Incomplete source wrapper diagnostic: '+log)
    boundaries = compare_boundaries(output,native) if native is not None else {'boundaries_exact':False,'boundary_measurement_missing':True}
    report={**compare(output),**boundaries,'boundary_comparison_before_final_comparison':True,'full_wrapper_exact':False}
    report['full_wrapper_exact'] = boundaries['boundaries_exact'] and report['exact_images'] == 10
    (output/'report.json').write_text(json.dumps(report,separators=(',',':'))+'\n')
    provenance(output,dump,godot,native)
    return report


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dump',type=Path,required=True); parser.add_argument('--godot',type=Path,required=True); parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--native',type=Path,required=True)
    args=parser.parse_args(); result=run(args.dump.resolve(),args.godot.resolve(),args.output.resolve(),args.native.resolve())
    print(result['exact_images'],'/10'); raise SystemExit(0 if result['full_wrapper_exact'] else 1)
