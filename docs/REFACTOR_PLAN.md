# Behaviour-preserving refactor survey

Survey date: 2026-10-15. Baseline: `origin/master` at `3423be31`, branch
`refactor/survey`. This PR changes documentation only. All proposed PRs below
are **not started**; this survey does not close implementation milestones or
change `plan/tasks.json` acceptance status.

## Non-negotiable boundaries

Read [SOURCE_FIRST](SOURCE_FIRST.md) first, then [HIT_RECEIVE_SOP](HIT_RECEIVE_SOP.md),
[VALIDATION](VALIDATION.md) and the current [STATUS](STATUS.md). Before a runtime
extraction, attach the five source-first answers for the affected methods:
all frame scripts (including empty frames), PlaceObject/MOVE lifetimes, exits,
source invariants, and the corresponding original-input recordings. A mechanical
move is not an exemption. If the evidence cannot answer them, defer that PR.
For settlement/presentation work retain SOP A–E; no new character-specific rules.

- No gameplay changes, new mechanisms, numeric cleanup, scheduling changes,
  oracle updates, tolerance changes, new default values or content expansion.
- Keep `_clear_interrupted_super_preparation` byte-for-byte unchanged in
  `fighter_runtime.gd`, and preserve its call position and conditions. Its existing
  anti-deadlock deviation from Flash is intentional, not a refactoring target.
- Every implementation PR runs the all-character saved Flash replay, Python,
  Godot and rollback gate below. Only the existing five failures may remain:
  `ai_colors`, `ai_context`, `ai_host`, `title_menu_source`, `ai_hit_gate`.
  Match failure signatures to the base; their names are not a blanket error waiver.
- Keep `game/`, `scripts/`, inputs, RNG/clock tapes and historical evidence intact.
  Rebuild into temporary directories. Compare generated data before replacing
  anything; a pure compiler extraction should produce identical bytes.
- Retain JSON field order where it affects emission, list/enumeration order,
  null/undefined distinctions, integer/float types and full numeric precision.
- Each row below is one independently mergeable/revertible PR. No row requires
  another row to land first. Preserve existing entry points with forwarding
  wrappers where callers exist; do not combine extraction with API redesign.
  Stop after the named slice, rather than gradually moving the entire class.

“All-character” here means all **16 implemented fighters**, not the 35 locked
fighter SWFs or every form. The retained gate has 103 cases / 65,726 fighter
states / 14 exact fields. It does not establish full visual/audio/browser/AI
acceptance. The later 35 Itachi cases remain additional source evidence, not
permission to replace the 103-case baseline with a smaller selection.

## Survey findings and ownership

Counts are physical lines at the baseline, not complexity scores. Generated
GDScript is excluded from handwritten-code size rankings.

| Area | Concrete finding | Boundary to preserve |
|---|---|---|
| Fighter | `godot/fighter_runtime.gd`: 2,380 lines; mixes source coordinates, frame dispatch, command dispatch, contacts, projectile locals, effects and diagnostics. `enter_frame` is 114 lines. | Fighter owns mutable simulation fields; `TimelinePreview` remains its current base. Do not introduce a new stateful component graph in a mechanical extraction. |
| Scheduling | `godot/main.gd`: 1,833 lines; `_advance_fight` spans 195 lines and coordinates intro, helpers, fighters, callbacks and root observations. | Phase order is source evidence, not a stylistic pipeline preference. Keep this orchestration visible. |
| Display | `godot/timeline_preview.gd`: 1,388 lines; `_render_placement` spans 121 lines; render transforms and source bounds coexist. | Render vectors are float32 projections; source scalar coordinates and source bounds are not interchangeable. |
| Rollback | `godot/battle_checkpoint.gd`: 643 lines; `_encode` spans 152 lines. Reflection captures script variables and shared container identity. | Main fields are explicitly classified; other script owners are traversed. A new helper object can silently change graph shape, callable binding and lifetime. |
| Online | `godot/online_lobby.gd`: 4,553 lines; `online_match.gd`: 2,378; `online_room_client.gd`: 1,104. UI construction, async room operations and session ownership share files. | Keep generation/epoch guards, immutable timer envelopes and confirmation barriers with their existing owners. |
| Compiler | `tools/importer/build_combat_model.py`: 2,152 lines; `build_model` is 594 lines; `_merge_root_atm_windows` 180 and `parse_projectile_motion` 173. | Separate source parsing from assembly, retaining source paths, hashes, statement position and fail-closed behaviour. |
| Probe builders | `build_ai_reference.py`: 720 lines / 500-line `build`; `build_ai_reference_vscom_tmp.py`: 658 / 460. Overlapping instrumentation helpers and launch workflows. | Diagnostic interventions and clean parity captures must remain distinguishable. The `_tmp` file is loaded by `build_ai_reference_vscom_natural_tmp.py`; it is not proven dead. |
| Harnesses | 53 Python test files; `test_source_inventory.py` is 1,225 lines, spanning SWF inspection through combat compilation. `godot/tests/combat_smoke.gd` is 1,784 lines. | Tests assert source behaviour. Splitting must preserve test IDs/counts or document exact ID mapping, setup isolation and every assertion. |
| Check policy | `run_godot_checked.py`, `test_move_cases.py`, `test_source_parity_suite.py` and `test_rollback_foundations.py` each inspect process output differently. | Exit zero alone is not success; markers, trace completeness and script errors are separate. Audio-only shutdown exceptions must remain narrow. |
| Evidence/docs | STATUS is 874 lines and tasks.json 1,105; dated narrative, partial acceptance, fixtures and historical runs are interleaved. OPERATIONS still describes earlier slice limitations. | Historical evidence is immutable; current navigation should link it, not rewrite history or turn partial into complete. |
| Repository tooling | `justfile` is a command index, Python uses `requirements-dev.txt`; `services/matchmaking` is a separate npm package with its own lockfile. | No repository-wide package migration is justified. Worker protocol/catalogs and Godot compatibility manifests cross the package boundary. |

The runtime already has `source_coordinate.gd`, `source_callback_registry.gd`,
`rollback_lifetime.gd`, `rollback_presentation.gd` and dedicated source services.
Prefer those boundaries to a new generic event bus, ECS, interpreter or global
utility module. `snapshot()` and `_diagnostic_state()` intentionally expose
*different* fields/coordinate representations; their resemblance is not proof
that they should share one schema.

## Prioritized PR queue

Verification abbreviations: **D** = integrity/docs checks; **G** = complete
implementation gate in the next section, once per final candidate; **C** =
rebuild affected compiler outputs outside the tree and byte-compare against base
(including source hashes and list order). Focused checks listed below supplement
G only when not already included. Risk is the risk of accidentally changing
behaviour, not permission to do so.

| Priority / PR | Scope and bounded change | Rationale | Risk and verification |
|---|---|---|---|
| P0 / R01: evidence navigation | New `docs/REGRESSION_INDEX.md`, links in `docs/VALIDATION.md` and `docs/OPERATIONS.md` only. Index the 103-case report, preservation record, five baseline failures and current commands. | Current reproduction requires piecing together character reviews; an older 14-field archive is not necessarily the current 16-fighter suite. | Low; D, verify every indexed fixture/hash/path; no replay for this documentation-only PR. Keep historical reports and task states unchanged. |
| P0 / R02: one log-classification seam | `tools/test_move_cases.py`, `tools/test_source_parity_suite.py`, new `tools/godot_result.py`, relevant `tools/tests` only. Extract their common exit/script-error/marker predicate with explicit per-caller options. | Prevent drift without replacing every runner at once. Do not migrate `run_godot_checked.py` or rollback policy in this PR. | Medium; G plus small captured-log cases for missing marker, exit zero + SCRIPT ERROR, timeout and clean run. Prove old/new classifications equal; changing exception policy is out of scope. |
| P1 / R03: projectile parser extraction | `tools/importer/build_combat_model.py`, new `combat_projectile_parser.py`; move `projectile_local_scope`, `parse_projectile_motion`, `parse_projectile_initialization` and their exclusive constants. Keep imported names available from old module. | Isolates a 173-line parser and its lexical-scope rules from model assembly. | Medium; G+C for all implemented fighters, existing projectile/contact/compiler tests. Preserve regex order and unknown-input rejection; do not replace parsing strategy. |
| P1 / R04: bounded model assembly | `tools/importer/build_combat_model.py` only. Extract the existing combo-transition assembly block from `build_model` into a pure helper with explicit ranges/scripts/frame inputs. | Reduces the 594-line assembler by one coherent block without a new intermediate schema. | Medium; G+C, existing combo lifetime and command catalog assertions. Preserve first-match selection, errors and provenance bytes. |
| P1 / R05: move one Python test class | `tools/tests/test_source_inventory.py`, new `test_timeline_geometry.py`; move only `TimelineGeometryTests` and its required fixtures/imports. | Separate XML/display-list tests from combat-model tests without duplicating shared fixture construction. | Low; G, compare discovered test count and old→new IDs; no new behavioural assertions. Do not also split the 266-line combat test. |
| P1 / R06: pure fighter geometry helper | `godot/fighter_runtime.gd`, new `source_sweep_geometry.gd`; move only `_horizontal_sweep_fraction`, retaining the method wrapper. | A small stateless mathematical boundary avoids relocating projectile or fighter state. | Medium; G; existing projectile contact and mirrored/air contact checks. Preserve comparison order, edge inclusion and all float operations exactly. No clamp/epsilon changes. |
| P1 / R07: proven unused method removal | `godot/fighter_runtime.gd` only: candidate `_frame_in` (final five lines). | Repository GDScript/Python search currently finds the definition only. | Low only after whole-tree textual/string-call, scene/resource, inherited and generated-call audit; G. If a dynamic caller is found, drop the PR. Do not remove `_physics_process: pass`: it overrides inherited processing. |
| P1 / R08: matrix construction boundary | `godot/timeline_preview.gd`, new `source_matrix_transform.gd`; extract `_matrix_transform` only, keeping its forwarding method. | Makes the Flash/JPEXS column mapping reviewable apart from rendering. | Medium; G plus existing rotated-hitbox/bitmap-mask checks. Keep `rotateSkew0/1`, twip division and `basis_scale` exactly; no unification with source scalar arithmetic. |
| P2 / R09: hit-effect lookup slice | `godot/fighter_runtime.gd`, new `fighter_hit_effect_lookup.gd`; move only strength normalization and table lookup helpers, accepting tables explicitly and retaining wrappers. | Separates pure lookup from settlement and signal emission. | Medium; G, `hit_settlement_frame_smoke` and combat smoke; SOP A–E source links. No move of `receive_attack`, `_settle_source_hit`, `_clear_interrupted_super_preparation` or effect emission. |
| P2 / R10: one scheduler phase extraction | `godot/main.gd` only. Extract the contiguous diagnostic-tick assignment loops in `_advance_fight` into a same-owner method, called at exactly the current position. | Starts reducing the large function without moving scheduling state or changing callback phases. | Medium; G plus `tools/test_shared_modes.py`; compare diagnostic tick/slot records on an existing fixture. No reordering of helper/fighter advance or root observation. |
| P2 / R11: checkpoint policy constants | `godot/battle_checkpoint.gd`, new `battle_checkpoint_fields.gd`; move only immutable/external/Main field-name arrays, keep aliases in checkpoint. | Makes ownership policy inspectable without rewriting graph serialization. | High; G and existing checkpoint invalid-state/COW/identity assertions. Compare field classifications and snapshot digests on base/head; no new exclusions, reordering, snapshot version or lifetime changes. |
| P2 / R12: one Godot smoke group | `godot/tests/combat_smoke.gd`, new test-support script; extract only a contiguous hit-effect assertion group, keeping original entry point, invocation order and completion marker. | Reduces the large harness without creating another parallel battle implementation. | Medium; G, compare assertion/group execution counts and source-linked expected values. Keep scene cleanup and RNG/timer setup at the same boundaries. |
| P2 / R13: probe pure helper deduplication | `tools/probes/build_ai_reference.py`, `build_ai_reference_vscom_tmp.py`, new probe helper module; share only byte-identical hashing/AS2 JSON-string quoting helpers confirmed by diff. | Removes low-risk duplication without merging two 500-line instrumentation workflows. | Low–medium; G plus existing probe-builder/capture provenance tests; compare generated instrumentation text/bytes for each existing mode. Leave capture ordering and activation behaviour untouched. |
| P2 / R14: capture process lookup reuse | `tools/probes/freeze_capture_native.py`, `capture_native_player.py`; share only exact movie/binary PID matching after confirming equivalent argument handling. | Two capture flows maintain overlapping process-discovery logic. | Medium; G plus existing capture serialization tests and mocked process-list cases. Keep account-wide lock held across launch/capture/snapshot/owned-process cleanup; no live Flash batch just to test this helper. |
| P2 / R15: lobby widget factories | `godot/online_lobby.gd`, new `online_lobby_widgets.gd`; move only `_label`, `_line_edit`, `_row`, `_button` factories, retaining wrappers. | Starts shrinking the largest runtime file at a presentation-only boundary. | Medium; G plus existing lobby UI smoke and one local UI inspection. Preserve signal connections, focus, names and sizes; do not move room/startup state or async callbacks. |
| P3 / R16: online validation helpers | `godot/online_match.gd`, new `online_match_values.gd`; extract only `_wire_integer` and `_is_digest` with wrappers. | Separates leaf validation from transport/recovery orchestration. | Medium; G plus existing online protocol/review regressions. Preserve accepted wire types/ranges and failure behaviour; no protocol version or normalization changes. |
| P3 / R17: Worker response projection | `services/matchmaking/src/room.ts`, one helper module, existing `test/server.test.mjs`; extract only closed-room state projection from `closedMarker`, leaving persistence/alarm calls in Room. | Room combines HTTP, socket and alarm lifecycle; a pure projection is safer than extracting `fetch` wholesale. | Medium; G plus `npm --prefix services/matchmaking test` and `npm --prefix services/matchmaking run format:check`. Preserve state shape, timestamps and socket ownership. No deployment, dependency or catalog changes. |

Do not collapse R03/R04 into a compiler rewrite, R06/R09 into a Fighter component
migration, or R15/R16 into an online state-machine redesign. Those would no
longer be the small review units described here. If a named helper is not pure
under closer source audit, keep it with its owner and defer that row.

## Determinism and rollback hazards to check in each PR

- **Ordering:** `advance_ai_timeline`, `_apply_ai_source_frame`, source callback
  registration and `_advance_fight` interleave retained children, nested gotos
  and observer snapshots. Sorting dictionaries or draining a queue earlier is a
  gameplay change. Preserve call-site order, including function expansion within
  its caller's statement order.
- **Instances:** aliases, `_hit_instances`, `_clip_placements_applied`,
  `_placement_owned` and invocation serials distinguish new placement, MOVE,
  failed lookup and repeated cast. Missing-receiver writes are consumed once.
  Reuse [placement evidence](../evidence/characters/itachi/review-mediums/README.md)
  and `clip_placement_once_smoke.gd`; do not introduce unsnapshotted caches.
- **Numbers:** `_source_x/_source_y` retain source precision while `position` is
  a display projection. Keep assignment-time twip truncation separate from
  projection recovery, and trace full precision. Do not “simplify” both paths.
- **Ownership:** consult [STATE_AUDIT](online-multiplayer/STATE_AUDIT.md).
  Checkpoint traversal records aliases, typed containers, script paths and named
  Callables. Static helpers avoid new state owners; moving fields or callbacks
  requires explicit save/restore, same-state digest and late-input proof.
- **Timers/RNG:** preserve shared tape cursors, consumer order, explicit clock,
  immutable external journal and callback phase. Never replace wall-clock
  callbacks with a guessed tick interval or read live time during replay.
- **Presentation:** retain `rollback_lifetime` retirement and
  `rollback_presentation` replay suppression. Materializing a restored display
  must not replay sounds, advance child clocks or execute placement callbacks.
- **Online:** preserve epoch/generation checks after awaits, confirmation before
  result commit, event delivery and cleanup on disconnect. Cosmetic extraction
  must not change who owns cancellation or late replies.

No dead-code deletion is justified merely by “legacy”, “AI” or `_tmp` naming.
The fallback command/motion paths are exercised by isolated tests; production
reachability and test/probe reachability must both be checked. Bulk deleting
historical evidence, moving generated files, normalizing every JSON document,
changing inheritance, and optimizing checkpoint encoding are deferred.
Performance work needs profiling and a baseline, and is not part of this queue.

## Exact regression commands

Run from the repository root with Python 3.10+ (record its actual version) and
Godot **4.7.2-stable**. Set `BVN_GODOT` to the executable's absolute path. Import
resources once per fresh worktree. The survey itself does not run gameplay tests:
it changes no executable code; commands below are the later implementation gate.

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
before updating its hash; never regenerate input hashes to hide changes. Contract
changes are not planned; if one becomes necessary, separate it and also run
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
No dash change is proposed. Use existing relevant `res://tests/*_smoke.gd`
checks for the bounded online/UI changes; no blanket browser matrix or fresh
Flash capture for mechanical leaf extraction. Generated output comparison C
must use each affected importer's existing CLI and identical pinned inputs,
with a temporary output directory, rather than modifying expected outputs.

### Runtime budget and evidence limits

These are planning ranges, **not measurements made by this docs PR**. Sources:
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

## Survey validation record

On this docs-only branch, `tools/verify.py`, `tools/check_handoff.py` and
`git diff --check` passed. All 103 retained fixture and decompressed original
trace hashes were checked against the review index. Embedded Python command
blocks were syntax-checked and smoke completion markers checked against source.
The protected function still has 544 bytes and the recorded SHA-256 above.
No runtime, compiler, test, generated content, source input or manifest was
modified. This new document is not an existing manifest-covered file. Gameplay
suites were deliberately not executed for a documentation-only survey; runtime
budgets above remain historical/estimated, not new parity claims.
