"""Capture supported fixed-input display observations under the caller's lock."""
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'tools/probes'))
from compare_mode_reference import compare
state = subprocess.check_output(['ioreg', '-n', 'Root', '-d1'], text=True)
if not re.search(r'"IOConsoleLocked"\s*=\s*No\b', state):
    raise SystemExit('DESKTOP_LOCKED_OR_UNKNOWN_STOP')
probe = OUT / 'probe-visibility-r02'
output = OUT / 'original-visibility-r01'
output.mkdir(exist_ok=False)
subprocess.run([sys.executable, str(ROOT / 'tools/probes/capture_native_player.py'),
                str(probe), str(output / 'original.log'), '--allow-window-activation'], check=True)
subprocess.run([sys.executable, str(ROOT / 'tools/probes/collect_ai_reference.py'),
                '--build', str(probe), '--capture', str(output / 'original.log'),
                '--output', str(output / 'collected'), '--retain-post-done-frames'], check=True)
events = output / 'collected/events.jsonl'
comparison = compare(events, OUT / 'native-visibility-r01/states.json')
source = []
for line in events.read_text().splitlines():
    event = json.loads(line)
    if event['kind'] != 'display_node' or event['fight_tick'] < 0:
        continue
    fields = event['value'].split(',')
    path = unquote(fields[0])
    if path not in ('_level0.game.p1', '_level0.game.p2'):
        continue
    source.append({'tick':event['fight_tick'],'slot':path.rsplit('.',1)[1], 'visible':json.loads(fields[18])})
native = json.loads((OUT / 'native-visibility-r01/states.json.visibility.json').read_text())
source.sort(key=lambda x:(x['tick'],x['slot']))
native.sort(key=lambda x:(x['tick'],x['slot']))
differences = [{'source':a,'native':b} for a,b in zip(source,native) if a!=b]
transitions=[]
last={}
for row in source:
    if last.get(row['slot']) != row['visible']:
        transitions.append(row)
    last[row['slot']]=row['visible']
result={'actor_states':comparison,'visibility':{'status':'matched' if source and len(source)==len(native) and not differences else 'different','source_rows':len(source),'native_rows':len(native),'differences':differences,'transitions':transitions},'scope':'Fixed diagnostic inputs; readonly MovieClip visibility sampling. Exact actor fields also compared to test observer noninterference.'}
(OUT / 'visibility-comparison-r01.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'actor_states':comparison['status'],'visibility':result['visibility']['status'],'transitions':transitions}))
