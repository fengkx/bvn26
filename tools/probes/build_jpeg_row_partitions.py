"""Vary row geometry independently of constant JPEG color values."""
import argparse
import hashlib
from io import BytesIO
from pathlib import Path
from PIL import Image
from tools.probes.build_jpeg_controls import prepare_controls


def controls():
    result=[]
    for y in (0,1,127,255):
        for cb in (120,127,133,140):
            for cr in (120,128,132):
                for width in (7,8,9,15,16,17,23,24,25):
                    for subsampling in (0,2):
                        image=Image.new('YCbCr',(width,8),(y,cb,cr));data=BytesIO()
                        image.save(data,format='JPEG',quality=100,subsampling=subsampling,optimize=False)
                        jpeg=data.getvalue()
                        result.append(({'id':len(result),'width':width,'height':8,'ycbcr':[y,cb,cr],'subsampling':subsampling,
                                        'input_sha256':hashlib.sha256(image.tobytes()).hexdigest(),
                                        'jpeg_sha256':hashlib.sha256(jpeg).hexdigest()},jpeg))
    assert len(result)==864
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--ffdec',type=Path,required=True)
    args=parser.parse_args();prepare_controls('jpeg-row-partitions',controls(),args.output,args.ffdec)
