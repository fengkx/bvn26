"""Independent all-alpha/extent controls; no candidate is production-admitted."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import struct

from tools.probes.analyze_cxform_rows import (
    analyze as previous_analysis, f32, load_reciprocals, score,
)
from tools.probes.analyze_materialized_controls import fixed_cx
from tools.probes.nested_composition import rgba
from tools.probes.normal_composition import over
from tools.probes.run_nested_filters import cases, decode, unpack

ROOT = Path(__file__).resolve().parents[2]
GREENS = (140,145,146,147,156,157,158,164,165,166,173,174,175,187,188,189,
          195,196,197,198,199,200,205,206,207,208,209,210,211,212,213,216)
WIDTHS = (34,35,47,63,64,65,127,128,129,255,256,257,511,512,513)
MODELS = ('r39', 'rounded_reciprocal', 'normalized_divide', 'normalized_multiply',
          'normalized_opacity_first', 'byte_estimate', 'byte_rounded',
          'byte_rounded_opacity_first', 'byte_rounded_joint')


def capture_rows(directory, identities):
    build = json.loads((directory/'build.json').read_text())
    if hashlib.sha256((ROOT/build['source']).read_bytes()).hexdigest() != build['source_sha256']:
        raise ValueError('Native source changed')
    raw = gzip.decompress((directory/'native.log.gz').read_bytes())
    hashes = json.loads((directory/'trace-sha256.json').read_text())
    if (hashlib.sha256(raw).hexdigest() != hashes['native.log'] or
            hashlib.sha256((directory/'native.log.gz').read_bytes()).hexdigest() != hashes['native.log.gz']):
        raise ValueError('Native trace changed')
    rows = []
    done = False
    for line in raw.decode().splitlines():
        p = line.split('|')
        if p[:2] != ['AIREF',build['run_id']]:
            continue
        if len(p)!=8 or done or p[2:6]!=[str(len(rows)),'0','0','0']:
            raise ValueError('Malformed or reordered capture')
        if p[6:]==['done','ok']:
            done = True
            continue
        if p[6]!='row' or len(rows)>=len(identities):
            raise ValueError('Unexpected row')
        values = list(map(int,p[7].split(',')))
        identity = identities[len(rows)]
        if values[:len(identity)]!=identity or len(values)!=len(identity)+128:
            raise ValueError('Unexpected row identity or extent')
        rows.append(values)
    if not done or len(rows)!=len(identities):
        raise ValueError('Incomplete native capture')
    return rows


def load_precision(path):
    rows = [line.split() for line in path.read_text().splitlines()]
    if [int(v[0]) for v in rows]!=list(range(1,256)) or any(len(v)!=6 for v in rows):
        raise ValueError('Incomplete reciprocal measurements')
    return {int(v[0]):[struct.unpack('<f',struct.pack('<I',int(b,16)))[0] for b in v[1:]] for v in rows}


def candidate(pixel, opacity, name, table, fixed_opacity=False):
    alpha = pixel[3]
    if not alpha:
        return [0]*4
    op_float = f32((opacity*256//100)/256 if fixed_opacity else opacity/100)
    out = []
    for channel,multiplier,offset in zip(pixel[:3],(.5,.75,1),(8,0,-4)):
        if name in ('r39','rounded_reciprocal'):
            reciprocal = table[alpha][0] if name=='r39' else f32(1/alpha)
            straight = f32(channel*reciprocal)
            transformed = f32(f32(straight*multiplier)+f32(offset/255))
            value = f32(f32(max(0,min(1,transformed))*alpha)*op_float)
        elif name.startswith('normalized'):
            multiply = name=='normalized_multiply'
            unit_alpha = table[alpha][3 if multiply else 1]
            reciprocal = table[alpha][4 if multiply else 2]
            unit_channel = f32(channel*f32(1/255)) if multiply else f32(channel/255)
            straight = f32(unit_channel*reciprocal)
            transformed = f32(f32(straight*multiplier)+f32(offset/255))
            premult = f32(max(0,min(1,transformed))*unit_alpha)
            if name=='normalized_opacity_first':
                value = f32(f32(premult*op_float)*255)
            else:
                value = f32(f32(premult*255)*op_float)
        elif name.startswith('byte_'):
            reciprocal = table[alpha][2] if name=='byte_estimate' else f32(255/alpha)
            transformed = f32(f32(f32(channel*reciprocal)*multiplier)+offset)
            transformed = max(0,min(255,transformed))
            scale = f32(alpha/255)
            op = op_float
            if name=='byte_rounded_opacity_first':
                value = f32(f32(transformed*op)*scale)
            elif name=='byte_rounded_joint':
                value = f32(transformed*f32(scale*op))
            else:
                value = f32(f32(transformed*scale)*op)
        else:
            raise ValueError('Unknown arithmetic model')
        out.append(int(value))
    return out+[alpha*(opacity*256//100)//256]


def bounded(pixel, opacity, width, x, name, table):
    # Preserve r39's geometry selector across every arithmetic comparison.
    if not 0<=x<width:
        raise ValueError('Outside clipped row')
    return candidate(pixel,opacity,name,table) if width>=16 and x<width//4*4 else fixed_cx(pixel,opacity)


def alpha_samples(directory, opacities=(25,50,100)):
    identities = [[a*len(opacities)+i,a,op] for a in range(256) for i,op in enumerate(opacities)]
    for row in capture_rows(directory,identities):
        index,alpha,opacity = row[:3]
        for x in range(32):
            source,native = unpack(row[3+x*4:7+x*4])
            if source!=rgba((70<<16)+(GREENS[x]<<8)+236,alpha):
                raise ValueError('Alpha source readback differs')
            yield [index,x],source,native,opacity


def extent_samples(directory):
    identities = []
    case = 0
    for alpha in (135,197):
        for opacity in (50,100):
            for width in WIDTHS:
                for start in (0,3):
                    for tx in (-590,-15,0,11,590):
                        identities.extend([case,alpha,opacity,width,start,tx,base] for base in range(0,640,32))
                        case += 1
    for row in capture_rows(directory,identities):
        index,alpha,opacity,width,start,tx,base = row[:7]
        for j in range(32):
            x = base+j
            source,native = unpack(row[7+j*4:11+j*4])
            sx = x-tx
            expected = rgba((70<<16)+((192+sx%16)<<8)+236,alpha) if 0<=sx<600 else [0]*4
            if source!=expected:
                raise ValueError('Extent source readback differs')
            yield [index,x],source,native,alpha,opacity,width,start,tx


def native_boundaries(name, table):
    for spec,ref in zip(cases(),decode(ROOT/'evidence/importer-loud-fail/r38/native')):
        index,profile,alpha,child_op,parent_op,cx = spec['key']
        for stage,size,source_stage,source_size,left,top,opacity in (
                ('parent_input',18,'child_filter',12,3,3,child_op),
                ('final',24,'parent_filter',18,1,1,parent_op)):
            for y in range(size):
                for x in range(size):
                    if stage=='parent_input':
                        actual = spec['inputs']['middle'] if 1<=x<17 and 1<=y<17 else [0]*4
                    else:
                        actual = spec['inputs']['back']
                    sx,sy = x-left,y-top
                    if 0<=sx<source_size and 0<=sy<source_size:
                        source = ref[source_stage][sy*source_size+sx]
                        front = bounded(source,opacity,source_size,sx,name,table) if cx else [c*(opacity*256//100)//256 for c in source]
                        actual = over(actual,front)
                    if stage=='final' and 10<=x<12:
                        actual = over(actual,spec['inputs']['sentinel'])
                    yield [index,stage,x,y],actual,ref[stage][y*size+x]


def analyze(root):
    table = load_precision(root/'reciprocal.txt')
    old = load_reciprocals(ROOT/'evidence/importer-loud-fail/r39/reciprocal.txt')
    if any(table[a][0]!=old[a] for a in old):
        raise ValueError('Independent helper changed original reciprocal estimates')
    samples = list(alpha_samples(root/'alpha'))
    scores = {}
    for name in MODELS:
        scores[name] = score((key,bounded(p,op,32,key[1],name,table),native) for key,p,native,op in samples)
    opacity_samples = list(alpha_samples(root/'opacity',(1,33,67,99)))
    opacity_scores = {}
    for fixed in (False,True):
        for name in MODELS:
            key = name+('/source_8_8_opacity' if fixed else '/unquantized_opacity')
            result = score((key,candidate(p,op,name,table,fixed),native) for key,p,native,op in opacity_samples)
            if name not in ('r39','normalized_divide'):
                result.pop('failures')
            opacity_scores[key] = result
    extents = list(extent_samples(root/'extents'))
    geometry = {}
    for intersection in (False,True):
        for alpha in (135,197):
            pairs = []
            for key,p,native,a,op,width,start,tx in extents:
                if a!=alpha:
                    continue
                x = key[1]
                lo,hi = max(0,start,tx),min(640,start+width,tx+600)
                left,length = (lo,hi-lo) if intersection else (start,width)
                actual = bounded(p,op,length,x-left,'r39',table) if lo<=x<hi else [0]*4
                pairs.append((key,actual,native))
            geometry[('intersection_control_' if intersection else 'unchanged_selector_')+str(alpha)] = score(pairs)
    boundaries = {name:score(native_boundaries(name,table)) for name in ('r39','normalized_divide')}
    # Retain complete counterexamples for the baseline and the improved but
    # rejected normalized comparator; other comparators retain strict counts.
    for name in scores:
        if name not in ('r39','normalized_divide'):
            scores[name].pop('failures')
    prior = previous_analysis(ROOT/'evidence/importer-loud-fail/r39',ROOT/'evidence/importer-loud-fail/r38')
    # previous_analysis has already validated these complete pinned captures.
    # This second pass measures the alternative without changing old regressions.
    alternate_prior = {}
    for name, path, event in (
            ('rows', ROOT/'evidence/importer-loud-fail/r39/native/native.log', 'row'),
            ('spans', ROOT/'evidence/importer-loud-fail/r38/spans/native.log', 'span'),
            ('varied', ROOT/'evidence/importer-loud-fail/r38/varied/native.log', 'span')):
        pairs = []
        for line in path.read_text().splitlines():
            fields = line.split('|')
            if len(fields)!=8 or fields[6]!=event:
                continue
            values = list(map(int,fields[7].split(',')))
            if name=='rows':
                index,pattern,alpha,opacity,width,start,tx = values[:7]
                samples = [(x,*unpack(values[7+x*4:11+x*4])) for x in range(32)]
            else:
                index,width,start,alpha,opacity = values[:5]
                samples = [(x,rgba(0xff8001 if name=='varied' and (x-start)%2 else 0x46c4ec,alpha),pixel)
                           for x,pixel in enumerate(unpack(values[7:]))]
            for x,source,native in samples:
                actual = bounded(source,opacity,width,x-start,'normalized_divide',table) if start<=x<start+width else [0]*4
                pairs.append(([index,x],actual,native))
        alternate_prior[name] = score(pairs)
    prior_scores = {k:{a:b for a,b in v.items() if a!='failures'} for k,v in prior['scores'].items()}
    return {'production_admitted':False,'candidate_admitted':False,
            'gpu_advance_allowed':False,'all_alpha':scores,'geometry':geometry,
            'nonbinary_opacity':opacity_scores,
            'native_boundaries':boundaries,'prior_regressions':prior_scores,
            'normalized_prior':alternate_prior,
            'scope':'Independent CPU comparisons; intersection routing is an observation, not a replacement of r39. No ISA inference.'}


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    result = analyze(args.root)
    payload = (json.dumps(result,indent=2)+'\n').encode()
    args.output.write_bytes(gzip.compress(payload,mtime=0) if args.output.suffix=='.gz' else payload)
    print(json.dumps({group:{name:{k:v for k,v in score.items() if k!='failures'} for name,score in result[group].items()} for group in ('all_alpha','geometry','native_boundaries','prior_regressions','normalized_prior','nonbinary_opacity')}))
    raise SystemExit(1)
