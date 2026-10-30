# s272 — Strict rasterization: digit-edge family blocked before admission

Base: master `443d36b6821eff88ca16bb7dba5609fc3b6275bd` / #149.
Branch: `feat/s272-strict-raster`. Exclusive authority:
[AFTER-s263 rank 9](../next-fix-priority-after-s263.md).
`production_admitted=false`; `native_parity_proven=false`;
`thin_raster_cut_proved=false`. M0-02 stays pending; zero product obligations closed.

**Evidence-only diagnosis, not a completed residual pixel classification.**
The selected candidate is **countdown digit glyph edges (Sprite1810)**.
The prerequisite “after state admission” is unmet. No matched Godot image exists
for the s262 capture, so no pixel in this family can yet be attributed to edge
coverage, color rounding, filtering or another raster cause. No implementation
cut is proved or applied. This does not claim that the historical strict RGBA
failure is caused by this family.

## Bounded extension of locked evidence

[Input hashes](input-sha256.json) pin s262 artifacts and unchanged diagnostic and
validation tools. [Diagnosis](diagnosis.json) replays s262's own compressed raw
capture through its existing validator, checks archived build/source hashes and
receipt raw hash, and compares the full recomputed contract with the saved one.
This is portable raw evidence replay, not a fresh receipt or runtime attestation.
It revalidates 32,227 events and 61 native bitmap frames. No old receipt is resealed.

The extension rebinds all 61 saved scene rows to that capture's native display,
fight tick and callback ordinal, reconstructs every compared native field from
raw-replayed nodes, recomputes exact differences, and checks the saved summary.
The Godot half is the **locked s262 scene observation**, not a new current-tip
Godot execution. Its isolated callback adapter verified 68 outputs; this does
not bind the production scene countdown to the original callback history.

At tick13/display463/callback25, native tens/ones frames are 5/10 while the
scene has 1/1. Comparing their glyph edges would compare different glyph state.
Native camera X is -0.05 versus 0; scale is 189.994799804687 versus
189.99739990234374. Camera X differs in 12 rows and exact serialized scale in
61 rows. The report retains all field counts and per-row values. Scale values
are not rounded or classified wholesale as a raster or arithmetic defect.
Camera observations are whole-scene blockers, not proof that the root-level
HUD glyph inherits the game camera transform.

The locked scene has `imaging_allowed=false`, `images_written=0`, and missing
allocation/child-clock and registration-to-intro joins. Selected matching HUD
fields do not admit the complete visual phase. The analysis keeps admission
false even in a synthetic negative control with all selected values equal.
Historical s220 images cannot substitute for this capture's missing scene image.
The unchanged historical raw strict RGBA check remains **0/61 exact**; its result
is kept separate from s262 state admission and is not a new paired comparison.

## Next discriminator for this one family

1. In an encoded native capture and its own scene, establish timer/digit
   PlaceObject allocation and independent child clocks across registration,
   intro, callback, draw and encoding. Distinguish frame1 re-entry from birth
   with retained/replaced controls. A different no-encoding tape cannot supply
   this capture's lifetime or callback schedule.
2. Join those observed boundaries to the actual scene without resetting HUD
   state, transplanting a tape or assigning native transforms. Require exact
   selected state **and** complete visual phase admission. Keep unresolved
   camera boundary/order versus arithmetic differences explicit; do not round
   them away. Resolving these upstream obligations is not work claimed by s272.
3. Only then capture the corresponding scene image and inspect the selected
   digit edges at identical coordinates against its own native image. Bind the
   glyph frame, placement, transform and compositing state first. Record exact
   differing RGBA channels and edge/interior membership without offset searches,
   tolerant masks, image substitution or changing the full-frame strict gate.
   If wrong glyph/state remains, stop before raster attribution. A renderer cut
   needs a source-bound causal discriminator; spatial proximity to an edge alone
   does not prove an antialiasing algorithm defect.

Source-first boundary: s262 retains Sprite1810/1813 frame scripts and authored
PlaceObject/MOVE/removal facts in its source contract. Digit gotoAndStop and
frame1 stop are not implicit label-end exits. Native capture exists for the same
case, but the necessary full visual-state join does not. Tests assert observed
state and rejection of corrupted evidence, not invented rendering semantics.
No runtime mechanism changes are authorized by these findings.

## Reproduction and cost

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s272/diagnose.py --output /tmp/s272.json
PYTHONPATH=. python3 evidence/sampling-upgrade/s272/diagnose.py --output /tmp/s272-required.json --require-thin-raster # exit 1
PYTHONPATH=. python3 evidence/sampling-upgrade/s253/diagnose.py --output /tmp/s272-historical-strict.json --strict-rgba # exit 1
python3 -m unittest tools.tests.test_strict_raster_admission tools.tests.test_callback_visual_state tools.tests.test_countdown_phase_tape tools.tests.test_rgba_clock_diagnosis tools.tests.test_sampling_bitmap tools.tests.test_sampling_native
python3 tools/verify.py
python3 tools/check_handoff.py
/tmp/bvn-s27-venv/bin/python tools/validate_contracts.py
```

[Gate results](gates.json) record commands, actual exits and subprocess costs;
[project checks](project-checks.json) record integrity, handoff and contracts.
Diagnosis and all 54 focused tests pass; thin-raster requirement and historical strict
RGBA honestly exit1. Contracts are a consistency check, not behavioral proof.
[Session timing](session-timing.json) records measured elapsed work through
packaging; actual person-days remain unknown.

Zero new builds, exports, native captures, Godot launches or images. Capture cost
is zero: locked evidence already demonstrates the blocking prerequisite. Another
capture without a proved observation/join design would not isolate this family;
future capture cost remains unknown. No claim of completing the upstream ranks.

Only s272 evidence, its focused tests and requested tracking files change.
Ranks 1–8 and s254–s271 remain untouched. No tolerance changes, baseline
replacement, image substitution, threshold relaxation, strict validator edits,
renderer/gameplay rewrite, production adapter, merge or deployment.
