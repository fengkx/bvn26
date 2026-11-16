"""Run the lane's headed visual fixtures while the caller owns flash_lock."""
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'evidence/characters/minrenx'
GODOT = '/Users/fengkx/me/agent-code/toolchains/godot-4.7.2/Godot.app/Contents/MacOS/Godot'
results = []
for name, folder in [('minrenx_visual_capture', 'screenshots'), ('minrenx_form_visual_capture', 'form-screenshots')]:
    command = [GODOT, '--path', str(ROOT / 'godot'), '--rendering-method', 'gl_compatibility',
               '--log-file', str(OUT / 'logs' / (name + '.engine.log')),
               '-s', 'res://tests/' + name + '.gd', '--quit-after', '3000', '--', str(OUT / folder)]
    run = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=240)
    log = run.stdout + run.stderr
    (OUT / 'logs' / (name + '.log')).write_text(log)
    marker = name.upper() + '_OK'
    passed = run.returncode == 0 and marker in log and 'SCRIPT ERROR' not in log
    results.append({'script': name, 'command': command, 'exit': run.returncode,
                    'render_capture_completed': passed,
                    'unaccepted_exit_residuals': [line for line in log.splitlines()
                       if any(word in line for word in ['ERROR:', 'WARNING:', 'leaked', 'still in use'])]})
    (OUT / 'native-visual-execution.json').write_text(json.dumps(results, indent=2) + '\n')
    assert passed, name
