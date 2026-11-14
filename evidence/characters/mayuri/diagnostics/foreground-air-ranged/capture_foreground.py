from pathlib import Path
source_path = Path('/Users/fengkx/me/agent-code/bvn2_6-mayuri/tools/probes/capture_native_player.py')
source = source_path.read_text()
old = "['/usr/bin/open', '-g', '-n', '-W'"
assert source.count(old) == 1
source = source.replace(old, "['/usr/bin/open', '-n', '-W'")
source = source.replace('default=120)', 'default=600)')
exec(compile(source, str(source_path), 'exec'), {'__file__': str(source_path), '__name__': '__main__'})
