# Regression evidence index

Reference baseline: `3423be31` (2026-10-15). This page locates retained evidence
and reproduction commands; it does not record a new gameplay acceptance run.
Read [SOURCE_FIRST](SOURCE_FIRST.md) before changing runtime behaviour and follow
[HIT_RECEIVE_SOP](HIT_RECEIVE_SOP.md) for the hit/receive chain. Current partial
acceptance remains in [STATUS](STATUS.md); historical reports and task states
are unchanged.

## Retained evidence

| Evidence | What it establishes / how to use it |
|---|---|
| [103-case replay index](../evidence/characters/itachi/review-mediums/regressions.json) | 103 retained cases, 16 implemented fighters, 65,726 states over 14 exact fields. Each result supplies `fixture`, compressed `source`, compressed `native`, and SHA-256 values. This is the current saved replay selection. |
| [Review scope and source-first answers](../evidence/characters/itachi/review-mediums/README.md) | Placement lifetime, cancellation coverage, original-input provenance and diagnostic limitations; links the individual original builds and instrumentation. |
| [Review results and timings](../evidence/characters/itachi/review-mediums/checks.json) | Separates the 103 saved cases from 35 newly captured Itachi cases. The latter are additional evidence, not a replacement for the cross-character selection. |
| [Original Itachi acceptance](../evidence/characters/itachi/README.md) and [checks](../evidence/characters/itachi/checks.json) | Earlier 71 prior-fighter cases plus 32 Itachi cases, Python counts, AI scope, rollback coverage and limitations. |
| [36 Godot check results](../evidence/characters/itachi/godot-checks.json) | Machine-readable test names and actual markers; includes all 15 rollback foundation checks. Do not run those 15 twice in the final gate. |
| [Later focused Godot checks](../evidence/characters/itachi/review-mediums/godot-checks.json) | Additional placement/rollback review context and timings. The roster's old summary says 11, but 16 per-fighter success records establish executed coverage. |
| [Five historical failures](../evidence/characters/itachi/baseline-godot-failures.json) | Records failures on `84d567fe`; these are inherited reference signatures, not a fresh result on the current candidate. |
| [Protected-function record](../evidence/characters/itachi/review-mediums/preservation.json) | `_clear_interrupted_super_preparation`: 544 bytes, SHA-256 `d39b2b50d96d37ac717e1d1e8e9ccd711a67f6bbadcee6afc30593d6e0caa91e`. Keep its bytes, call position and conditions unchanged. The anti-deadlock deviation is intentional. |

“All-character” means the 16 implemented fighters listed in the replay index:
`byakuya`, `chad`, `itachi`, `kakashi`, `lee`, `minren`, `neji`, `renji`, `rifagu`,
`rukia`, `sakura`, `sasuke`, `yihu`, `yijiao`, `yin`, `yulong`. The Sasuke/Renji
fixture group covers two fighters. It does not mean all 35 locked fighter SWFs,
all forms, or full audiovisual/browser/AI acceptance.

The 14 fields are `frame`, `x`, `y`, `xscale`, `action`, `hp`, `ql`, `sw`,
`touch`, `touchFloor`, `hits`, `paused`, `hstm`, `hurtSkling`; the comparator
also checks tick/slot alignment and complete row counts. Preserve original
inputs, tapes, comparison precision and thresholds. Execution, target reach
and original parity are separate results.

## Known failures: review signatures, not just names

| Test (`res://tests/<name>_smoke.gd`) | Retained failure |
|---|---|
| `ai_colors` | `SCRIPT ERROR: Assertion failed.`; no success marker |
| `ai_context` | `SCRIPT ERROR: Assertion failed.`; no success marker |
| `ai_host` | Two `Unconnected CPU frame service` assertions even though `AI_HOST_SMOKE_OK` appears |
| `title_menu_source` | Invalid `hide_single` assignment on `Control (TitleMenu)`, followed by scene-path/resource shutdown errors |
| `ai_hit_gate` | `SCRIPT ERROR: Assertion failed.`; no success marker |

Only these inherited failures may remain during the refactor queue. A new
assertion, timeout, parse error or missing resource in a test with the same name
is not waived. Generic assertion text alone cannot prove an identical cause:
compare its source location and context on base/head when necessary. Exit zero
and a success marker cannot override a script error.

## Check retained files without replaying the game

Run from the repository root. This verifies all indexed fixture, original and
native trace paths and hashes. Trace hashes cover **decompressed** bytes;
`hashes.runtime` is a historical runtime digest, not a requirement that a future
refactor's file bytes remain identical. The protected function has its separate
byte-level check below.

```sh
python3 - <<'PY_CHECK'
import gzip, hashlib, json
from pathlib import Path
index = json.loads(Path('evidence/characters/itachi/review-mediums/regressions.json').read_text())
assert len(index['results']) == index['cases'] == 103
assert len(index['fighters']) == 16
assert len({case['id'] for case in index['results']}) == 103
for case in index['results']:
    for field in ['fixture', 'source', 'native']:
        path = Path(case[field])
        raw = path.read_bytes()
        if path.suffix == '.gz':
            raw = gzip.decompress(raw)
        assert hashlib.sha256(raw).hexdigest() == case['hashes'][field], path
assert sum(case['comparison']['source_states'] for case in index['results']) == 65726
print('EVIDENCE_INDEX_OK cases=103 files=309 hashes=309 fighters=16 states=65726')
PY_CHECK
```

## Exact regression commands

Run from the repository root with Python 3.10+ (record its actual version) and
Godot **4.7.2-stable**. Set `BVN_GODOT` to the executable's absolute path. Import
resources once per fresh worktree. Documentation-only navigation changes run D and the retained-file checks above;
commands below are the implementation gate G, run once on the final candidate.

```sh
export BVN_GODOT=/absolute/path/to/Godot
export BVN_CHECK_DIR="$(mktemp -d /tmp/bvn-refactor-check.XXXXXX)"
"$BVN_GODOT" --version
python3 --version
"$BVN_GODOT" --headless --path godot --editor --import --quit
python3 tools/verify.py
python3 tools/check_handoff.py
python3 -m unittest discover -s tools/tests
```

D is `verify.py` plus `check_handoff.py` and `git diff --check`. If a tracked
manifest-covered document/tool is legitimately changed, review its exact diff
before updating its hash; never regenerate input hashes to hide changes. For contract
changes, also run
`.venv/bin/python tools/validate_contracts.py` with `requirements-dev.txt` installed.

The current 103-case corpus is a report plus individual fixtures/traces, **not**
the older `references.tar.gz` format expected by `test_source_parity_suite.py`.
This copy-paste command uses the existing executor and exact comparator. It
validates the retained hashes and writes fresh results outside the repository;
it does not change source-build provenance or recapture Flash.

```sh
python3 - <<'PY'
import gzip, hashlib, json, os, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.path[:0] = ['tools', 'tools/probes']
from test_move_cases import execute
from compare_mode_reference import compare
root = Path.cwd()
out = Path(os.environ['BVN_CHECK_DIR']) / 'flash-replay'
out.mkdir()
godot = Path(os.environ['BVN_GODOT'])
index = json.loads(Path('evidence/characters/itachi/review-mediums/regressions.json').read_text())
assert index['cases'] == len(index['results']) == 103
assert len(index['fighters']) == 16
for case in index['results']:
    assert hashlib.sha256(Path(case['fixture']).read_bytes()).hexdigest() == case['hashes']['fixture']
    assert hashlib.sha256(gzip.decompress(Path(case['source']).read_bytes())).hexdigest() == case['hashes']['source']
def replay(case):
    folder = out / case['id']
    folder.mkdir()
    fixture = (root / case['fixture']).resolve()
    started = time.monotonic()
    execution = execute(godot, fixture, folder)
    native = folder / (fixture.stem + '.json')
    comparison = compare(root / case['source'], native) if execution['executed'] else None
    return {'id': case['id'], 'execution': execution, 'comparison': comparison,
            'seconds': time.monotonic() - started}
started = time.monotonic()
with ThreadPoolExecutor(max_workers=4) as pool:
    results = list(pool.map(replay, index['results']))
report = {'seconds': time.monotonic() - started, 'results': results}
(out / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
assert all(r['execution']['executed'] and r['comparison']['status'] == 'matched' for r in results)
assert sum(r['comparison']['source_states'] for r in results) == 65726
print('FLASH_REPLAY_OK cases=103 fighters=16 states=65726', report['seconds'])
PY
```

The 14-field fighter comparator does not compare every helper/audio/visual
field. Preserve existing source-build/instrumentation evidence links in the
index; add the already-retained helper or AI tape check when that boundary is
actually touched. `target_seen` describes fixture reach, not the comparator's
parity verdict. Do not drop diagnostic fixtures that intentionally miss a target.

Run the existing 36-check selection from the Itachi acceptance report, plus the
placement regression. It includes **all 15 rollback foundation checks**, so do
not run those twice. The code below uses explicit timeouts and retains raw logs;
it applies the existing narrow audio-shutdown allowance. Historical failures
are reported for signature review, not converted into passes.

```sh
python3 - <<'PY'
import json, os, subprocess, time
from pathlib import Path
out = Path(os.environ['BVN_CHECK_DIR']) / 'godot'
out.mkdir()
selected = json.loads(Path('evidence/characters/itachi/godot-checks.json').read_text())
names = [r['name'] for r in selected] + ['clip_placement_once_smoke']
known = {n + '_smoke' for n in ['ai_colors', 'ai_context', 'ai_host', 'title_menu_source', 'ai_hit_gate']}
results = []
for name in names:
    started = time.monotonic()
    command = [os.environ['BVN_GODOT'], '--headless', '--verbose', '--path', 'godot',
               '--log-file', str(out / (name + '.engine.log')), '--quit-after', '5000',
               '-s', 'res://tests/' + name + '.gd']
    try:
        run = subprocess.run(command, capture_output=True, text=True, timeout=600)
        log, code = run.stdout + run.stderr, run.returncode
    except subprocess.TimeoutExpired as exc:
        log = (exc.stdout or b'') + (exc.stderr or b'')
        log = log.decode(errors='replace') if isinstance(log, bytes) else log
        code = -1
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
        passed = passed and log.count('ROLLBACK_ROSTER_CASE_OK') == 16
    results.append({'name': name, 'passed': passed, 'exit': code,
                    'known_baseline_failure': name in known, 'seconds': time.monotonic() - started})
(out / 'report.json').write_text(json.dumps(results, indent=2))
for row in results:
    print(row)
assert all(r['passed'] or r['name'] in known for r in results)
print('Review known failure logs against baseline-godot-failures.json before accepting.')
PY
```

Compare retained failures with
`evidence/characters/itachi/baseline-godot-failures.json` and, if a signature
changes, the same command on `3423be31`. A timeout, missing resource or new parse
error is not the inherited assertion. The old roster summary says `fighters=11`;
the 16 `ROLLBACK_ROSTER_CASE_OK` records are the coverage check. For a rollback-only
iteration, the existing command is
`python3 tools/test_rollback_foundations.py --godot "$BVN_GODOT" --report "$BVN_CHECK_DIR/rollback.json"`;
its per-process timeout is 180 seconds, whereas a retained loaded-host roster
run took 403.6 seconds. Use the 600-second driver above for the final gate;
a timeout is an infrastructure result to investigate, never a gameplay pass.

Verify the protected function on every implementation candidate:

```sh
python3 - <<'PY'
import hashlib
from pathlib import Path
raw = Path('godot/fighter_runtime.gd').read_bytes()
start = raw.index(b'func _clear_interrupted_super_preparation()')
end = raw.index(b'\n\n', start) + 2
assert end - start == 544
assert hashlib.sha256(raw[start:end]).hexdigest() == 'd39b2b50d96d37ac717e1d1e8e9ccd711a67f6bbadcee6afc30593d6e0caa91e'
print('PROTECTED_FUNCTION_OK')
PY
```

For shared battle/dispatch changes also run:

```sh
python3 tools/test_shared_modes.py --godot "$BVN_GODOT"
```

Controller/goto/render changes already get player controller + visual smokes in
G. Direction-dash changes additionally require
`python3 tools/test_ghost_reference.py --godot "$BVN_GODOT"`.
Run this extra check only when that boundary changes. Use existing relevant `res://tests/*_smoke.gd`
checks for the bounded online/UI changes; no blanket browser matrix or fresh
Flash capture for mechanical leaf extraction. Generated output comparison C
must use each affected importer's existing CLI and identical pinned inputs,
with a temporary output directory, rather than modifying expected outputs.

### Runtime budget and evidence limits

These are historical planning ranges, **not fresh measurements**. Sources:
[Itachi checks](../evidence/characters/itachi/checks.json),
[review checks](../evidence/characters/itachi/review-mediums/checks.json), and their
per-case `godot-checks.json` / `regressions.json` files. Host contention matters.

| Check | Approximate time | Basis |
|---|---|---|
| D: verify + handoff + whitespace | Seconds to under 1 minute | Read-only local hashes/link checks; time the actual run. |
| Python discovery | Budget 1–3 minutes | Estimate; retained report records 301 tests / 299 pass / 2 skip, not isolated elapsed time. Preserve skip reasons and investigate count changes. |
| 103 saved Flash replays, four workers | Budget 5–15 minutes; serial can approach an hour under load | Retained review sums 3,371.6 subprocess seconds; parallel sum is not wall time. No Flash windows or capture-lock waits needed. |
| 36 Godot checks + placement, including rollback | Budget 8–15 minutes sequential | Earlier 36 checks sum 494.4 seconds; later roster alone 403.6, round 113.8, counter 15.5, Itachi rollback 38.2 seconds. |
| Whole G, warm imports | Roughly 15–35 minutes | Estimate from above; record actual elapsed time, command, commit and engine version. Cold import extra, not measured here. |

Run focused tests during editing and G once on the final implementation
candidate. Repeat only after relevant changes, failures or unresolved evidence.
Do not rerun the 15 rollback checks separately after the 36-check selection;
do not add exhaustive pairings, all cancel-window edges, 10,000 ticks or fresh
native captures without a concrete uncovered risk. If this small scope needs a
new design decision (state ownership, schema/protocol change, source behaviour
choice), stop and ask the user instead of expanding the refactor.
