# M0-02 source-site observer preparation and interrupted native attempt

Branch base: merged PR245/master `f30ed7c0c392356d772f954ee5bccc1ce2f0a6c6`.
This is observer engineering for M0-02, not a sampling rank. M0-02 remains pending;
`production_admitted=false`, `native_parity_proven=false`. No accepted initial-state,
input-consumption, random replay, exclusive state trace or deterministic repeat is
claimed. The user requested offline checks first and deferred further live capture.

## Actual attempt and current readiness

`run-01` launched a separately built observer copy using the pinned Flash debugger,
existing capture lock and r02's exact movie-PID AX/CG/System Events driver. PID 30565
returned the correct temporary movie title; Normal was visibly captured. After S,
CG/NSWorkspace reported frontmost PID 21273 rather than the movie PID, so the guard
stopped before further input. Cleanup left no owned movie PID. This is focus loss,
not a TCC denial or an irreducible user-permission failure.

The retained raw log contains exactly one new tagged event:
`M002|m002-observer-20261108-r03a|1|273|0|before-game-callback|boot|...`.
It proves that observer boot trace executed in this attempted capture; it does not
prove the global forwarding hooks worked. No key/random/state event was observed.
The historical attempted source and builder are in `run-01/tool-snapshot/`.
Their global hook assignments are **not** the current design. Their failure cause
has not been established; source inspection did not find root observer deletion.

Current `observer.as` and `build_observer.py` use explicit lexical source sites
rather than replacing native API properties. `/tmp/bvn-m0-observer-build-02` was
compiled but **not launched**, respecting the user's request to defer capture.
The full build identity is retained in `build.json`; the temporary asset directory
is not committed. This is a prepared next live cut, not proof-gap closure.

## SOURCE_FIRST boundary and exact scope

The original source is `scripts/main.json`, backed by locked `game/main.swf`.

- `frame_1/DoAction.as`: append namespaced observer functions and unique boot tag.
- `DefineSprite_1900/frame_1/DoAction.as`: replace only the two original
  `Math.random()` call expressions in `loadSound` with forwarding functions that
  call the original API once, log the actual result and return it unchanged.
  Each result carries a distinct `loadSound-1/2` site label. These are music draws,
  not the complete AI/random consumer stream.
- `DefineSprite_1991/frame_1/DoAction.as`: instrument the existing camera/wall
  controller's `onEnterFrame` entry/exit, and the source's `_root.ready.play()`
  boundary. Its original frame-control calls remain. Replace only the two
  `renderSkip` native key queries with forwarding calls, with source-site labels.
  These are intro queries, not proof of fighter decision/input consumption.

No new display object is placed. The compiled tag audit checks all recursively
nested payloads and requires exactly these three changed DoAction tags:
`root/547:12`, `root/2106:39/sprite1900/1:12`,
`root/2198:39/sprite1991/1:12`. Every other tag payload, timeline header,
placement/MOVE/removal and all 74 non-main assets remain byte-identical. No goto,
stop, pause, actor field, input result or random result is manufactured. Original
source exit paths and scheduling calls are preserved; added tracing can still
perturb timing, and observer noninterference is NOT proved by byte auditing.

Actor checkpoints record container x/y/xscale and body frame/hp/ql/action/beida/
kcplayed. Game checkpoints record root frame, rounds, pause flags, loaded flag,
mode, stage, roster and assists. Numeric values use the retained binary-significand
encoder, not shortened decimal formatting. The new local ordinal belongs only to
this existing callback. The `getTimer` value is observed wall-clock time, not an
ExecutionProfile global tick. Unknown values remain undefined. The first observed
unpaused callback is not asserted to be the exact gameplay initial-state boundary.
Original same-input evidence is r02; a same-input instrumented comparison remains
absent, so SOURCE_FIRST's complete behavior gate is not satisfied.

## Admission and provenance checks

`capture_observer.py` keeps source hashes and instrumented output hashes separate,
checks the pinned player/config, copies the built assets into a unique temporary
movie path, retains AX/CG before/after each physical operation, and checks returned
PID/focus. It refuses a preexisting run tag and never clears the global flashlog.
Prelaunch, postlaunch/preinput and final raw logs are distinct: a startup log reset
must not be misrepresented as append-only history. Cleanup targets only the exact
unique temporary movie command.

`analyze.py` refuses malformed/foreign tags, noncontiguous or duplicated sequence
numbers, missing unique boot, non-append input intervals, mismatched selected/raw
logs, wrong returned input PID, missing asset/cleanup checks, and absent actual
state/key/random observations. Failed or missing observations are not admitted.
It stores random **observations**, not a replay tape. The tag plus unique build/PID
receipts supports scoped attribution; it is not OS-level attestation of each write.
Full exclusive state-trace admission remains unproved until an actual run passes
all checks and its provenance is independently reviewed.

## Reproduction after the user restores a capture window

```sh
PYTHONDONTWRITEBYTECODE=1 python3.11 evidence/oracle/native-fight-r03/build_observer.py \
  --ffdec /tmp/bvn-m0-observer-tools/ffdec/ffdec.jar \
  --output /tmp/new-observer-build --run-id m002-new-unique-run-token
PYTHONDONTWRITEBYTECODE=1 python3.11 evidence/oracle/native-fight-r03/capture_observer.py \
  --build /tmp/new-observer-build --output /tmp/new-observer-capture \
  --allow-window-activation
# Capture returns 1: no complete M0-02 oracle is certified.
python3.11 evidence/oracle/native-fight-r03/analyze.py /tmp/new-observer-capture
python3.11 evidence/oracle/native-fight-r03/analyze.py /tmp/new-observer-capture --require-oracle
# Require-oracle remains 1 until full independent acceptance exists.
```

JPEXS 26.2.1 was obtained from its official GitHub release. Its jar SHA is
`090ab695053ad94cba6408574c7d7eea20ec60b6ae789ee6056a23f45106762f`, matching the
retained s168 compiler identity; the older reference-environment jar pin is not
silently substituted. The player SHA remains
`8d4c1f5934adae809b5f4ce4f6ca7c64d4260df46bb3eb9c41fe32be2ee905be`.
The current build uses three source sites; the attempted earlier build used two.
No historical evidence, locked assets, runtime, contracts or validators changed.

## Offline verification and handoff

27 tests pass: five new observer/parser/source guards, six retained PID/window
binding tests, four retained boot safety tests and twelve shared capture tests.
`verify.py`, `check_handoff.py` and diff checks pass. The actual incomplete run's
`analyze.py --require-oracle` returns 1 and is not admitted. Outputs are retained
in `checks.json`. The current built bytes were independently rechecked against
all three allowed tag paths and the output hash after the final guard revision.
No further native capture was attempted after the user requested offline work.
The next live step requires a foreground capture interval, not a new permission
grant. Focus loss is a reversible facility blocker, not proved irreducible.
Last user-provided UI budget reading was approximately 48% weekly, floor 20%; no
credential/session files or unofficial budget APIs were read.

Compiler source: [official JPEXS 26.2.1 release](https://github.com/jindrapetrik/jpexs-decompiler/releases/tag/version26.2.1).

Raw instrumentation diffs and compiler stderr are stored as `.gz` without changing
their decompressed bytes. `instrumentation_sha256` hashes the decompressed diff.
The first staged diff check rejected CRLF/raw-log whitespace; compression retains
the original receipt while allowing the final staged whitespace check.
