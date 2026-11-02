# s290 — AFTER-s281 rank #9 strict raster (honest-unproved)

Base: `origin/master` `42bc2c690e83dfeff12367fa67bf944bf4f56366` (#167, s289).
Branch: `feat/s290-strict-raster`. Exclusive authority:
[AFTER-s281 rank #9](../next-fix-priority-after-s281.md).
`production_admitted=false`; `native_parity_proven=false`; M0-02 pending.
Evidence-only; zero product obligations closed.

**Full same-capture state admission and the matched scene image pair remain
absent.** Both proof requirements exit 1 with `S290_STRICT_RASTER_UNPROVED`.
Digit-edge/interior RGBA residuals are null (unmeasured), not zero. The candidate
family is countdown digit glyph edges (Sprite1810), not a diagnosed renderer fault.

## Evidence and bounded result

[diagnose.py](diagnose.py) verifies [input pins](input-sha256.json), recomputes
locked [s281](../s281/README.md) through its existing s272/s262 and s274 raw
checks, and requires exact equality with the retained diagnosis. No old receipt
is repaired. The historical replay is not current-tip Godot execution or a new
capture. Replaying these prerequisites does not execute another AFTER-s281 rank.

The new [boundary audit](diagnosis.json) enumerates all 61 s262 state pairs,
retaining run ID, raw hash, tick, display and callback firing at every boundary.
It separates glyph differences from other selected scene differences and records
pixel classification as `not_measured` for each row:

- At least one digit differs at every tick 0–60: tens in 57 rows, ones in 55.
- Other selected scene state differs at every tick: exact camera scale in 61
  rows and camera X in 12. No selected-state-equal row is available to nominate
  for pixel capture; even equality would not prove full visual phase.
- Tick13/display463/callback25 has native digit frames 5/10 versus scene 1/1.
  Camera facts do not establish that HUD glyphs inherit the game camera, or
  identify a rounding defect.
- s262 has 32,227 revalidated events, 68 callbacks and 61 native bitmap frames,
  but zero same-capture Godot images. s274 has a distinct run/hash, 26,828 events,
  63 callbacks, 57 encoding windows and four natural entry joins; its local
  lifetime admission supplies neither scene admission nor pixel payloads.

The ordered gates distinguish state **unproved**, matched scene images
**blocked**, and exact edge/interior RGBA **not measured**. Historical s253 strict
RGBA is checked separately with the unchanged checker; it is not substituted
for the absent s262/s274 pair and cannot classify this candidate family.
No accepting trace schema, synthetic positive proof, raster mask or comparator
is introduced. Tests exercise rejection of altered pins, incomplete/reordered
rows, hidden differences, changed boundaries, image/proof promotion and invented
zero residuals. Retained tests cover cross-capture substitution and the fact that
matching selected fields cannot prove missing phase.

## Blocker and next discriminator

The locked source-first references remain [s262's source contract](../s262/source-contract.json)
and [s274's audit](../s274/README.md): Sprite1810 frame1 stops, frames2–10 have
no DoAction; Sprite1813 places a new ones digit at frame1/depth3 and removes it
at frame10. Callback gotoAndStop and actual child entry are distinct observations;
frame1 reentry does not prove a new allocation. No label end is invented as a
return. Source invariants and same-input native observations are retained, but
independent child-clock/allocation and registration/intro/scene joins remain
incomplete. The five questions therefore do not authorize a runtime change.

Before pixel work, one capture must establish complete state admission and its
own corresponding scene image. Bind glyph/frame, PlaceObject/MOVE lifetime,
placement, transform, compositing and capture boundary. Only then classify exact
unchanged RGBA at identical coordinates using source-bound edge/interior
membership, retaining exact differing channels. Proximity to an edge alone
would still not prove rasterizer causation. That future experiment is unexecuted;
upstream admission repair is outside this slice.

No tolerance, offset search, image substitution, assumed camera rounding,
renderer rewrite, HUD reset or cross-run callback transplant. No new build,
player/Godot launch, capture or image. Only s290 and proportionate tracking files
change; s254–s289, game/, scripts/, runtime, contracts, shared samplers,
thresholds and validators remain unchanged. AFTER-s281 ranks 1–8 are not executed.
No merge or deployment.

## Reproduce

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s290/diagnose.py --output /tmp/s290.json
PYTHONPATH=. python3 evidence/sampling-upgrade/s290/diagnose.py --output /tmp/s290-state.json --require-state-admission # expected exit 1
PYTHONPATH=. python3 evidence/sampling-upgrade/s290/diagnose.py --output /tmp/s290-raster.json --require-thin-raster # expected exit 1
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s290 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s281 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest tools.tests.test_strict_raster_admission tools.tests.test_encoded_digit_lifetime tools.tests.test_callback_visual_state tools.tests.test_countdown_phase_tape tools.tests.test_rgba_clock_diagnosis tools.tests.test_sampling_bitmap tools.tests.test_sampling_native
PYTHONPATH=. python3 evidence/sampling-upgrade/s253/diagnose.py --output /tmp/s290-historical.json --strict-rgba # expected exit 1
python3 tools/verify.py
python3 tools/check_handoff.py
```

[Gates](gates.json), [project checks](project-checks.json),
[scope audit](scope-audit.json), [manifest audit](manifest-audit.json) and
[timing](session-timing.json) retain outcomes and measured check costs.
Initial reading/design and future capture costs are unmeasured; person-days
remain unknown. No Godot or contract checks apply to this evidence-only change.

Validation: **80 tests pass** (8 new, 7 retained s281, 65 retained tool tests).
Diagnosis, input integrity, handoff and diff checks exit0. Both s290 proof
requirements and historical strict RGBA exit1 as expected; no pixel proof.
