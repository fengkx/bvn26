from pathlib import Path
import sys,json
from PIL import Image
sys.path[:0]=['.','tools','tools/probes']
from sampling_bitmap import decode_row
folder=Path(sys.argv[1]);out=folder/'images';out.mkdir(exist_ok=True);data=None;row=0;ticks=[]
for line in (folder/'original.log').read_text().splitlines():
 p=line.split('|',7)
 if len(p)!=8:continue
 tick=int(p[5]);kind=p[6];value=p[7]
 if kind=='bitmap_begin':data=bytearray();row=0
 elif kind=='bitmap_row':
  y,s=value.split(',',1);assert int(y)==row;data.extend(decode_row(s));row+=1
 elif kind=='bitmap_end':
  assert row==400 and value=='400';Image.frombytes('RGBA',(600,400),bytes(data)).save(out/f'{tick:03}.png');ticks.append(tick)
print(ticks)
