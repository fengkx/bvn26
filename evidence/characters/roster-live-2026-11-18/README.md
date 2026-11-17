# Selectable roster live audit — 2026-11-18

Actual native Flash and native Godot executions, using identical input fixtures.
This is a first visual audit of every selectable fighter/form and helper, not
acceptance of every move or a claim of complete one-to-one parity.

## Coverage and results

- All 40 selectable fighters/forms: 420 ticks each; two guard sequences and one
  ultimate or the source-supported equivalent command. All 33,680 actor-state
  rows match across the 14 compared fields. Every case records source `blocked`
  guard packets. Eight rendered frame pairs per case were reviewed.
- Root position: 37 of 40 cases match. Lee differs at tick 123, Itachi at 293,
  and Kakashi at 198–203 (eight differing rows in 16,840 total). Differences
  remain in `comparison.json`; no tolerances or source baselines were changed.
- All six helpers: 420 ticks each, with eight rendered frame pairs reviewed.
  Actor states, root position, helper action/position/orientation and active
  durations match. Native helper rows are projected to the existing eight-field
  source comparator; the unprojected rows remain in each archive.
- Dedicated 32-tick guard-break cases for all 35 base roles are complete.
  All 2,310 actor-state and 1,155 root-position rows match; every source case
  records the actual `break` branch. Three frame pairs per case were reviewed.
  The five selected forms already have dedicated source guard-break captures in
  `../selected-forms/live-2026-11-17/`. See `break-comparison.json` for full comparisons.
- Dense Ichigo Bankai follow-up: four additional rendered pairs at ticks 149,
  151, 155 and 160 confirm a purple bounds rectangle missed by the wider initial
  sampling. All 362 actor states and 181 root positions still match.

## Repairs and open findings

Sage Naruto's white/cyan wind rectangle was fixed by compiling the source's
complex solid fill edges, retaining holes and shared vertices. The same-input
rerun matches 842 actor states and 421 root positions; before/source/after PNGs
are in `curved-paints/`.

Ichigo Bankai uses the same source-backed geometry path. The post-repair
rendered rerun removes the rectangle at all four dense samples and preserves
all 362 actor states and 181 root positions. Separate depth/HUD differences
remain visible and are not counted as repaired.

`visual-findings.md` records remaining particle rotation, depth/occlusion,
missing HUD, helper black-backdrop timing and smoke-edge observations. Gaara's
missing integer-random hit rotation is source-confirmed. Itachi's missing HUD
was reproduced both by direct terminal replay and by rendering every tick.
These findings prevent a visual parity pass even where combat traces match.

## Method and reproducibility

The source inventory covers 188 solid shape definitions. Candidates are not
automatically defects: rectangles, transparent controls and unused paints must
be distinguished before changing rendering. `solid-source-audit.json` retains
source hashes and shape ownership. `curved-paints/README.md` answers the
source-first questions for the two confirmed curve defects.

Native visual sampling runs the full fixture once, saves BattleCheckpoint state
at requested ticks, restores each state and redraws the scene. It was calibrated
against independent terminal replay: actor states match and the first sample's
pixels match; later clock digits differ because external timers are frozen.
This calibration does not establish every effect's child-clock parity. Follow-up
terminal and continuous-render runs are retained for specific visual defects.
Countdown digits, energy-bar flash phase and player arrows are not synchronized
visual baselines in this first pass.

Original Flash bitmap rows and native PNGs remain in per-case archives. No Flash
SWF is included. `runners/decode.py` reconstructs the 600×400 source PNGs from
`original/original.log`. `contact/` provides small side-by-side sheets (Flash on
the left). Archives include fixture, original provenance, captured random/timer
streams, actor/presentation/helper traces and native run logs. SHA-256 values and
full comparisons are in the comparison JSON files. `capture-retries.tar.gz`
retains interrupted/timeout attempts; fresh run IDs were used for started retries.

`runners/` records the executed scripts and calibration. Their absolute scratch
paths refer to `/private/tmp/bvn-roster-live`; the repository tools under
`tools/probes/` supply the original build, capture, collection and comparison
implementations. Production does not depend on these probes or on Flash.

## Web verification

The local release Web build was exercised with actual keyboard selection and
S+I inputs for both repaired roles. The crescent and close-range wind curves
render correctly; screenshots and build provenance are in `web/`. Two viewport
lifecycle errors were retained for follow-up, so this is not a zero-error Web
acceptance or a production deployment claim.
