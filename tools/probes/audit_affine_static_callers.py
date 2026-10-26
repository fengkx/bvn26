"""Verify static affine call bytes and intersect independently captured profile PCs."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import re
import struct

from tools.probes.extract_cache_affine_binary import BINARY_SHA256

TARGETS = (0x10029dad0, 0x10029de20)


def profile_counts(path):
    text = gzip.decompress(path.read_bytes()).decode() if path.suffix == '.gz' else path.read_text()
    counts = Counter()
    for line in text.split('Total number in stack')[0].splitlines():
        match = re.search(r'(\d+) \?\?\?  \(in Flash Player Debugger\).*?load address (0x[0-9a-f]+) \+ (0x[0-9a-f]+)', line)
        if match:
            counts[int(match[3],16)+0x100000000] += int(match[1])
    if not counts:
        raise ValueError('Profile contains no recognizable Flash module-relative PCs')
    return counts


def verify_call(raw, site, target):
    if len(raw) != 5 or raw[0] != 0xe8 or site+5+struct.unpack('<i',raw[1:])[0] != target:
        raise ValueError('Disassembly call does not match a direct rel32 target')


def analyze(binary, disassembly, profiles):
    data = binary.read_bytes()
    if hashlib.sha256(data).hexdigest() != BINARY_SHA256:
        raise ValueError('Executable differs from independently pinned Flash build')
    segments, position = [], 32
    for _ in range(struct.unpack_from('<I',data,16)[0]):
        command,size = struct.unpack_from('<II',data,position)
        if command == 0x19:
            _,_,_,address,_,offset,length = struct.unpack_from('<II16sQQQQ',data,position)
            segments.append((address,offset,length))
        position += size
    counts = {name:profile_counts(path) for name,path in profiles.items()}
    edges = []
    pattern = re.compile(r'([0-9a-f]+):\s+([0-9a-f ]+)\s+callq\s+0x([0-9a-f]+)\s*$')
    for line in disassembly.open():
        match = pattern.match(line)
        if not match or int(match[3],16) not in TARGETS:
            continue
        site,target = int(match[1],16),int(match[3],16)
        raw = bytes.fromhex(match[2])
        verify_call(raw,site,target)
        offsets = [offset+site-base for base,offset,length in segments if base <= site and site+5 <= base+length]
        if len(offsets) != 1 or data[offsets[0]:offsets[0]+5] != raw:
            raise ValueError('Disassembly bytes differ from pinned executable')
        edges.append({'site':hex(site),'target':hex(target),'bytes':raw.hex(),'return_pc':hex(site+5),
                      'profile_observations':{name:c[site+5] for name,c in counts.items()}})
    if not edges or len({e['site'] for e in edges}) != len(edges):
        raise ValueError('No direct calls found or duplicate disassembly call sites')
    return {'binary_sha256':BINARY_SHA256,'disassembly_sha256':hashlib.sha256(disassembly.read_bytes()).hexdigest(),
            'profiles':{name:{'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                              'unique_reported_pcs':len(counts[name])} for name,path in profiles.items()},
            'direct_edges':edges,'counts':dict(Counter(e['target'] for e in edges)),
            'sampled_edges':[e for e in edges if any(e['profile_observations'].values())],
            'count_semantics':'Inclusive profile-tree observations, not invocation counts; no absence-to-nonexecution inference.',
            'bitmap_fill_setup_routing_established':False,'production_admitted':False}


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary',type=Path,required=True)
    parser.add_argument('--disassembly',type=Path,required=True,help='Full llvm-objdump/otool style disassembly including address and raw bytes')
    parser.add_argument('--profile',action='append',default=[],metavar='NAME=PATH')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();profiles={}
    for item in args.profile:
        name,separator,path=item.partition('=')
        if not separator or not name or name in profiles:parser.error('Profiles require unique NAME=PATH arguments')
        profiles[name]=Path(path)
    result=analyze(args.binary,args.disassembly,profiles)
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'counts':result['counts'],'sampled_edges':len(result['sampled_edges'])}))
