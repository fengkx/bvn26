# s254 — Post-queue rank 1: non-display completion diagnosis

Baseline master `53d35fcd` / #131; branch `feat/s254-post-queue-rerank`.
The [new ranking](../next-fix-priority-after-s253.md) was written before the
analysis. Exclusive s254 executes rank 1 only, on the retained **s232 Yijiao
geometry capture**. Evidence-only: no runtime or instrumentation fix is proved.
`production_admitted=false`; `native_parity_proven=false`; M0-02 stays pending.

## What is new

s249 proves a standalone display window, explicitly excluding non-display.
s232's earlier diagnostic groups all 50 events after done together. This cut
joins those events to **both** fight tick and root display period and verifies
the actual archived build's observation order. It separates callbacks that must
be retained from the next root invocation that causes the rejection:

| Boundary | Sequence | Tick / display | Observation |
| --- | --- | --- | --- |
| Last requested geometry sample | 5649–5654 | 60 / 525 | begin, four boxes, end with count4/receivers4 |
| First done | 5655 | 60 / 525 | after the complete geometry sample |
| Terminal-period callbacks | 5656–5689 | 60 / 525 | 34 key reads, both actors; must not be cut at done |
| First later-root event | 5690 | 61 / 526 | input_next_display; strict validator's first boundary violation |
| Later-root remainder | 5691–5705 | 61 / 526 | actor/helper observations, a full geometry sample and second done |

The complete stream has **5,705 events**, 62 geometry begin/end pairs and two
done events. All 50 suffix rows and the final requested geometry sample are
retained in `diagnosis.json`, including payloads and clocks. The unchanged
`validate_capture` rejects the **entire untrimmed stream** with `events beyond
completion boundary` (exit1). Zero samples are admitted; no receipt is issued.
We do not feed a selected prefix to a collector or claim a full geometry pass.

The hash-bound `instrumentation.diff` in s232's build archive places the root
increments before input/state observation, then `aiGeometrySample()`, then
`if(aiFight >= 60) { done; fscommand("quit"); }`. It has no closure guard.
The report includes that complete generated root function. Archive metadata,
all instrumented SWF hashes and locked source hashes are checked; the original
s232 artifact manifest pins case, build and compressed raw bytes. This is a
source/build-order cross-check, **not** an executed-PC trace or a new capture.

The first observed later-period event and the generated root order support a
root-observer re-entry diagnosis while quit is pending. They do not measure the
exact quit dispatch time or prove a new closure preserves every geometry mode.
In particular, the 34 terminal callbacks rule out treating every post-done row
as garbage. s249's display proof cannot be silently promoted to geometry proof.

## Source-first limits and next observation

This is analysis of the probe window, not an implementation of a game mechanism.
The archived root callback's complete statement order, unchanged static tape and
native observations are bound above. Authored move-frame scripts, PlaceObject /
MOVE lifetimes and label exits have not been audited for a gameplay change.
The five-question runtime gate is therefore **not satisfied for runtime edits**.
Tests lock retained observations and evidence integrity, not inferred gameplay.

The next bounded experiment would use exactly the s232 tape and standalone
geometry mode, with a source-bound opt-in guard before the next root increment.
Capture a normal exit and a declared held-quit control; bind the compiled probe
and preserve terminal callbacks, final geometry_end/count, actor/random/input
records, full raw stream and strict receipt validation. Explicitly observe
closure before tick61 and compare original native actor inputs/states without
editing the source tape. A successful receipt would only recover the capture
prerequisite; run the unchanged full geometry gate separately and retain its
receiver/source failures. No such experiment or fix is claimed here.

## Changed and deliberately unchanged

Added ranking, read-only diagnosis, focused negative tests and handoff records.
No production code, builder, observer, collector, strict validator, callback,
threshold, baseline, tape or old evidence is modified. No blanket aliases,
receiver eligibility changes or gameplay rewrites. Bitmap's existing completion
policy and all display/source obligations remain intact. Ranks2–5 are not begun;
no other capture or s241–s244 residual is reopened.

## Reproduction and gates

All diagnosis inputs are repository artifacts; no player, XML cache or old
absolute-path restoration is needed. Run from the repository root:

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s254/diagnose.py --output /tmp/s254-diagnosis.json
PYTHONPATH=. python3 evidence/sampling-upgrade/s254/diagnose.py --output /tmp/s254-strict.json --strict-native
python3 -m unittest tools.tests.test_non_display_completion_diagnosis tools.tests.test_sampling_native tools.tests.test_sampling_geometry tools.tests.test_display_completion_default tools.tests.test_yulong_display_completion tools.tests.test_import_guards
python3 tools/verify.py
python3 tools/check_handoff.py
```

Diagnosis exits **0** for successful evidence recomputation; `--strict-native`
exits **1** for the unchanged native completion rejection. This wrapper calls
the real validator on the complete decompressed capture; it is not a receipt
revalidation or a stand-in green geometry gate. The full geometry product gate
remains blocked at capture admission; downstream obligations are not evaluated.

59 focused tests pass, including unchanged display completion and sampling
negative tests. Integrity, handoff and contracts exit0. `gates.json` and
`project-checks.json` record commands, exits, logs and measured subprocess time;
`manifest-audit.json` records reviewed tracked-document hashes. Actual measured
validation effort is recorded, with no inferred person-days or total session
time. No merge or deployment.
