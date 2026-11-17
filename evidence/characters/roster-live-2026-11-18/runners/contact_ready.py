from pathlib import Path
import json,subprocess,sys
from PIL import Image, ImageDraw
r=Path('/private/tmp/bvn-roster-live');out=r/'contact';out.mkdir(exist_ok=True)
for entry in json.loads((r/'native-r02/execution.json').read_text()):
 slug=entry['id'];src=r/'original'/slug
 if not (src/'collected/summary.json').exists():continue
 if not (src/'images/420.png').exists():subprocess.run([sys.executable,str(r/'decode.py'),str(src)],check=True,stdout=subprocess.DEVNULL)
 dest=out/(slug+'.jpg')
 if dest.exists():continue
 native=r/'native-r02'/slug
 if entry['method']=='terminal-replay':native=native/'terminal-replay'
 ticks=[18,60,145,175,205,240,300,420]
 sheet=Image.new('RGB',(1200,8*425),'#202020');draw=ImageDraw.Draw(sheet)
 for i,t in enumerate(ticks):
  draw.text((4,i*425+4),f'{slug} tick {t}: Flash | Godot',fill='white')
  sheet.paste(Image.open(src/f'images/{t:03}.png'),(0,i*425+25));sheet.paste(Image.open(native/f'{t:03}.png'),(600,i*425+25))
 sheet.save(dest)
 print(slug,flush=True)
