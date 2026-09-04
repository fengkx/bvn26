"""Read SWF headers, tag counts, frame labels and linkage names without executing it.
Usage: python3 inspect_swf.py FILE.swf [FILE.swf ...]
Supports FWS and zlib-compressed CWS. Frame numbers are 1-based.
"""
import collections, hashlib, json, struct, sys, zlib
from pathlib import Path

def inspect(path):
    raw=Path(path).read_bytes()
    if raw[:3] not in (b'FWS',b'CWS'):
        raise ValueError('Unsupported SWF signature')
    data=raw if raw[:3]==b'FWS' else raw[:8]+zlib.decompress(raw[8:])
    declared=struct.unpack_from('<I',data,4)[0]
    if len(data)!=declared:raise ValueError('SWF decompressed length mismatch')
    n=data[8]>>3;bits=''.join(f'{v:08b}' for v in data[8:25]);rect=[]
    for i in range(4):
        v=int(bits[5+i*n:5+(i+1)*n],2)
        rect.append(v-(1<<n) if v>>(n-1) else v)
    off=8+(5+4*n+7)//8;fps,frames=struct.unpack_from('<HH',data,off);off+=4
    counts=collections.Counter();timelines=[];exports=[];clip_action_tags=[];attrs=None
    def walk(start,end,name,framecount):
        nonlocal attrs
        p=start;frame=1;labels=[];actions=[];ended=False
        while p+2<=end:
            h=struct.unpack_from('<H',data,p)[0];p+=2;t=h>>6;size=h&63
            if size==63:size=struct.unpack_from('<I',data,p)[0];p+=4
            if p+size>end:raise ValueError(f'Truncated tag {t}')
            v=data[p:p+size];counts[t]+=1
            if t==39:
                cid,nframes=struct.unpack_from('<HH',v)
                walk(p+4,p+size,f'sprite_{cid}',nframes)
            elif t in (26,70) and v and v[0]&0x80:
                # PlaceObject2/3 stores HasClipActions in the high bit of its
                # first flags byte. The action payload is kept for M0/M1
                # semantic tooling; inventory must still make every occurrence
                # visible so it cannot be silently lost by a later converter.
                clip_action_tags.append({'timeline':name,'frame':frame,'tag':t,'bytes':size})
            elif t==43:labels.append({'frame':frame,'label':v.split(b'\0')[0].decode('utf8','replace')})
            elif t in (12,59):actions.append({'frame':frame,'tag':t,'bytes':size})
            elif t==69:attrs=struct.unpack_from('<I',v)[0]
            elif t in (56,76):
                num=struct.unpack_from('<H',v)[0];q=2
                for _ in range(num):
                    cid=struct.unpack_from('<H',v,q)[0];q+=2;r=v.index(0,q)
                    exports.append({'character_id':cid,'name':v[q:r].decode('utf8','replace')});q=r+1
            if t==1:frame+=1
            p+=size
            if t==0:ended=True;break
        if not ended:raise ValueError(f'Missing end tag in {name}')
        if p!=end:raise ValueError(f'Trailing bytes in {name}')
        timelines.append({'name':name,'declared_frames':framecount,'show_frames':frame-1,'labels':labels,'actions':actions})
    walk(off,len(data),'root',frames)
    return {'file':Path(path).name,'sha256':hashlib.sha256(raw).hexdigest(),'file_bytes':len(raw),'uncompressed_bytes':len(data),'swf_version':raw[3], 'avm':'AVM2' if attrs is not None and attrs&8 else 'AVM1', 'file_attributes':attrs, 'width':(rect[1]-rect[0])/20,'height':(rect[3]-rect[2])/20,'header_fps':fps/256,'root_frames':frames,'tag_counts':dict(counts),'exports':exports,'clip_action_tags':clip_action_tags,'timelines':timelines}

if __name__=='__main__':
    print(json.dumps([inspect(p) for p in sys.argv[1:]],ensure_ascii=False,indent=2))
