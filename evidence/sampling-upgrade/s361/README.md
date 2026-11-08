# s361 — AFTER-s353 rank #8: Button2009 UI

Base: `5521e336` (s360 #238 squash). Branch: `feat/s361-button2009-ui`.
Authority: [unchanged AFTER-s353 rank #8](../next-fix-priority-after-s353.md).
Ranks 1–7 delivered; ranks 9+ planning only. No re-ranking.
`production_admitted=false`; `native_parity_proven=false`; M0-02 pending.
Zero mechanism/product obligations closed. Evidence-only delivery.

## Independent route and bounded result

Unlike s352's System Events name/bundle queries, this cut joins `/bin/ps`
executable paths to **NSWorkspace running applications and WindowServer owner
records**. [Read-only collector](capture_facility.py) and [Swift query](window_probe.swift)
are repo-relative; the player path and SHA-256 come from the locked
[s343 receipt](../s343/lookup-candidates.json). The initial sandbox `ps` failed
with `operation not permitted`; the retained collection ran with approved
escalation. No UI events are synthesized by these tools.

[Raw facility receipt](facility-result.json) independently distinguishes:

- PID **50810**: `/Volumes/Flash Player/Flash Player.app` executable.
- PID **68944**: the receipt-pinned installed executable; the current disk SHA-256
  matches `8d4c1f5934adae809b5f4ce4f6ca7c64d4260df46bb3eb9c41fe32be2ee905be`.
- Window **117370**: owner PID 68944, title pointing to this worktree's
  `game/main.swf`, bounds 600×428 at (0,33). NSWorkspace reports the app inactive.
  This record does not contain `kCGWindowIsOnscreen`.

This resolves the **current process-path/window-owner metadata association**;
it does not retrospectively reinterpret s352's duplicate PID rows. Current disk
bytes plus a process path are not a hash of the loaded executable image, and a
window title does not prove loaded movie identity. The mounted copy was not
selected, altered or hash-qualified. The query returned player windows only;
unrelated process/window rows were omitted from retained output.

The exact receipt application path was then passed to Computer Use. It returned
`Computer Use server error -10005: timeoutReached` after 10.9543 seconds. A binding
check returned `undefined` after 3.1263 seconds. [CUA receipt](cua-attempts.json)
records both calls. No screenshot or accessibility state was returned, no
permission prompt was observed, and no keyboard/mouse input was sent. The tool
may attempt background activation during selection; its outcome is unknown.
The timeout is a facility failure, **not a dispatch or no-dispatch observation**.
No application was killed or settings changed.

**Visible content and actual input-target control remain unproved.** Screen
capture/accessibility preflight booleans do not prove that control. No launch
request was issued by this cut, no original-menu Enter/release or observed
no-dispatch controls ran, and there are no new native behavior captures.
Compilation/opcode projection and observer-off/on qualification remain deferred
behind this rank's window/input prerequisite. No compiler limitation is claimed.
Historical candidate patches and s263 events are retained validation only.

## Reproduction and gates

Portable recheck (standard Python library, no installed player or macOS needed):

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 evidence/sampling-upgrade/s361/diagnose.py --output /tmp/s361.json
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s361 -p 'test_*.py'
python3 tools/verify.py
python3 tools/check_handoff.py
```

Base diagnosis and `--require-process-window-association` exit **0**. The four
flags `--require-native-ui`, `--require-opcode-qualification`,
`--require-thin-coverage`, `--require-full-as` each exit **1**, as does their
combined gate. Both admission flags remain false for every report.
[Gate receipts](gates.json) and [project checks](project-checks.json) include
commands, expected/actual exits and measured subprocess duration. Tests reject
wrong binary hashes, process mismatches, wrong owners, duplicate applications,
query failure and invented visibility/input/no-dispatch claims. The complete
locked s352 diagnosis and unchanged retained Button2009 tests are replayed.

For a fresh macOS observation, invoke the collector from a separate checkout or
retain its output separately; it writes `facility-result.json` beside itself.
Do not overwrite this historical package with new observations. Host tool hashes
are in [host-tools.json](host-tools.json). The Swift module cache stays under
`/tmp`, outside formal source. The collector is read-only with respect to apps;
UI interaction uses Computer Use only. New observations require fresh analysis,
not flipping false flags in this diagnosis.

[Input pins](input-sha256.json) cover complete s352 files, authority, player
receipt and new route receipts. [Artifact pins](artifact-sha256.json) cover all
package files except that index. [Scope audit](scope-audit.json) checks only new
s361 and minimal tracking updates, with zero s254–s360, authority, source,
runtime, contract or shared-tool diffs. [Manifest audit](manifest-audit.json)
records the reviewed tracking hashes. [Timing](session-timing.json) records
measured elapsed/check costs, not person-days. No contract/runtime change calls
for Godot or contract acceptance testing here.

## Source-first boundary and next discriminator

1. Retained s276 preparation through s352 identifies Sprite2010 stops at frames
   1/10; no new per-frame behavior is inferred.
2. Root56 places menu depth157; menu10 newly places Button2009 depth5. Static
   placement is not measured continuous native lifetime.
3. Both original handlers explicitly `gotoAndStop(1)`; no forced frames are used.
4. Tests protect source/receipt invariants and evidence boundaries, not presumed
   observer neutrality or listener order.
5. Same-input original-menu execution remains absent. No runtime change or
   mechanism completion follows.

Next obtain visible state and an actual input binding for the identified
receipt-path process, qualify complete compiled opcode/control-flow projection
and observer-off/on with live placement/timeline bracketing, then execute
original-menu Enter/release and observed no-dispatch controls. No forced frames,
AS calls as input, listener-order assumption, combat tape change or proof from
launch success/timeout. Delivery closes only this evidence cut. Draft PR only;
no ready-for-review, merge or deployment.

Validation: **118 tests pass**; verify.py, check_handoff.py and whitespace checks
exit 0. Expected proof failures are retained, not suppressed.
