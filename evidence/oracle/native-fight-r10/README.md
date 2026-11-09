# r10: discriminate rejected timer boundaries without admitting them

Offline replay only; no Flash launch, capture, new SWF, runtime or shared-validator
change. Base f16fe1884945e0ec75666497a9619e2f296a338a includes r09 (#252).
Official remaining UNKNOWN; not claiming above floor. M0-02 remains pending;
production_admitted=false, native_parity_proven=false, oracle_accepted=false.

## Verified account from r09 and source

The refusal is a phase/completeness mismatch in the captured prefix, not evidence
that the HP assignment failed. The timer was already executing while HP had not
yet been assigned at the observed chushi boundary.

Locked `scripts/main.json:DefineSprite_1813/frame_1/DoAction.as` initializes
`gametime=maxtime` and, outside unlimited/practice mode, registers
`setInterval(time,1000)`. The callback checks zhanting and both actors' sw before
subtracting time. Those conditions do **not** prevent the callback from executing;
remaining display logic still runs. r08 observes its entry/exit and actors without
excluding paused/loading states. It does not require HP initialized first.

Actual immutable r09 sequence:

- Timer ordinals1–6 entry/exit (12 boundaries, last pair seq1130/1133) contain
  undefined HP for both actors. No other actor field is incomplete there.
- chushi-hp-before seq1142, actor rows1143/1144: HP undefined.
- Original chained HP assignment, source `frame_8/DoAction.as`, `chushi`.
- chushi-hp-after seq1145, actor rows1146/1147: both HP equal observed maxhp's
  encoding `f:1:9:131072000:0` (=1000). Before/after have getTimer62119,
  camera ordinal182, zhanting=true and gamePaused=false.
- Ready-play-before seq2293/getTimer66979 is a later source-local marker.
- First observed unpaused camera entry seq3092/getTimer71221/ordinal455 is later
  still. It is a sampled checkpoint, not the exact startFight call or global tick.

Source `startGame()` calls chushi and only then sets p2loaded=true. Source
`startFight()` has a distinct readiness/unpause path. Other round/restart paths
also call chushi. r09 does not tag the chushi caller; this report does not assert
which caller executed or infer scheduler order beyond the actual event sequence.
The source excerpts and exact paths/lines are in `source-boundaries.json`.

Thus r09 proves HP was unset at the early callbacks and set at the later observed
assignment. It does not prove an engine defect, timer race or lost input. The
unchanged r05 structural gate requires complete actor fields at every retained
clock boundary; the full prefix correctly fails that requirement. Positive fight
queries cannot discharge a separate completeness obligation.

## Minimal offline facility

`analyze.py` verifies the pinned r09 receipt hashes, build/session identity,
fresh tag, append interval and exact tagged/raw selection, then uses the existing
strict sequence parser. It requires one adjacent before/after HP marker pair,
matching immediate P1/P2 actor pairs and a complete post-assignment HP result.
Missing, repeated or reordered assignment markers refuse classification rather
than guessing a phase. Repeated-round classification is intentionally unsupported.

All48 timer boundaries and their complete raw actor rows are retained in
`classification.json`, including every undefined value. Timer entry/exit pairs
and consecutive local ordinals are checked. Each boundary receives two descriptive
labels: relation to the **observed HP assignment**, and relation to the **first
observed unpaused checkpoint**. Neither is called a global tick or initial state.

Actual results:

| Class | Count |
|---|---:|
| Before observed HP assignment, incomplete | 12 |
| After observed HP assignment, complete fields | 36 |
| After observed HP assignment, incomplete | 0 |
| Before first observed unpaused checkpoint | 28 |
| At/after first observed unpaused checkpoint | 20 |

There are16 complete timer boundaries after HP assignment but before the first
observed unpaused checkpoint: field completeness alone is not fight readiness.
A negative test introduces undefined HP at a post-assignment boundary; it remains
explicitly incomplete and oracle_accepted remains false. No filtering/filling or
synthetic replacement row is used. An incomplete HP-after result cannot even
establish the descriptive phase boundary.

The entire original raw prefix is passed to **unchanged r05 validate_rows**;
its refusal stays `Incomplete actor state at clock boundary`. Both CLI modes exit1
and every admission flag stays false, regardless of classification counts.
Classification is an explanation of a rejected run, not a revised admission rule.
No historical r09 wrapper is executed because it writes its historical report;
the unchanged structural function is imported directly without editing it.

```sh
python3.11 evidence/oracle/native-fight-r10/analyze.py
python3.11 evidence/oracle/native-fight-r10/analyze.py --require-oracle
python3.11 -m unittest discover -s evidence/oracle/native-fight-r10 -v
```

No new markers are necessary to distinguish this existing HP transition, so no
new SWF compile/tag mutation is justified or performed. Tests cover all48 retained
boundaries, post-assignment missing HP, missing/duplicate/reordered HP markers,
incomplete assignment results, timer gaps/missing actors and readiness distinction.
See checks.json for actual exits and project checks.

## Next evidence needed

No new live is required to explain these twelve failures: r09 already contains the
necessary source-local before/after observations. Full M0-02 acceptance still needs
freshly authorized live work. In particular, distinguish exact fight-start/caller
and scheduler phases from camera samples, bind physical inputs to downstream
consumption and certified ticks, establish complete random tape/provenance, full
exclusive contract trace, deterministic repeat and observer noninterference.
No repeated capture is authorized here. Any future lifecycle-aware acceptance
proposal must preserve and explicitly account for the entire loading prefix,
prove initialization and instance continuity, reject post-initialization missing
state, and undergo independent review; this classifier does not implement it.
