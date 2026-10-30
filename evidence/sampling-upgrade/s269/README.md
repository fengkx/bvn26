# s269 — AFTER-s263 rank 6: one standalone callsite completion window

Base master `91bcd700` / #146; branch `feat/s269-nondisplay-completion`.
Only [AFTER-s263 rank 6](../next-fix-priority-after-s263.md) is executed.
`production_admitted=false`; `native_parity_proven=false`; M0-02 stays pending.
The bounded completion cut is proved for this case only, in an explicit opt-in
wrapper. Full callsite/AS admission is **not** proved. No default rollout.

## Selected rejection, classified before capture

The selected retained rejection is **s223's first Sasuke callsite capture**:
[complete raw stream](../s223/rejected-completion-boundary.log.gz),
[original build](../s223/rejected-completion-boundary-build.tar.gz), and unchanged
[s223 case](../s223/sasuke__attack__neutral__ground__near.json).
This is a different observation mode from s259's recovered s232 geometry case.
Callsite's existing DoAction/clip-action instrumentation dependencies are retained;
no geometry/display/bitmap mode is combined with it.

[classify.py](classify.py) verifies the retained artifact hashes, archived SWFs,
source hashes and archived root observer order before classifying all 10,240
events. [historical-classification.json](historical-classification.json) retains
exact sequence numbers, payloads, clocks and the observer source:

- First done: sequence 10,178, tick60/display531.
- 51 terminal-period events: 34 key reads, six clip entries, two DoAction entries,
  four frame/intro boundaries, and five callsite phases. The selected terminal
  call has predicate-before → true → call-before → call-after → end.
- 11 later-root events at tick61/display532, including another action sample and
  second done. Root observation advanced before the quit request took effect.

The unchanged native validator rejects the **entire** historical stream with
`events beyond completion boundary`, exit1. No old receipt is issued, repaired
or resealed; no suffix is trimmed. The old incomplete invocation at tick10 is
separate from this completion failure and remains an unresolved obligation.

## Separate opt-in experiment

[build_probe.py](build_probe.py) reuses the locked s259 wrapper/instrumenter
pattern for this one fixed case, with only standalone `--sampling-callsite`.
The s259 binary itself is geometry/Yijiao and cannot serve as this callsite/Sasuke
control; rebuilding is necessary to keep modes separate. It builds ordinary
instrumentation first, then adds the next-root guard to a
**temporary** main script; the held control moves only the probe's quit request
to after closure. No shared builder, collector, strict validator or runtime changes.
Each archive includes the complete two-stage diff, main scripts and captured SWFs.
All four fighter/helper output SWFs, callsite specification and action inventory
are byte/data-identical to the retained s223 build. Main necessarily differs for
fresh run identity and the declared instrumentation.

| Run | Events | Native receipt | Root samples | Post-done events | Callsite / full AS |
| --- | ---: | --- | ---: | --- | --- |
| Normal | 9,955 | exit0 | 61 | 5 same-period frame/intro events | exit1 / exit1 |
| Held quit | 9,882 | exit0 | 61 | 51 callbacks + closure | exit1 / exit1 |
| Retained s223 | 10,240 | exit1 | zero admitted | 51 terminal + 11 later-root | blocked at receipt |

Normal quit does **not** exercise the guard or prove a complete terminal callback
cycle. Held quit does: all 51 terminal callbacks (including the complete selected
call) remain, then `capture_window_closed` executes before the next root increment.
No tick61 or second done appears. This proves a bounded capture completion cut,
not full invocation coverage, authored completion or a gameplay return model.

Both new captures match all **122 actor rows on 14 fields**, three sets of 122
helper rows, and all 61 input-latch rows from s223 at ticks0–60. Held also matches
all 1,561 key reads; normal has 1,527, omitting the 34 callbacks which did not run
before normal shutdown. Ticks0–59 key reads match in both runs.
Random call order and values are retained in [diagnosis.json](diagnosis.json):
five fight-period random values differ. No locked random replay or zero probe
perturbation is claimed. Pre-fight counts, generated instance names and root
clock offsets are not normalized in captures. Tick-range comparisons never feed
a shortened stream to admission or dimension validators.

The fresh normal/held runs retain 439/434 complete selected invocations,
respectively, and each retains one incomplete tick10 invocation ending at
`call_before`. Both callsite CLIs exit1. Full AS independently exits1 with **825
unvisited blocks / 420 uninstrumented scripts**, without relaxing ownership.
`runtime_fighter=null` still does not attest actual loaded allocation/bytes.

## Source-first boundary and next discriminator

1. Archived main `frame_10/DoAction.as` root order is bound by the retained diff;
   new full scripts/diffs show the guard before `aiDisplay++`/`aiFight++`, input,
   state and `doaction_sample`. Done only arms the guard.
2. No authored PlaceObject/MOVE or instance lifetime changes; identical fighter
   SWFs retain `Sasuke.swf#DefineSprite_603/frame_1/PlaceObject2_16_31` enterFrame.
3. No authored goto, label exit or stop changes. Only observation/quit scheduling
   changes; no missing call-after is synthesized.
4. Tests lock retained source-bound call phases and strict rejection of sequence
   gaps, later-root events, missing final sample and missing call-after.
5. Two fresh original-player captures use the exact old input bytes. Measured
   actor/input controls agree; random differences and incomplete calls remain.

The next **local** discriminator, if separately authorized, is whether the normal
quit's terminal callback truncation can be independently bounded without changing
authored calls, across a separately selected retained rejection. Do not roll this
wrapper out by default or claim arbitrary modes are solved. The tick10 invocation
needs its own source/continuation evidence before a full-callsite claim; it is not
investigated here and does not reopen ranks 3 or 8. Ranks **1–5/7–9**, all
**s254–s268**, production code, thresholds and baseline tapes remain unchanged.

## Costs and validation

Fresh capture was required because an old stream cannot demonstrate execution of
an added guard or the held-quit control. Exactly two builds and two captures, no
retries: builds **7.918/8.161 s**, captures **31.743/29.245 s**, normal/held order.
See [build-costs.json](build-costs.json), [capture-costs.json](capture-costs.json),
[gates.json](gates.json) and [project-checks.json](project-checks.json).
Both used the existing serialized native-player lock and authorized activation.
Each complete adapter stream was compared byte-for-byte with all run-prefixed
host-log lines before the next launch; hashes are in each host-log audit.
These subprocess wall costs are measured; person-days remain unknown.

107 focused tests pass. Native receipts, diagnosis and locked s259 recomputation
exit0; historical rejection, incomplete callsite and full AS exit1 as intended.
Integrity/handoff/contracts checks pass. [scope-audit.json](scope-audit.json) and
[manifest-audit.json](manifest-audit.json) record the exclusive scope and reviewed
hash changes. No merge or deployment.

## Reproduce

Portable checks need neither native player nor an XML cache:

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s269/classify.py --output /tmp/s269-old.json
PYTHONPATH=. python3 evidence/sampling-upgrade/s269/classify.py --output /tmp/s269-old-strict.json --strict-native
PYTHONPATH=. python3 evidence/sampling-upgrade/s269/diagnose.py --output /tmp/s269-diagnosis.json
python3 -m unittest tools.tests.test_callsite_completion_window tools.tests.test_geometry_completion_window tools.tests.test_non_display_completion_diagnosis tools.tests.test_display_completion_default tools.tests.test_yulong_display_completion tools.tests.test_sampling_geometry tools.tests.test_sampling_native tools.tests.test_sampling_callsite tools.tests.test_import_guards
python3 tools/verify.py
python3 tools/check_handoff.py
```

The `--strict-native` command intentionally exits1. For existing receipt/gate
revalidation, restore each `normal/` or `held/native-build.tar.gz` into its recorded
`/private/tmp/bvn-s269-{normal,held}-build`, decompress its full native log into
`/private/tmp/bvn-s269-{normal,held}-capture/native.log`, and copy its original
receipt there as `receipt.json`. Restore pinned probe sources/player and run exact
commands in gates.json; do not reseal receipts. New captures must use fresh paths
and run IDs, as in build-costs.json/capture-costs.json; add `--hold-quit` only for
the independent held build. Keep both raw streams and all failures.
