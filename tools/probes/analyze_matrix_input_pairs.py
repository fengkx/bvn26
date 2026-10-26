"""Reject pointwise matrix constructions before assuming a separate cache snapshot is filter input."""
import argparse
from collections import Counter,defaultdict
import json
import math
from pathlib import Path
import struct
from tools.probes.analyze_matrix_component_boundaries import decode
from tools.probes.build_bound_bitmap_component import ROOT


def predict(pixel,matrix,precision,space,conversion):
    coefficients=[struct.unpack('<f',struct.pack('<f',v))[0] for v in matrix]
    if precision!='float32':
        bits,rounding=precision.split('/');scale=1<<int(bits)
        quantize=math.trunc if rounding=='trunc' else round
        coefficients=[quantize(v*scale)/scale for v in coefficients]
    alpha=pixel[3]
    if not alpha:return [0]*4
    values=[v*255/alpha for v in pixel[:3]]+[alpha] if space=='straight' else list(pixel)
    result=[]
    for row in range(3):
        value=sum(coefficients[row*5+j]*values[j] for j in range(4))+coefficients[row*5+4]*(1 if space=='straight' else alpha/255)
        value=max(0,min(255 if space=='straight' else alpha,value))
        if space=='straight':value*=alpha/255
        result.append(math.floor(value+(0.5 if conversion=='nearest' else 0)))
    return result+[alpha]


def analyze():
    build,images,_,_,_,_=decode(ROOT/'evidence/importer-loud-fail/r195/native/frame3')
    matrix=build['case']['placement']['filters'][0]['matrix'];assert matrix[15:]==[0,0,0,1,0]
    pairs=Counter();locations=defaultdict(list)
    for tick in (0,8):
        for i,(before,after) in enumerate(zip(images[f'{tick}-cache'],images[f'{tick}-authored'])):
            pair=tuple(before),tuple(after);pairs[pair]+=1
            locations[pair].append([tick,i%600,i//600])
    groups=defaultdict(list)
    for (source,native),count in sorted(pairs.items()):
        groups[source].append({'native':list(native),'pixels':count,'locations':locations[(source,native)]})
    ambiguous=[{'source':list(source),'outputs':outputs} for source,outputs in groups.items() if len(outputs)>1]
    scores={}
    for precision in ('float32','8/trunc','8/even','16/trunc','16/even'):
        for space in ('straight','premultiplied'):
            for conversion in ('floor','nearest'):
                score={'samples':sum(pairs.values()),'exact':0,'counterexamples':[]}
                for (pixel,native),count in sorted(pairs.items()):
                    actual=predict(pixel,matrix,precision,space,conversion)
                    if actual==list(native):score['exact']+=count
                    else:score['counterexamples'].append({'source':list(pixel),'native':list(native),'actual':actual,'count':count})
                scores[f'{precision}/{space}/{conversion}']=score
    return {'observed_source_values':len(groups),'source_output_pairs':len(pairs),'ambiguous_inputs':ambiguous,'scores':scores,
            'matrix_properties':matrix,'materialized_filter_input_proved':False,'candidate_admitted':False,'gpu_advance_allowed':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=analyze()
    a.output.write_text(json.dumps(r,separators=(',',':'))+'\n');print('inputs',r['observed_source_values'],'pairs',r['source_output_pairs'],'ambiguous',len(r['ambiguous_inputs']))
    for k,v in r['scores'].items():print(k,v['exact'],v['samples'])
