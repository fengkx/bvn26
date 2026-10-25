"""Discriminate one shared scaled-translation tie rule and retain old matrix controls."""
import argparse
import json
import math
from pathlib import Path
from tools.probes.analyze_bitmap_nested_scale import decode,translations
from tools.probes.analyze_bitmap_nested_translation import ROOT,predict


def measure(cases):
    names=('scaled_inner_nearest_even','scaled_inner_nearest_away','scaled_inner_nearest_up')
    scores={name:{'samples':0,'exact':0,'failures':[]} for name in names}
    direct={'samples':0,'exact':0,'failures':[]};tie_cases=[]
    for c in cases:
        i,_,_,outer,inner_scale,inner,_,scale,composed,outer_scale=c['key']
        models=translations(inner,outer,outer_scale,composed)
        models['scaled_inner_nearest_up']=math.floor(inner*outer_scale*4+.5)/4+math.trunc(outer*4)/4
        fractional=inner*outer_scale*4-math.floor(inner*outer_scale*4)
        if fractional==.5:tie_cases.append(int(i))
        for x in range(600):
            if x<composed+scale or x+1>composed+59*scale:continue
            for name,s in scores.items():
                p=predict(scale,models[name],x);s['samples']+=1
                if p==c['nested'][x]:s['exact']+=1
                else:s['failures'].append({'case':int(i),'x':x,'actual':p,'native':c['nested'][x]})
            p=predict(scale,composed,x);direct['samples']+=1
            if p==c['direct'][x]:direct['exact']+=1
            else:direct['failures'].append({'case':int(i),'x':x,'actual':p,'native':c['direct'][x]})
    return {'scores':scores,'direct':direct,'tie_cases':tie_cases}


def analyze(native):
    cases=decode(native,720);result=measure(cases)
    result.update({'properties':[c['key'] for c in cases],'old_scale':measure(decode(ROOT/'evidence/importer-loud-fail/r96/native')),'production_admitted':False})
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=analyze(a.native);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,separators=(',',':'))+'\n');print({m:(v['exact'],v['samples']) for m,v in r['scores'].items()});print('direct',r['direct']['exact'],r['direct']['samples'],'tie cases',len(r['tie_cases']))
