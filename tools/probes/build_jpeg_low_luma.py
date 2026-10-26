"""Independently encoded constant YCbCr controls around residual low luma."""
import argparse
import hashlib
from io import BytesIO
from pathlib import Path
from PIL import Image
from tools.probes.build_jpeg_controls import prepare_controls


def controls():
    result=[]
    for y in (0,1,2,3,16,127,254,255):
        for cb in range(129,136):
            for cr in range(131,135):
                for subsampling in (0,2):
                    image=Image.new('YCbCr',(16,16),(y,cb,cr));data=BytesIO()
                    image.save(data,format='JPEG',quality=100,subsampling=subsampling,optimize=False)
                    jpeg=data.getvalue()
                    result.append(({'id':len(result),'ycbcr':[y,cb,cr],'subsampling':subsampling,
                                    'input_sha256':hashlib.sha256(image.tobytes()).hexdigest(),
                                    'jpeg_sha256':hashlib.sha256(jpeg).hexdigest()},jpeg))
    assert len(result)==448
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--ffdec',type=Path,required=True)
    args=parser.parse_args();prepare_controls('jpeg-low-luma',controls(),args.output,args.ffdec)
