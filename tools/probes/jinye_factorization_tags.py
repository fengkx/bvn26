"""Encode and independently parse bounded synthetic nearest bitmap quads."""
import struct
from tools.probes.build_minimal_swf import rect


def signed_bits(value,width):
    assert -(1<<(width-1))<=value<(1<<(width-1))
    return f'{value&((1<<width)-1):0{width}b}'


def pack(bits):
    bits+='0'*(-len(bits)%8)
    return int(bits,2).to_bytes(len(bits)//8,'big')


def matrix_bytes(matrix):
    a,b,c,d,tx,ty=matrix
    assert tx==ty==0
    aa,dd=int(a*20*65536),int(d*20*65536)
    assert aa==a*20*65536 and dd==d*20*65536
    n=max(aa.bit_length(),dd.bit_length())+1
    bits='1'+f'{n:05b}'+signed_bits(aa,n)+signed_bits(dd,n)
    bb,cc=int(b*20*65536),int(c*20*65536)
    assert bb==b*20*65536 and cc==c*20*65536
    if bb or cc:
        n=max(abs(bb).bit_length(),abs(cc).bit_length())+1
        bits+='1'+f'{n:05b}'+signed_bits(bb,n)+signed_bits(cc,n)
    else:bits+='0'
    return pack(bits+'00000')


def encode_shape(cid,fill,polygon):
    points=[(int(x*20),int(y*20)) for x,y in polygon]
    assert all(x*20==px and y*20==py for (x,y),(px,py) in zip(polygon,points))
    bounds=rect(min(p[0] for p in points),max(p[0] for p in points),min(p[1] for p in points),max(p[1] for p in points))
    x,y=points[0];width=max(1,abs(x).bit_length()+1,abs(y).bit_length()+1)
    bits='0'+'00101'+f'{width:05b}'+signed_bits(x,width)+signed_bits(y,width)+'1'
    for (x,y),(xx,yy) in zip(points,points[1:]+points[:1]):
        dx,dy=xx-x,yy-y;n=max(2,abs(dx).bit_length()+1,abs(dy).bit_length()+1)
        assert n<=17
        bits+='11'+f'{n-2:04b}'+'1'+signed_bits(dx,n)+signed_bits(dy,n)
    bits+='000000'
    payload=struct.pack('<H',cid)+bounds+b'\x01\x43'+struct.pack('<H',55)+matrix_bytes(fill)+b'\x00\x10'+pack(bits)
    return struct.pack('<HI',(2<<6)|63,len(payload))+payload


class Reader:
    def __init__(self,data):self.data=data;self.pos=0
    def bits(self,n,signed=False):
        assert self.pos+n<=len(self.data)*8
        value=0
        for _ in range(n):value=(value<<1)|((self.data[self.pos//8]>>(7-self.pos%8))&1);self.pos+=1
        return value-(1<<n) if signed and n and value&(1<<(n-1)) else value
    def align(self):
        while self.pos%8:assert self.bits(1)==0
    def ui16(self):return self.bits(8)+256*self.bits(8)


def parse_shape(raw):
    header=struct.unpack_from('<H',raw)[0];assert header>>6==2 and header&63==63
    assert struct.unpack_from('<I',raw,2)[0]==len(raw)-6
    reader=Reader(raw[6:]);cid=reader.ui16();n=reader.bits(5);bounds=[reader.bits(n,True) for _ in range(4)];reader.align()
    assert reader.bits(8)==1 and reader.bits(8)==67;bitmap=reader.ui16();assert bitmap==55
    linear=[65536,0,0,65536]
    if reader.bits(1):
        n=reader.bits(5);linear[0]=reader.bits(n,True);linear[3]=reader.bits(n,True)
    if reader.bits(1):
        n=reader.bits(5);linear[1]=reader.bits(n,True);linear[2]=reader.bits(n,True)
    n=reader.bits(5);translation=[reader.bits(n,True),reader.bits(n,True)];reader.align()
    assert reader.bits(8)==0 and reader.bits(4)==1 and reader.bits(4)==0
    assert reader.bits(1)==0 and reader.bits(5)==5
    n=reader.bits(5);x,y=reader.bits(n,True),reader.bits(n,True);assert reader.bits(1)==1
    points=[[x,y]]
    for _ in range(4):
        assert reader.bits(1)==1 and reader.bits(1)==1
        n=reader.bits(4)+2;assert reader.bits(1)==1
        x+=reader.bits(n,True);y+=reader.bits(n,True);points.append([x,y])
    assert reader.bits(6)==0;reader.align();assert reader.pos==len(reader.data)*8 and points[0]==points[-1]
    assert bounds==[min(p[0] for p in points),max(p[0] for p in points),min(p[1] for p in points),max(p[1] for p in points)]
    return {'shape':cid,'bitmap':bitmap,'fill_type':67,'fill_linear_fixed':linear,'fill_translation_twips':translation,
            'fill':[v/(65536*20) for v in linear]+[v/20 for v in translation],
            'mask_twips':points[:-1],'mask':[[x/20,y/20] for x,y in points[:-1]],'bounds_twips':bounds}
