"""Preserve dormant source styles while exactly factoring active bitmap quads."""
import struct
from tools.probes.build_minimal_swf import rect
from tools.probes.jinye_factorization_tags import Reader,pack,signed_bits


def parse(raw):
    header=struct.unpack_from('<H',raw)[0];assert header>>6==2 and header&63==63
    assert struct.unpack_from('<I',raw,2)[0]==len(raw)-6
    r=Reader(raw[6:]);cid=r.ui16();n=r.bits(5);bounds=[r.bits(n,True) for _ in range(4)];r.align()
    assert r.bits(8)==2;styles=[]
    for _ in range(2):
        start=r.pos//8;mode=r.bits(8);bitmap=r.ui16();assert mode in (65,67)
        linear=[65536,0,0,65536]
        if r.bits(1):n=r.bits(5);linear[0]=r.bits(n,True);linear[3]=r.bits(n,True)
        if r.bits(1):n=r.bits(5);linear[1]=r.bits(n,True);linear[2]=r.bits(n,True)
        n=r.bits(5);translation=[r.bits(n,True),r.bits(n,True)];r.align()
        styles.append({'type':mode,'bitmap':bitmap,'linear_fixed':linear,'translation_twips':translation,'raw_hex':r.data[start:r.pos//8].hex()})
    assert [s['bitmap'] for s in styles]==[65535,55]
    assert r.bits(8)==0 and r.bits(4)==2 and r.bits(4)==0
    assert r.bits(1)==0 and r.bits(5)==5
    n=r.bits(5);x,y=r.bits(n,True),r.bits(n,True);assert r.bits(2)==2;points=[[x,y]]
    for _ in range(4):
        assert r.bits(1)==1 and r.bits(1)==1
        n=r.bits(4)+2;assert r.bits(1)==1
        x+=r.bits(n,True);y+=r.bits(n,True);points.append([x,y])
    assert r.bits(6)==0;r.align();assert r.pos==len(r.data)*8 and points[0]==points[-1]
    assert bounds==[min(p[0] for p in points),max(p[0] for p in points),min(p[1] for p in points),max(p[1] for p in points)]
    return {'shape':cid,'styles':styles,'mask_twips':points[:-1],'bounds_twips':bounds}


def matrix(linear,translation):
    a,b,c,d=linear;n=max(abs(a).bit_length(),abs(d).bit_length())+1
    bits='1'+f'{n:05b}'+signed_bits(a,n)+signed_bits(d,n)
    n=max(abs(b).bit_length(),abs(c).bit_length())+1
    bits+='1'+f'{n:05b}'+signed_bits(b,n)+signed_bits(c,n)
    n=max(1,*(abs(v).bit_length()+1 for v in translation));assert n<32
    bits+=f'{n:05b}'+''.join(signed_bits(v,n) for v in translation)
    return pack(bits)


def factored(raw,cid,factor):
    source=parse(raw);a,b,c,d,tx,ty=factor;assert tx==ty==0
    old=source['styles'][1];aa,bb,cc,dd=old['linear_fixed'];x,y=old['translation_twips']
    linear=[a*aa+c*bb,b*aa+d*bb,a*cc+c*dd,b*cc+d*dd];translation=[a*x+c*y,b*x+d*y]
    points=[[a*x+c*y,b*x+d*y] for x,y in source['mask_twips']]
    bounds=rect(min(p[0] for p in points),max(p[0] for p in points),min(p[1] for p in points),max(p[1] for p in points))
    x,y=points[0];n=max(1,abs(x).bit_length()+1,abs(y).bit_length()+1)
    bits='000101'+f'{n:05b}'+signed_bits(x,n)+signed_bits(y,n)+'10'
    for (x,y),(xx,yy) in zip(points,points[1:]+points[:1]):
        dx,dy=xx-x,yy-y;n=max(2,abs(dx).bit_length()+1,abs(dy).bit_length()+1);assert n<=17
        bits+='11'+f'{n-2:04b}'+'1'+signed_bits(dx,n)+signed_bits(dy,n)
    bits+='000000'
    payload=struct.pack('<H',cid)+bounds+b'\x02'+bytes.fromhex(source['styles'][0]['raw_hex'])+b'\x43'+struct.pack('<H',55)+matrix(linear,translation)+b'\x00\x20'+pack(bits)
    result=struct.pack('<HI',(2<<6)|63,len(payload))+payload;parsed=parse(result)
    assert parsed['styles'][0]==source['styles'][0]
    assert parsed['styles'][1]['linear_fixed']==linear and parsed['styles'][1]['translation_twips']==translation and parsed['mask_twips']==points
    return result,parsed
