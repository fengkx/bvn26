from pathlib import Path
import json,time,subprocess,sys
r=Path('/private/tmp/bvn-roster-live');previous=0
while True:
 count=len(json.loads((r/'break-native/execution.json').read_text()))
 if count!=previous:
  for script in ['compare_extra.py','extra_contacts.py','archive_extra.py']:
   with (r/('final-'+script+'.log')).open('a') as f:subprocess.run([sys.executable,str(r/script)],stdout=f,stderr=subprocess.STDOUT,check=True)
  previous=count;print('BREAK_EVIDENCE_READY',count,flush=True)
 if count==35:break
 time.sleep(10)
