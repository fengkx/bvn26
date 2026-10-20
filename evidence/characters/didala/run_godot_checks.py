import json, os, subprocess, time
from pathlib import Path
out = Path(os.environ['BVN_CHECK_DIR']) / 'godot'
out.mkdir()
selected = json.loads(Path('evidence/characters/itachi/godot-checks.json').read_text())
names = [r['name'] for r in selected] + ['clip_placement_once_smoke', 'projectile_child_clock_smoke', 'projectile_contact_history_smoke', 'didala_rollback_smoke']
baseline = json.loads(Path('evidence/characters/itachi/baseline-godot-failures.json').read_text())
known = {r['name'] + '_smoke': r for r in baseline['checks']}
assert set(known) == {n + '_smoke' for n in
    ['ai_colors', 'ai_context', 'ai_host', 'title_menu_source', 'ai_hit_gate']}

def failure_signature(log):
    lines = log.splitlines()
    return {'errors': [line for line in lines if line.startswith(('SCRIPT ERROR:', 'ERROR:'))
                       and 'Condition "ret != noErr"' not in line],
            'markers': [line for line in lines if '_SMOKE_OK' in line or line == 'stage_sound_smoke ok']}

results = []
for name in names:
    started = time.monotonic()
    command = [os.environ['BVN_GODOT'], '--headless', '--verbose', '--path', 'godot',
               '--log-file', str(out / (name + '.engine.log')), '--quit-after', '5000',
               '-s', 'res://tests/' + name + '.gd']
    timed_out = False
    try:
        run = subprocess.run(command, capture_output=True, text=True, timeout=600)
        log, code = run.stdout + run.stderr, run.returncode
    except subprocess.TimeoutExpired as exc:
        def text(value):
            return value.decode(errors='replace') if isinstance(value, bytes) else (value or '')
        log = text(exc.stdout) + text(exc.stderr)
        code, timed_out = -1, True
    (out / (name + '.log')).write_text(log)
    leaks = [line for line in log.splitlines() if line.startswith('Leaked instance:')]
    audio = bool(leaks) and all(line.startswith(tuple('Leaked instance: ' + kind + ':' for kind in
        ['AudioStreamMP3', 'AudioStreamPlaybackMP3', 'AudioStreamWAV', 'AudioStreamPlaybackWAV'])) for line in leaks)
    errors = [line for line in log.splitlines() if line.startswith('ERROR:')
              and 'Condition "ret != noErr"' not in line
              and not (audio and 'resources still in use at exit' in line)]
    marker = {'stage_sound_smoke': 'stage_sound_smoke ok',
              'nested_start_sound_smoke': 'NESTED_START_SOUND_SMOKE_PASSED'}.get(name, name.upper() + '_OK')
    passed = code == 0 and marker in log and not errors and not any(
        token in log for token in ['SCRIPT ERROR', 'Parse Error', 'Assertion failed'])
    if name == 'rollback_roster_smoke':
        passed = passed and log.count('ROLLBACK_ROSTER_CASE_OK') == len(json.loads(Path('godot/generated/main/character_selection/available.json').read_text())['fighters'])
    signature = failure_signature(log)
    expected = known.get(name)
    baseline_match = bool(expected) and not timed_out and code == expected['exit'] and signature == {
        'errors': expected['errors'], 'markers': expected['markers']}
    results.append({'name': name, 'passed': passed, 'exit': code, 'timed_out': timed_out,
                    'signature': signature, 'baseline_match': baseline_match,
                    'seconds': time.monotonic() - started})
(out / 'report.json').write_text(json.dumps(results, indent=2))
for row in results:
    print(row)
assert all(r['passed'] or r['baseline_match'] for r in results)
print('GODOT_GATE_OK passed=', sum(r['passed'] for r in results),
      'matched_baseline_failures=', sum(not r['passed'] and r['baseline_match'] for r in results))