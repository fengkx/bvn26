# r11: first observed readiness subset, not certified fight start

Offline analysis of immutable r09 only, based on master
7926ecffe5a0d60f341402fda2be419ccd5fbb35 (#253). No Flash launch/capture, no new
SWF/marker, no runtime or shared-gate change. Official remaining UNKNOWN;
not claiming above floor. production_admitted=false, native_parity_proven=false,
oracle_accepted=false; M0-02 pending.

## Evidence boundary

r10 already proved that early timer snapshots precede observed HP assignment.
This additive classifier asks a narrower next question: at which recorded camera
entry do the following **observed subset** of conditions first coincide?

1. After the recorded chushi HP assignment with complete matching HP-after values.
2. After the recorded ready-play request (a request, not proof of completion).
3. Both recorded pause flags are false.
4. The recorded p2loaded flag is true.
5. The immediately following P1/P2 actor snapshots contain all expected numeric
   fields, including HP. No undefined field is filled or discarded.

The first such checkpoint is **seq3092, getTimer71221, local camera ordinal455**.
Its preceding game-entry checkpoint is **seq3074, getTimer71179, ordinal454**,
with zhanting=true. Both have p2loaded=true. The first subset is a sampled
observation, not the exact transition instant, a global tick or engine-ready proof.
758 game-entry checkpoints are retained by source sequence and actor-row references;
291 satisfy this subset. First/preceding checkpoint actor rows are also retained
verbatim in classification.json. Original source rows remain immutable in r09.

Locked `scripts/main.json:frame_8/DoAction.as` defines:

```actionscript
function startFight()
{
   _root.zhanting = false;
   _root.readying = false;
   _root.setMenuEnable(true);
}
```

r09 does not record source-local startFight entry/normal-return, readying, or the
outcome of setMenuEnable. Other source paths also clear zhanting. Therefore an
unpaused camera snapshot—even with complete HP/p2loaded—cannot identify that
function's execution or prove all fight-readiness obligations. No marker is
invented, and `exact_fight_start_proven` / `full_fight_readiness_proven` stay false.
The caller/instance continuity and global scheduling boundary are also unproved.

## Per-boundary distinction, including re-pause

All48 timer boundaries and raw actor rows remain present. The classifier uses
**each timer boundary's own pause flags**, never the first checkpoint as a lasting
permission to call later boundaries ready:

| Observed class | Count |
|---|---:|
| Before HP assignment, incomplete | 12 |
| After HP assignment, fields complete but paused | 18 |
| After HP assignment, fields complete and unpaused (full readiness unproved) | 18 |

The first16 complete-but-paused boundaries precede the first subset checkpoint.
The other2 are timer ordinal17 entry/exit, seq3920/3923, **after** that checkpoint.
This is why r10's temporal relation counts (16 complete before,20 after the first
unpaused checkpoint) must not be mistaken for persistent readiness. Timer rows
lack a contemporaneous p2loaded/readying/menu tuple, so no stale camera flag is
carried forward to certify them. `timer_readiness_proven=false` for every row.
A post-HP incomplete row has its own class and stays incomplete even after the
first subset. Unknown booleans and missing/ambiguous boundaries fail closed.

## Facility and refusal

`analyze.py` verifies r09 receipt hashes, session/build identity, raw/tag selection,
freshness/append interval and locked main source hash. It imports r10's pure
classifier (not its historical-writing replay) and r05's unchanged structural
function. No historical report is rewritten. It retains checks at every camera
entry and every timer boundary; all12 early incomplete rows stay rejected.

Both CLI modes return **1**. The entire original prefix still fails unchanged
r05 validate_rows with `Incomplete actor state at clock boundary`. A sampled
readiness subset does not override that refusal or any other oracle requirement.

```sh
python3.11 evidence/oracle/native-fight-r11/analyze.py
python3.11 evidence/oracle/native-fight-r11/analyze.py --require-oracle
python3.11 -m unittest discover -s evidence/oracle/native-fight-r11 -v
```

Tests cover missing loading/actor data, unknown booleans, missing phase markers,
post-HP incomplete state, later re-pause and inability to promote a subset to
exact start/readiness/admission. Checks and artifact hashes are retained. No SWF
compilation was needed because the change is offline interpretation only.

## Live needed next?

Not for this classification; existing r09 observations are sufficient. **Yes for
proving exact fight start/full readiness**: a future authorized, source-reviewed
capture would need the actual startFight boundary, contemporaneous readying/menu
outcome and actor/instance state, plus scheduler phase evidence. This package
neither adds those markers nor runs that capture. Missing signals are explicit,
not replaced by a guessed tick or the first convenient complete row.

Certified downstream input consumption, complete random tape/provenance, exclusive
full contract trace, deterministic repeat and original/instrumented noninterference
also remain unproved. No production requirement or M0-02 acceptance is closed.
