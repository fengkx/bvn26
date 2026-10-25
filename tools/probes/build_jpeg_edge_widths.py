"""Vary only SOF width while preserving original JPEG coefficient/entropy bytes."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import zlib
from tools.probes.build_bound_bitmap_component import ROOT, source_tags, tag
from tools.probes.build_flash_filter_probe import build


def cases():
    source=ROOT/'game/fighter/orochimaru.swf'
    inventory=json.loads((ROOT/'evidence/importer-loud-fail/r209/orochimaru.json').read_text())
    assert hashlib.sha256(source.read_bytes()).hexdigest()==inventory['source']['sha256']
    payload,raw=next((p,r) for c,p,r in source_tags(source) if c==35 and struct.unpack_from('<H',p)[0]==340)
    assert hashlib.sha256(raw).hexdigest()==inventory['raw_tag_sha256']['340']
    n=struct.unpack_from('<I',payload,2)[0];jpeg=payload[6:6+n]
    sof=jpeg.index(b'\xff\xc0');assert struct.unpack_from('>HH',jpeg,sof+5)==(378,186)
    result=[({'id':0,'width':186,'height':378,'tag':35,'bitmap_id':340,'jpeg_sha256':hashlib.sha256(jpeg).hexdigest()},raw,jpeg)]
    for width in (184,185,186,187,188,192):
        modified=bytearray(jpeg);struct.pack_into('>H',modified,sof+7,width);modified=bytes(modified)
        assert modified[:sof+7]==jpeg[:sof+7] and modified[sof+9:]==jpeg[sof+9:]
        assert (width+15)//16==(186+15)//16
        i=len(result);bitmap_id=400+i
        result.append(({'id':i,'width':width,'height':378,'tag':21,'bitmap_id':bitmap_id,
                        'sof_width_offset':sof+7,'jpeg_sha256':hashlib.sha256(modified).hexdigest()},
                       tag(21,struct.pack('<H',bitmap_id)+modified),modified))
    return result


def prepare(output,ffdec):
    report=build('jpeg-edge-widths',output,ffdec);rows=cases()
    tags=b''.join(raw for _,raw,_ in rows)
    exports=struct.pack('<H',len(rows))+b''.join(struct.pack('<H',c['bitmap_id'])+f"jpeg_edge_{c['id']}".encode()+b'\0' for c,_,_ in rows)
    path=output/'game/main.swf';raw=path.read_bytes();body=raw[8:] if raw[:3]==b'FWS' else zlib.decompress(raw[8:])
    start=(5+4*(body[0]>>3)+7)//8+4;body=body[:start]+tags+tag(56,exports)+body[start:]
    path.write_bytes(b'FWS'+raw[3:4]+struct.pack('<I',len(body)+8)+body)
    report.update({'cases':[c for c,_,_ in rows],'production_admitted':False})
    report['outputs_sha256']['game/main.swf']=hashlib.sha256(path.read_bytes()).hexdigest()
    (output/'build.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--ffdec',type=Path,required=True)
    args=parser.parse_args();prepare(args.output,args.ffdec)
