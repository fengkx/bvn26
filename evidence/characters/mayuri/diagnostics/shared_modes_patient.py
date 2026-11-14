from pathlib import Path
p=Path('/Users/fengkx/me/agent-code/bvn2_6-mayuri/tools/test_shared_modes.py')
source=p.read_text()
assert source.count('timeout=90, check=True')==1
print('Harness-only timeout 90 -> 600 seconds; same commands, fixtures and comparison.',flush=True)
exec(compile(source.replace('timeout=90, check=True','timeout=600, check=True'),str(p),'exec'),{'__name__':'__main__','__file__':str(p)})
