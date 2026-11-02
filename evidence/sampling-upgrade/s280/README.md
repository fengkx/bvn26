# s280 — Additional non-display completion: s228 DoAction (unproved)

Base master `343d1dbb` / #157; branch `feat/s280-nondisplay-completion`.
Exclusive authority: [AFTER-s272 rank 8](../next-fix-priority-after-s272.md).
`production_admitted=false`; `native_parity_proven=false`; M0-02 pending.
Evidence-only diagnosis; no completion implementation or product obligation closed.

## Different retained rejection

Selected **s228 Ichigo zero-stage standalone DoAction**, catalog key 一护2,
`game/fighter/ichigo.swf`, unchanged
[case](../s228/ichigo__attack__neutral__ground__near.json).
This is neither s232/Yijiao geometry (s254–s259) nor s223/Sasuke callsite (s269).
Geometry/display/bitmap/clipaction/callsite sampling flags are all false.
No solved case is rebuilt or recaptured.

[diagnose.py](diagnose.py) reuses the pinned s269 read-only event classifier and
extends it with per-period accounting for this distinct rejection. It verifies
all s228 artifact pins, archived build metadata, every output SWF, original
source hashes and instrumentation diff. The complete 5,630-event stream is
passed to the unchanged native validator, which exits1 with
`native evidence: events beyond completion boundary`. Zero samples admitted;
DoAction/full-AS admission remains blocked, not evaluated as passing.

[diagnosis.json](diagnosis.json) retains every suffix row, payload, sequence,
clock, and the complete archived root observer:

| Boundary | Sequence | Tick / display | Classification |
| --- | --- | --- | --- |
| Requested final DoAction sample | 5539 | 60 / 497 | Before first done |
| First done | 5540 | 60 / 497 | Requests ordinary quit |
| Terminal callbacks | 5541–5574 | 60 / 497 | 34 key reads; not disposable tail |
| First later root | 5575–5585 | 61 / 498 | Input, actor/helper rows, sample, second done |
| Later callbacks | 5586–5619 | 61 / 498 | Another 34 key reads |
| Second later root | 5620–5630 | 62 / 499 | Input, actor/helper rows, sample, third done |

All **90** post-done events are classified: 34 terminal and 56 later-root rows.
There are 63 action samples and three dones. No suffix prefix is substituted
for the full trace in admission. Tick62 has no observed post-done callbacks;
that absence does not prove a complete final callback cycle or exact quit time.
The archived root increments display/fight, latches input, records states and
DoAction sample, then requests quit; there is no closure guard. This supports
root re-entry while quit is pending, not an executed-PC or shutdown-time claim.

## Normal quit truncation is separate

The locked s269 normal/held raw streams are reclassified, without rerunning or
resealing their receipts. Normal has 5 post-done frame/intro events and no
terminal key reads; held has 51 terminal callbacks (including 34 key reads)
plus closure, with 61 samples in both. These are **Sasuke callsite controls**,
not execution evidence for Ichigo DoAction. A normal receipt alone cannot prove
terminal completeness. Neither the 34 s228 key reads nor s269's 51 callbacks
is a universal expected callback count for a fresh run.

## Independent opt-in experiment justified, not yet proved

The selected whole suffix and source order justify the following next discriminator:

1. Build only this unchanged s228 tape/configuration with standalone DoAction.
   Bind the original source/inventory and every built SWF. Use s269's temporary
   main-script guard pattern as a candidate, with a distinct explicit opt-in;
   its Sasuke binary cannot serve as the Ichigo control. No shared default change.
2. Produce two fresh builds/run IDs: normal quit at done and held quit after
   closure. Done arms closure; the next root callback closes observation before
   incrementing either clock, changing inputs, sampling or emitting another done.
   Retain all callbacks between done and closure. Archive full scripts/diffs.
3. Keep full raw logs, host-log equality checks, original receipts and failures.
   Held must actually observe closure before tick61, preserve the final requested
   sample and all intervening events. Strict native validation must pass on the
   full stream; no trimming, mixed modes or historical receipt repair.
4. Compare ticks0–60 actor/helper/input records against s228; separately retain
   random order/values and callback order. Report normal's missing terminal events
   as quit truncation, not parity or proof of completeness. Do not assume identical
   startup clocks, callback counts, generated names or random replay.
5. Run unchanged DoAction and full-AS gates independently, preserving all
   unvisited/unsupported/source ownership failures. A bounded capture pass would
   establish only this capture prerequisite, never native parity or default rollout.

No new capture is required to establish this historical rejection and its
missing proof. An implementation claim **would require** the above fresh pair;
locked s269 cannot supply it. This PR takes the explicitly allowed unproved,
evidence-only outcome. Zero new builds/player launches/captures; no hypothetical
capture cost is reported as measured. s269's historical costs were 7.918/8.161s
build and 31.743/29.245s capture; they are context, not an s280 estimate.
Measured analysis/check costs are in [gates.json](gates.json),
[project-checks.json](project-checks.json), and [session-timing.json](session-timing.json).
Person-days and future capture cost remain unknown.

## Source-first and scope

The source-bound root observer answers the probe's per-callback ordering and
completion behavior. No authored frame scripts, PlaceObject/MOVE lifetime,
goto/stop/label exit or gameplay invariant is changed. Same-input s228 native
observations exist, but a changed probe has no native execution evidence.
The five-question gate does not authorize a gameplay/runtime implementation.
Tests assert retained observations and rejection integrity, not inferred timing.

Only s280 evidence, focused tests and requested tracking/manifest files change.
Other ranks and s254–s279 are untouched. No default rollout, mixed modes, old
receipt resealing, trimming, solved-case repetition, relaxed threshold, gameplay
rewrite, merge or deployment.

## Reproduce

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s280/diagnose.py --output /tmp/s280.json
PYTHONPATH=. python3 evidence/sampling-upgrade/s280/diagnose.py --output /tmp/s280-strict.json --strict-native
PYTHONPATH=. python3 evidence/sampling-upgrade/s280/diagnose.py --output /tmp/s280-required.json --require-completion-proof
python3 -m unittest tools.tests.test_additional_nondisplay_completion tools.tests.test_callsite_completion_window tools.tests.test_non_display_completion_diagnosis tools.tests.test_sampling_native tools.tests.test_sampling_doaction tools.tests.test_display_completion_default tools.tests.test_yulong_display_completion tools.tests.test_import_guards
python3 tools/verify.py
python3 tools/check_handoff.py
```

Diagnosis exits0; strict native and completion proof requirements intentionally
exit1. Portable analysis/tests require no player, XML cache, new capture or
receipt restoration. Project checks verify package integrity, not game parity.

Validation: **76 focused tests pass**. Integrity, handoff and contracts exit0.
Both negative gates exit1 as expected. No Godot check applies to this evidence-only cut.
