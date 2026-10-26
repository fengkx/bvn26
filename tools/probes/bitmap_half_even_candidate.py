"""Independent half-even diagnostic; historical sampler modules remain unchanged."""
import math
from tools.probes.analyze_clipped_half_step import axis
from tools.probes.analyze_bitmap_repeat_rounding import coordinate


def row(c):
    repeat=c['repeat'];width,height=c['width'],c['height']
    left=max(c['left'],math.ceil(c['shape_left']*c['sx']+math.trunc(c['tx']*4)/4))
    calc=lambda scale,translation,pixel,size:coordinate(scale,translation,pixel,size) if repeat else axis(scale,translation,pixel,'even')
    yy=calc(c['sy'],c['ty'],c['y'],height)-c.get('fill_y',0)
    xs=[calc(c['sx'],c['tx'],x,width)-c.get('fill_x',0) for x in range(left,c['right'])]
    modes=['byte']*len(xs)
    for chunk in range(0,len(xs),256):
        end=min(chunk+256,len(xs))
        if repeat:
            start=chunk
            while start<end:
                period=math.floor(xs[start]/width);stop=start+1
                while stop<end and math.floor(xs[stop]/width)==period:stop+=1
                bulk=start+(stop-start)//4*4
                if bulk>start:
                    mode='vertical' if xs[bulk-1]%width<width-1 and yy%height<height-1 else 'horizontal'
                    modes[start:bulk]=[mode]*(bulk-start)
                start=stop
        elif 1<=yy<height-1:
            start,stop=chunk,end
            while start<stop and xs[start]<1:start+=1
            while stop>start and xs[stop-1]>=width-1:stop-=1
            bulk=start+(stop-start)//4*4;modes[start:bulk]=['vertical']*(bulk-start)
    return left,xs,yy,modes


def interpolate(x,y,texel,mode):
    ix,iy=math.floor(x),math.floor(y);fx,fy=math.floor((x-ix)*256),math.floor((y-iy)*256)
    a,b,c,d=[texel(ix+dx,iy+dy) for dx,dy in ((0,0),(1,0),(0,1),(1,1))]
    if mode=='byte':
        weights=[(256-fx)*(256-fy)//256,fx*(256-fy)//256,(256-fx)*fy//256];weights.append(256-sum(weights))
        return [sum(w*p[k] for w,p in zip(weights,(a,b,c,d)))//256 for k in range(4)]
    if mode=='vertical':
        l=[(a[k]*(256-fy)+c[k]*fy)//256 for k in range(4)];r=[(b[k]*(256-fy)+d[k]*fy)//256 for k in range(4)]
        return [(l[k]*(256-fx)+r[k]*fx)//256 for k in range(4)]
    if mode=='horizontal':
        t=[(a[k]*(256-fx)+b[k]*fx)//256 for k in range(4)];b=[(c[k]*(256-fx)+d[k]*fx)//256 for k in range(4)]
        return [(t[k]*(256-fy)+b[k]*fy)//256 for k in range(4)]
    raise ValueError('Unknown interpolation mode')


def fixture_texel(c,x,y):
    if c['repeat']:x,y=x%c['width'],y%c['height']
    else:x,y=max(0,min(c['width']-1,x)),max(0,min(c['height']-1,y))
    alpha=c['alpha']
    if c.get('varying_alpha'):alpha=(0,64,128,255)[y%2*2+x%2]
    if c['pattern']=='basis':
        color=((1,0,0),(0,1,0),(0,0,1),(1,1,1))[y%2*2+x%2]
        rgb=[v*alpha for v in color]
    elif c['pattern']=='unique':rgb=[255*int(y%2*2+x%2==c['corner']),(x*37+17)%256,113]
    elif c['pattern']=='impulse':
        k=c['corner'];rgb=[255*int(y%2*2+x%2==k) if k<4 else 255*(x if k==4 else y)%510,113,113]
    else:raise ValueError('Unknown source pattern')
    return rgb+[alpha]


def old_controls():
    from tools.probes.build_bitmap_godot_fixture import build
    fixture=build();scores={};failures=[]
    for index,c in enumerate(fixture['cases']):
        left,xs,yy,modes=row(c)
        targets=c.get('row_expected',[c.get('expected')]);score=scores.setdefault(c['suite'],{'samples':0,'exact':0})
        for offset,target in enumerate(targets):
            x=c['left']+offset if 'row_expected' in c else c['x'];j=x-left
            assert 0<=j<len(xs)
            p=interpolate(xs[j],yy,lambda a,b:fixture_texel(c,a,b),modes[j])
            if c.get('straight_rgba'):
                p=[(v*(65280//p[3])+127)//256 if p[3] else 0 for v in p[:3]]+[p[3]]
            else:p[3]=255
            score['samples']+=1
            if p==target:score['exact']+=1
            else:failures.append({'case':index,'suite':c['suite'],'x':x,'actual':p,'native':target})
    return {'scores':scores,'samples':sum(s['samples'] for s in scores.values()),'exact':sum(s['exact'] for s in scores.values()),'failures':failures}


def jiraiya_controls():
    from fractions import Fraction
    from tools.probes.analyze_jiraiya_bitmap_binding import decode,ROOT
    fixture,images=decode(ROOT/'evidence/importer-loud-fail/r89/native');results=[]
    width,height=fixture['target_size'];raw=fixture['pixels_premultiplied'];sw,sh=fixture['width'],fixture['height']
    texel=lambda x,y:raw[max(0,min(sh-1,y))*sw+max(0,min(sw-1,x))]
    for index,(case,native) in enumerate(zip(fixture['cases'],images)):
        sx,sy,tx,ty=[Fraction(str(case[k])) for k in ('sx','sy','tx','ty')]
        start,end=tx,tx+sw*sx;top,bottom=ty+Fraction(4,5)*sy,ty+Fraction(294,5)*sy
        output=[[0]*4 for _ in range(width*height)]
        for y in range(max(0,math.floor(top)),min(height,math.ceil(bottom))):
            c={**case,'repeat':False,'width':sw,'height':sh,'y':y,'left':max(0,math.ceil(start)),
               'right':min(width,math.floor(end)),'shape_left':0,'fill_y':0.8}
            left,xs,yy,modes=row(c)
            for x in range(max(0,math.floor(start)),min(width,math.ceil(end))):
                if left<=x<left+len(xs):xx,mode=xs[x-left],modes[x-left]
                else:xx,mode=axis(case['sx'],case['tx'],x,'even'),'byte'
                coverage=(min(Fraction(x+1),end)-max(Fraction(x),start))*(min(Fraction(y+1),bottom)-max(Fraction(y),top))
                p=interpolate(xx,yy,texel,mode);output[y*width+x]=[math.floor(v*coverage) for v in p]
        failures=[{'x':i%width,'y':i//width,'actual':p,'native':q} for i,(p,q) in enumerate(zip(output,native)) if p!=q]
        results.append({'case':index,'samples':width*height,'exact':width*height-len(failures),'failures':failures})
    return {'cases':results,'exact_images':sum(not r['failures'] for r in results)}


def span_controls():
    from itertools import product
    from tools.probes.analyze_jiraiya_span_controls import decode,texel,YS,ROOT,SX,SY
    cases,inputs=decode(ROOT/'evidence/importer-loud-fail/r90/native')
    score={'samples':0,'exact':0,'failures':[],'input_exact':inputs}
    for case in cases:
        i,tx,pattern,kind,left,right,*_=case['key']
        for index,(y,x) in enumerate(product(YS,range(70,80))):
            if not (kind or left<=x<right) or x+1>tx+60*SX:continue
            c={'sx':SX,'sy':SY,'tx':tx,'ty':4,'width':60,'height':58,'repeat':False,
               'fill_y':.8,'shape_left':0,'left':x if kind else int(left),
               'right':x+1 if kind else min(int(right),math.floor(tx+60*SX)),'y':y}
            start,xs,yy,modes=row(c);j=x-start
            p=interpolate(xs[j],yy,lambda a,b:texel(int(pattern),a,b)+[255],modes[j])
            target=case['pixels'][index];score['samples']+=1
            if p==target:score['exact']+=1
            else:score['failures'].append({'case':int(i),'x':x,'y':y,'actual':p,'native':target})
    return score


if __name__=='__main__':
    import argparse
    import json
    from pathlib import Path
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    result={'old':old_controls(),'jiraiya':jiraiya_controls(),'spans':span_controls(),'production_admitted':False}
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print('old',result['old']['exact'],result['old']['samples'])
    print('Jiraiya',result['jiraiya']['exact_images'],'spans',result['spans']['exact'],result['spans']['samples'])
