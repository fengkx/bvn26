from pathlib import Path
import subprocess,sys
from PIL import Image,ImageDraw
r=Path('/private/tmp/bvn-roster-live')
for p in (r/'contact').glob('*.jpg'):
 Image.open(p).resize((600,1700)).save(p.with_suffix('.small.png'))
for category,ticks in [('helper',[18,30,45,60,90,145,205,420]),('curved',[149,151,155,160]),('break',[16,24,32])]:
 out=r/(category+'-contact');out.mkdir(exist_ok=True)
 for src in sorted((r/(category+'-original')).iterdir()):
  if not src.is_dir() or not (src/'collected/summary.json').exists():continue
  dest=out/(src.name+'.png')
  if dest.exists():continue
  subprocess.run([sys.executable,str(r/'decode.py'),str(src)],check=True,stdout=subprocess.DEVNULL)
  native=r/(category+'-native')/src.name
  if category=='curved':native=r/'curved-native'
  sheet=Image.new('RGB',(1200,len(ticks)*425),'#202020');d=ImageDraw.Draw(sheet)
  for i,t in enumerate(ticks):
   d.text((4,i*425+4),f'{src.name} tick {t}: Flash | Godot',fill='white')
   sheet.paste(Image.open(src/f'images/{t:03}.png'),(0,i*425+25));sheet.paste(Image.open(native/f'{t:03}.png'),(600,i*425+25))
  sheet.resize((600,len(ticks)*212)).save(dest)
  print(dest,flush=True)
