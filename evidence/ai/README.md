# AI static-analysis evidence

Date: 2026-09-08. Status: static source analysis only.

The specification is [AI_SPEC.md](../../docs/AI_SPEC.md). No AI runtime was
implemented or original-game AI replay captured in this change. M5-03 remains
pending; the existing execution profile remains provisional.

## Reproduction

```bash
python3 tools/analyze_ai.py
python3 tools/analyze_ai.py --check
python3 tools/verify.py
python3 tools/check_handoff.py
```

`source-audit.json` indexes all 62 retained script bundles and uses the existing
minren/yihu base timeline exports for geometry and display membership. Input
SHA-256 values are embedded. It is analysis evidence, not a production data
contract, compiled AI program, or proof that every discovered controller is
reachable. Existing timeline exports were not regenerated during this analysis.

## Observed static results

- 35 main fighter bundles, 26 assistance bundles, and one main bundle scanned.
- 69 controller scripts in nine exact-source groups; member paths, hashes,
  changed functions and full diffs against the standard controller are retained.
- 49 identical `randAI` definitions across all 35 main fighter bundles.
- The only observed assignments to the five AI random fields are the five
  ordered assignments inside `randAI`.
- 311 source lines contain `Math.random()` or `random(...)`; this is a lexical
  inventory, not a count of executed calls or proof of RNG stream identity.
- Every indexed base-slice Sprite 16 enterFrame placement has matching linear
  display-list membership. Membership includes placement frames and is not
  equivalent to executed callback ticks.
- Both base AImain clips contain 11 sensors on frame 2. The standard controller
  references `absmian`, which is absent from those two frame-2 display lists.

## Validation boundary

The audit freshness check, retained-input verification and handoff checks passed
for this change. They verify source association, reproducibility and document
links/dependencies only. No Godot smoke or new Flash AI test was run: no runtime
code or schema was changed. The specification lists the required future tests
as AI-T01 through AI-T14 and unresolved runtime questions as AI-U01 through
AI-U09. A missing reference, timer-lifetime issue or decompiler oddity is recorded
as a question to verify, not silently repaired.

The pre-change retained-input verification also passed. Manifest updates for this
work are limited to the explicitly edited documentation/task entries and the new
AI artifacts; unrelated working-tree changes were preserved.

## Subsequent compiler work

See [compiler-progress.md](compiler-progress.md) for the native predicate compiler,
scalar translation checks and parent-goto probe. This later work does not change
the full-battle acceptance status above.
