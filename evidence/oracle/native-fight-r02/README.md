# M0-02 native physical menu facility recovery

This is live facility engineering, not a sampling rank or an accepted fight oracle.
`production_admitted=false`, `native_parity_proven=false`, M0-02 remains pending.
The branch starts at `0823f0ac70d954ad97d62a5e0a3aa475e9da8dd1`, preserving the
prior r01 work after coordinator restacking onto merged PR244/master
`59a71e27bf5e7b5dd71128d0749a8e49cfd73f0c`. The historical r01 dependency and
no-publication statements describe that earlier attempt, not this delivery.

## Recovered path and limitations

The user explicitly authorized ordinary Accessibility/System Events exact-PID
input and AX/CG observation. No CUA app-string selection is used here.
Public reports motivated testing, not a presumption of root cause:
[duplicate bundle identifiers](https://github.com/openai/codex/issues/41040),
[AnyDesk AX control](https://github.com/openai/codex/issues/58527), and
[Godot exact-PID input](https://github.com/openai/codex/issues/46471).

A hash-verified mounted player opens a unique temporary byte-identical copy of
all 75 locked assets while holding `/tmp/bvn-native-flash-capture.lock`. The
movie command, NSWorkspace executable, CG window owner/title and AX window title
are joined to the same PID. Non-unique bindings fail. Inputs use normal physical
Escape/S/J operations; no AS input, frame forcing, asset patch or runtime change.
Escape leaves the original startup fullscreen mode. Subsequent screenshots use
only the CG-derived movie rectangle after confirming that PID is frontmost.
The desktop is interactive, not isolated; user focus changes must fail the next
check, and a race after checking is not excluded.

The exploratory run visibly selected Vs Com, Ichigo, Naruto, Kon and Gaara,
then the map menu label `现世`, and reached ROUND 1. Screenshots are observations,
not numeric state: the arena picture is retained without guessing a map ID,
positions, stance, HP, energy, facing or native clock phase. The original log
appended 3,206 bytes, including load/control/start messages, but this is an
account-wide interval without a unique run marker. Other existing players were
not stopped. This is not exclusive trace attribution or a normalized fight trace.

Host AX/screen preflight succeeded under approved command execution. Sandbox-only
preflight false/empty inventory was not treated as TCC denial. No TCC grant,
trust acceptance, signature change, process injection or other-session restart
was performed. There was no approval rejection in these operations.

## Retained failures matter

- `exploration/input-ledger.json` corrects an exploratory harness limitation:
  its raw receipts contain a zero-input placeholder, but separate tool calls DID
  send inputs. Those raw fields must not be used as input counts. The supplemental
  ledger lists actual commands, not measured native consumption.
- Two original fullscreen S attempts did not visibly change Normal. Escape
  changed the same PID to a movie-titled AX window. No universal explanation for
  full-screen input failure is claimed.
- A busy-lock launch failed before creating a player. The lock inode was never
  removed or replaced.
- `run-01` exposed an AppleScript reference-resolution error: storing process
  candidates then telling `item 1` returned PID50810 instead of owned PID80268.
  One Escape operation was therefore sent through that wrong resolution. Its
  effect on the old non-windowed process is unknown; it was not killed. The
  current script uses the direct `first application process whose unix id ...`
  expression and verifies `unix id` before focus AND before input. The old script
  is retained in `run-01/tool-snapshot`, never reused.
- `run-01` also failed append validation across launch. The current collector
  retains prelaunch, postlaunch/preinput baseline and final raw bytes separately.
  It makes no append-only claim across a reset. The append proof covers only the
  retained input-baseline-to-final interval; no global log is truncated by us.
- `run-02` sent S during the startup logo, then entered Normal, not Vs Com. Its
  later fight screenshot and exit status are not successful fixed-case evidence.
  Tape v2 adds natural startup settling; observed screenshots, not delay alone,
  determine whether the target case was reached. Step filenames are intended
  stages, not certified screen classifications.

- `run-03` stopped after Escape because the frontmost PID changed from 90737 to 21273. No subsequent S/J input was sent; only the owned movie was cleaned. This is a real focus guard failure, not a TCC denial.

## Final live result

`run-04` executes tape v2 on owned PID 95146 in 93.36 seconds. All eight screenshots
were inspected: Normal -> Vs Com -> Ichigo -> Naruto -> Kon -> Gaara -> `现世`
menu label -> active Ichigo/Naruto fight. The final screenshot shows clock 55 and
an ongoing exchange, NOT the exact initial state. The postlaunch input baseline
is zero bytes; final log is 3,362 bytes with a verified append relationship. All
75 original/copied asset hashes pass after cleanup; no owned movie PID remains.
This and the earlier manual run establish a usable native input/capture path,
not deterministic fight repeatability. See `review.json` and `run-04/session.json`.

All capture runs return 1; unproved oracle acceptance is intentional. Six binding
regressions plus four r01 safety tests plus twelve shared capture tests pass (22).
`tools/verify.py`, `tools/check_handoff.py` and `git diff --check` return 0; full
outputs and measured durations are retained in `checks.json`. Contracts and all
historical sampling evidence are unchanged.

## Contract gaps and next work

This package does not satisfy M0-02 acceptance. Missing are an independently
observed exact post-menu fight state/clock phase, physical-input consumption ticks,
recorded random consumption (or valid seeded control), exclusive run-tagged trace
attribution, and a normalized contract-valid state/event trace with a repeatable
comparison. Wall-time key holds and screenshots cannot fill those fields. An
original uninstrumented log contains sparse diagnostics, not the required state.
The recorder deliberately returns exit1 even when all physical operations finish.
No speculative user-only permission action is needed or recommended.

The next engineering step is a separately built, source-audited observer that
records actual frame/input/random/state observations without replacing menu
navigation or forcing initial state; then pair it with this live facility and
validate replay/trace contracts independently. Existing sampling builders cannot
be relabeled as this oracle if they force frames or substitute user inputs.

SOURCE_FIRST boundary: menu controls are observed in
`scripts/main.json` at `DefineSprite_620/frame_1/PlaceObject2_619_28/CLIPACTIONRECORD onClipEvent(enterFrame).as`;
key defaults/startup fullscreen are in `frame_7/DoAction.as` and `frame_2/DoAction.as`.
Selection flow is in `DefineSprite_1477/frame_1/DoAction.as`; its `updateXY` emits
coordinate diagnostics, and the original match setup is in
`DefineSprite_1991/frame_1/DoAction.as`. No placement, exit-label, timing or combat
invariant is implemented or changed. Five-question gameplay evidence remains
incomplete, so there is no Godot/runtime work or gameplay acceptance here.

## Recheck

On the authorized Mac with the pinned mounted player and existing trace config:

```sh
PYTHONDONTWRITEBYTECODE=1 python3.11 evidence/oracle/native-fight-r02/capture_menu.py \
  --output /tmp/new-native-menu-run --allow-window-activation
# Expected exit 1: facility execution does not imply oracle acceptance.
PYTHONDONTWRITEBYTECODE=1 python3.11 -m unittest discover \
  -s evidence/oracle/native-fight-r02 -p 'test_*.py'
python3 tools/verify.py
python3 tools/check_handoff.py
```

The output directory must not exist. New tool dependencies resolve relative to
this repository; temporary movie paths and host identity paths are receipt-pinned.
`capture_menu.py` reuses the retained r01 hash/append helpers and the existing
capture tool's lock and exact command matcher, without editing either.
The replay tape is a facility-specific physical tape, not a contract `replay` or
`match-input`. Random/initial-state/normalized-trace fields remain null.
