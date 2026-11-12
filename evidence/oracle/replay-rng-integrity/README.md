# M0-02: reliable RNG consumption validation for repeatable replay

Base: `af538c7aafc1fa0114440c0a80c0b077c316fa4a` (#275 squash). This change implements an offline integrity check in the existing continuous-replay validator; it does not continue the debugger-client/producer search.

## Production gap selected

M0-02 requires reproducible initial state/input and attributable capture; TR-02 requires the same input/random consumption to reproduce discrete results. M0-03 still needs native scheduling calibration. Rechecking the broader path found:

- Existing replay/schema semantics already check held/pressed/released transitions (`tools/validate_contracts.py`); another format-only schema would duplicate that work.
- The physical menu tape explicitly uses wall time, not observed consumption ticks. A new foreground run or host input mechanism would need separate preservation/experiment review; none was run.
- The continuous AI replay validator already compares state, geometry, inputs, clocks and random consumers. Its random check trusted the supplied stream without rechecking sequence/draw integrity, fell back to sequence -1 when the loaded intro poll was absent, derived its cursor offset from the replay's claimed indices, and coerced replay types. Its source-number decoder also lacked the collector's encoding checks. These are offline-reproducible acceptance-tool defects, independent of the unresolved helper/native-return route.

The collector already requires contiguous observation and draw indices. The validator now checks those invariants itself at the comparison boundary rather than trusting that an arbitrary input JSONL passed the collector. This is useful tool progress, not a new accepted oracle.

## Implemented behavior

`tools/probes/validate_ai_continuous_replay.py` now:

1. Requires contiguous source event and RNG sequences from one, plus a loaded intro poll before Ready. It never invents an absent replay start or renumbers draws.
2. Reuses the existing collector's binary-number decoder. Math.random observations require a nonempty site and finite value in [0,1). State-coordinate decoding remains unchanged; negative coordinates are not rejected by this rule.
3. Derives the pre-replay RNG offset and Ready cursor from source observations, including the valid zero-draw case. All pre-intro draws are checked before the existing replay window is selected; they are not silently discarded as malformed prefix.
4. Compares the complete ordered original-index/site/value vector without string/bool coercion or tolerances. Missing/extra/reordered/different consumption fails. `random_tape_complete` must be the boolean true, not a truthy string.
5. Writes a structured unknown/exit1 report for invalid evidence instead of leaving the CLI with only a traceback. Report limits use the actual requested horizon.

No thresholds or admission gates are relaxed. The existing positive-path synthetic fixture was corrected to include the boundary it purports to test, unique event sequences, and legal RNG values. Its malformed predecessor remains reproducible from the pinned base commit; no historical capture was edited.

## Actual verification and bounds

`before-after.json` is explicitly **synthetic**, not a native receipt. `reproduce.py` reads the base validator and old unit fixture from Git. The untouched old fixture already failed the random scope check. With a self-consistent but invalid vector containing all its source draws, the old random subcheck reported `scope_complete=true` despite missing intro start, duplicate terminal sequence and RNG values 1.5/-1.5. The overall old report remained unknown for another reason; this is **not a demonstrated whole-oracle false admission**. The new validator refuses the invalid stream. Targeted mutations separately exercise missing start, index gaps/reset, nonfinite/invalid values and replay omissions/type substitutions.

An immutable historical `input-alias-r12` stream also passes the new source-tape extraction test and exactly matches its separately retained random tape. The full historical replay comparison still exits1 (`source_build_provenance_not_clean`, body_boundaries); 288 expected random draws versus 110 consumed remain unaccepted. That input-alias capture is an older intervention-bearing, selected-bundle diagnostic, not the physical-input oracle. `historical-recheck.json` pins inputs and records that refusal. No claim of complete native RNG coverage, deterministic repeat or noninterference is made.

21 tests across numeric/capture-boundary, continuous replay, and the new random-integrity suite pass. `checks.json` records final commands/exits. No live/Flash/FDB/CU, native instrumentation, SWF compile, game/scripts/runtime edits or deployment operation. Historical oracle packages and the two untracked failed r22 directories are unchanged.

All five flags remain false: production_admitted, native_parity_proven, oracle_accepted, certified_global_tick, os_input_join_proven. M0-02 remains pending. Source-observed contiguity cannot prove uninstrumented random calls are absent. No original/native return is inferred. Official quota UNKNOWN; no supported quota-read tool was exposed in this turn.

## Recheck and next executable step

```sh
PYTHONDONTWRITEBYTECODE=1 python3.11 -m unittest tools.tests.test_ai_capture_boundary tools.tests.test_ai_continuous_replay tools.tests.test_ai_random_consumption
PYTHONDONTWRITEBYTECODE=1 python3.11 evidence/oracle/replay-rng-integrity/reproduce.py
PYTHONDONTWRITEBYTECODE=1 python3.11 tools/probes/validate_ai_continuous_replay.py evidence/ai/input-alias-r12/events.jsonl evidence/ai/input-alias-r12-first-difference.json --horizon 600 --source-build evidence/ai/input-alias-r12/build.json --output /tmp/bvn-rng-historical-recheck.json
python3.11 tools/verify.py
python3.11 tools/check_handoff.py
```

After independent review, the next executable offline step is to trace the first missing/different RNG consumer in the existing continuous replay against its source site and runner, retaining the incomplete vector and provenance refusal. Do not patch a draw merely to consume tape or treat that intervention-bearing diagnostic as M0-02 admission. Any fresh original-vs-observer repeat experiment still requires an explicit plan for fixed setup, physical input, full consumer coverage, clock mapping and noninterference controls plus separate authorization. No experiment permission is requested by this PR.
