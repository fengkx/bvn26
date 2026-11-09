# M0-02 live validation of the prepared r03b source-site observer

**The live attempt completed; the oracle gate refused acceptance.** M0-02 remains
pending. `production_admitted=false`, `native_parity_proven=false`,
`oracle_accepted=false`. This package validates observations from the prepared
observer; it does not close M0-02 and is not a sampling rank.

Base/master was verified clean and current at
`baf7e202106b1d0bf1f2ffe3da4dc199a28a59a5` (merged PR246).
Branch: `feat/m0-02-oracle-r03-live`. The user explicitly authorized the foreground
interval. The existing r03 builder, observer, capture driver and analyzer were
used unchanged. No CUA app-string/bundle binding was used.

## Live result

The capture took **85.25 seconds**, using unique run tag
`m002-live-20261109-r04-7bc19e` and receipt-matched movie PID **99050**.
Nine physical operations completed with the same returned PID/frontmost state:
Escape, S, six menu J presses, then one fight J press. AX/CG receipts and screenshots
retain the path through Normal -> Vs Com -> Ichigo/Naruto -> Kon/Gaara -> the
`现世` map menu -> active fight. The final J was physically posted; its gameplay
consumption/effect is not proved by screenshots or the input command return.

The initial pre-focus probe reported frontmost PID 87154. The driver activated
owned PID 99050 before Escape; all 17 subsequent before/after probes reported
PID 99050, and every physical operation returned that PID with frontmost=true.
There was **no observed focus-loss or TCC blocker**. The capture lock was held,
all final source/copied-asset hash checks passed, and cleanup left no matching
temporary movie PID. Other player processes were not terminated. No trust prompt
was accepted, permission setting changed, signature modified or deployment made.

The unchanged strict analyzer ran both normally and with `--require-oracle`;
**both exited 1** with `State/input/random live observations missing`.
`analysis-gates.json` retains command/output/error receipts. The more specific
reason is zero positive key-return observations: the observer's two instrumented
key sites belong to intro `renderSkip`, while the last physical J was sent during
combat after that path stopped querying. No gate was weakened to admit this run.

## What was actually observed

The retained raw log yields **4,615** contiguous run-tagged records:

| Observation | Count / result |
|---|---|
| Unique boot marker | 1 |
| Local callback entry/exit pairs | 722, contiguous ordinals 1–722 |
| Game-state records | 1,444 |
| Actor-state records | 2,888 |
| Intro key-return queries | 280; all false; ordinals 199–338 |
| Music random-return records | 1, at `loadSound-1` |
| Source ready-play boundary | 1, local ordinal 338 |
| Bounded end marker | Absent; cleanup occurred before the 900-callback horizon |

The random return was `0.6610792092978954`, stored first as the retained exact
binary-significand representation. It was an observed native result, not a seeded
or substituted value. `loadSound-2` was not observed. This is only the scoped
music-call stream, not a complete random tape or proof about all AI consumers.

The first callback-entry checkpoint observed with both pause flags false is
sequence 3074, local ordinal 466, `getTimer=71962 ms`, root frame 56, round 1, mode 2,
`p2loaded=true`, map `现世`, roster `一护/鸣人`, assists `魂/我爱罗`.
The two corresponding actor records are:

| Field | p1 | p2 |
|---|---:|---:|
| Container x | 374.1 | 637.1 |
| Container y | -25 | -25 |
| Container xscale | 100 | -100 |
| Body frame | 4 | 20 |
| hp | 1000 | 1000 |
| ql | 0 | 0 |
| action / beida | 0 / 0 | 0 / 0 |
| kcplayed | 2 | 2 |

These are **first observed unpaused checkpoint values**, not a certified exact
fight initial state or stance. Earlier records retain undefined fields during
loading; they are not filled with guessed values. Callback ordinal and wall-clock
`getTimer` are not a proved global simulation tick or complete scheduling phase.

`describe_capture.py` derives `observations.json` as a **partial description, not
an admission gate**. It reuses the strict parser, checks raw/tag selection,
sequence and callback pairing, build/receipt identity, append interval, input PID,
cleanup and exact changed tags. It does not replace or relax `r03/analyze.py`.

## Build and provenance

The r03b design was rebuilt into `/tmp/bvn-m0-observer-live-r04` with the new tag;
then copied into the receipt-pinned unique temporary movie directory. The pinned
player executable SHA remains
`8d4c1f5934adae809b5f4ce4f6ca7c64d4260df46bb3eb9c41fe32be2ee905be`.
The locked source main SHA remains
`707fac0ec6bb2af1a3d18dc308dd403cb556a0988144b0f6f10555382287f92d`.
JPEXS SHA is `090ab695053ad94cba6408574c7d7eea20ec60b6ae789ee6056a23f45106762f`.
The session retains OS/architecture, translated-command check, trace config,
physical tape/tool hashes, all source hashes and all output hashes.

Recursive byte auditing before and after capture verifies exactly three changed
DoAction payloads: `root/547:12`, `root/2106:39/sprite1900/1:12`, and
`root/2198:39/sprite1991/1:12`. All other tag payloads/timeline headers and the
74 non-main assets are unchanged. The raw instrumentation diff is gzip-retained;
its decompressed hash equals `build.json.instrumentation_sha256`.

The run tag was absent before launch. The account-wide log reset across startup
(281 bytes prelaunch -> 127 bytes postlaunch/preinput), which is recorded rather
than hidden. The input interval itself is append-only: 127 -> 1,150,356 bytes,
a delta of 1,150,229 bytes. `tagged.log` is an exact line selection from the retained
final raw log. The inherited session `flashlog.attribution` text describes the
unattributed account-wide interval; the separate tagged selection is explicitly
checked here. Fresh tag + unique build/movie PID + continuous sequence provides
scoped provenance, not independent per-write OS PID attestation or proof that a
complete exclusive state trace has been obtained.

## Remaining M0-02 gaps and SOURCE_FIRST limits

- Exact per-tick fight initial state and global clock/phase ordering remain unproved.
- Fight-path `Key.isDown` consumption and downstream action decisions are not
  instrumented. All observed intro queries are false; no positive-input gate passes.
- Music random sampling is partial. Full random-consumer provenance, a pinned
  replay tape and consumption verification remain absent.
- No complete exclusive contract-valid state trace is admitted. This run is a
  captured observer prefix, not a normalized replay/trace contract artifact.
- Deterministic repeat and the SOURCE_FIRST same-input instrumented/uninstrumented
  comparison remain unperformed. Timing noninterference is not established.

The underlying source-site map and non-modification boundary remain as documented
in [r03](../native-fight-r03/README.md). This run only observes those sites; no
forced frames, AS-as-input, global native API hijack, original asset mutation,
validator change or gameplay implementation is introduced.

## Checks and reproduction

27 retained facility/observer tests pass (`tests.json`). The current build's exact
three-tag audit also passes. Project verify/handoff and final scope/hash receipts
are retained with this package. Raw capture exit 1 is expected, as is oracle exit 1.

```sh
PYTHONDONTWRITEBYTECODE=1 python3.11 evidence/oracle/native-fight-r03/analyze.py \
  evidence/oracle/native-fight-r04/run-01
PYTHONDONTWRITEBYTECODE=1 python3.11 evidence/oracle/native-fight-r03/analyze.py \
  evidence/oracle/native-fight-r04/run-01 --require-oracle
# Both exit 1; retain the refusal.
PYTHONDONTWRITEBYTECODE=1 python3.11 evidence/oracle/native-fight-r04/describe_capture.py
# Description only; all three admission flags remain false.
```

Rebuilding/relaunching uses the r03 commands with a fresh output directory and
fresh unique tag. It requires a separately authorized foreground interval; this
turn used exactly one completed live attempt. No extra capture was started.
Current Codex remaining percentage was not visible in tool UI; no credential,
session or unofficial rate-limit files/endpoints were read. The last user-provided
reading in this session was approximately 48%, with a requested floor near 20%.
