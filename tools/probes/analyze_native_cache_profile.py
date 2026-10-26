"""Locate sampled native call sites without inferring unsampled arithmetic branches."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import re
import struct
from tools.probes.analyze_bitmap_cache_width import ROOT
from tools.probes.extract_cache_affine_binary import BINARY_SHA256

EDGES = {0x1000f5000:0x10015d560,0x10015d5a0:0x10015c080,
         0x10015c4de:0x100157cb0,0x10015d144:0x10020ee10}


def read(path):
    return gzip.decompress(path.read_bytes()).decode() if path.suffix=='.gz' else path.read_text()


def analyze(evidence):
    result={}
    for kind,expected in [('cached','true'),('uncached','false')]:
        folder=evidence/kind
        build=json.loads((folder/'build.json').read_text())
        assert hashlib.sha256((ROOT/build['source']).read_bytes()).hexdigest()==build['source_sha256']
        rows=[line.split('|') for line in read(folder/'native.log.gz').splitlines() if line.startswith('AIREF|')]
        assert len(rows)==5 and rows[-1][6:]==['done','ok']
        for i,row in enumerate(rows):assert row[1]==build['run_id'] and row[2:6]==[str(i),'0','0','0']
        assert rows[1][6:]==['cache',expected] and rows[2][6:]==['iterations','60000']
        profile=json.loads((folder/'profile.json').read_text())
        assert profile['sample_exit']==0 and profile['capture_complete'] and not profile['pixel_reference']
        assert profile['binary_sha256']==BINARY_SHA256 and profile['movie_sha256']==build['outputs_sha256']['game/main.swf']
        text=read(folder/'sample.txt.gz').split('Total number in stack')[0]
        counts=Counter()
        for line in text.splitlines():
            match=re.search(r'(\d+) \?\?\?  \(in Flash Player Debugger\).*?load address (0x[0-9a-f]+) \+ (0x[0-9a-f]+)',line)
            if match:counts[int(match[3],16)]+=int(match[1])
        assert counts
        result[kind]={'unique_reported_pcs':len(counts),'call_return_observations':{hex(site+5):counts[site+5-0x100000000] for site in EDGES},
                      'generic_affine_observed_pcs':[hex(pc+0x100000000) for pc in sorted(counts) if 0x29dad0<=pc<0x29e32d]}
    return {'profiles':result,'specific_normalization_branch_verified':False,'candidate_admitted':False,'production_admitted':False,
            'count_semantics':'Inclusive sample-tree occurrences, not invocation counts; absence does not establish nonexecution.'}


def static_edges(binary):
    data=binary.read_bytes();assert hashlib.sha256(data).hexdigest()==BINARY_SHA256
    position=32;segments=[]
    for _ in range(struct.unpack_from('<I',data,16)[0]):
        command,size=struct.unpack_from('<II',data,position)
        if command==0x19:
            _,_,_,address,_,offset,length=struct.unpack_from('<II16sQQQQ',data,position);segments.append((address,offset,length))
        position+=size
    result=[]
    for site,target in EDGES.items():
        offsets=[offset+site-base for base,offset,length in segments if base<=site and site+5<=base+length];assert len(offsets)==1
        raw=data[offsets[0]:offsets[0]+5];assert raw[0]==0xe8 and site+5+struct.unpack('<i',raw[1:])[0]==target
        result.append({'site':hex(site),'return_pc':hex(site+5),'target':hex(target),'bytes':raw.hex()})
    return {'binary_sha256':BINARY_SHA256,'call_edges':result,'specific_normalization_branch_verified':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--evidence',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--binary',type=Path)
    a=p.parse_args();a.output.write_text(json.dumps(analyze(a.evidence),indent=2)+'\n')
    if a.binary:(a.evidence/'static-edges.json').write_text(json.dumps(static_edges(a.binary),indent=2)+'\n')
