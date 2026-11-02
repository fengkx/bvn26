# s308 — AFTER-s299 rank #9 strict digit-edge residual (evidence-only)

Base: origin/master `bcc4a7aa1332f2162bbab14d7e55eb99591f0141` (s307 #185).
Branch: `feat/s308-strict-raster`.
Exclusive authority: [AFTER-s299 rank #9](../next-fix-priority-after-s299.md).
`production_admitted=false`; `native_parity_proven=false`; M0-02 pending.
**Honest-unproved: complete same-capture state admission is absent.**
Zero product obligations closed.

## Bounded result

[diagnose.py](diagnose.py) verifies [input pins](input-sha256.json), reproduces
all of the locked [s299 diagnosis](../s299/README.md), and requires exact equality.
Its existing s281/s272/s262 and s274 read-only checks retain raw provenance.
This is historical evidence replay, not new execution of AFTER-s299 ranks 1–8,
a new capture, or current-tip Godot evidence. No admission repair is attempted.

[diagnosis.json](diagnosis.json) retains all 61 boundary identities (run, raw
hash, tick, display, callback firing) and retains explicit per-boundary unknowns
for source-bound edge membership, interior membership, exact RGBA residuals
and differing channels. **Null means unmeasured, not zero.** This cut adds
per-boundary capture/classification eligibility and the first unmet gate:
complete same-capture state. All 61 captures are blocked before imaging.
Every row still has a digit mismatch and other selected scene mismatch. Tens differ in 57 rows,
ones in 55, camera scale in 61 and camera X in 12. Tick13/display463/callback25
has native digit frames 5/10 versus scene 1/1.

The retained s262 capture has 32,227 events, 68 callbacks and 61 native bitmap
frames, but zero same-capture Godot images. The distinct s274 capture has 26,828
events, 63 callbacks, 57 encoding windows and four natural entry joins. Its
local lifetime admission cannot supply s262 scene admission or pixel payloads.
Historical s253 RGBA remains historical evidence; it is not a replacement pair.
No boundary is eligible for this cut's paired capture. Even selected-field
equality would not establish full visual phase.

## Ordered gates and blocker

| Requirement | Exit | Code | Result |
| --- | --- | --- | --- |
| Evidence audit | 0 | `S308_DIAGNOSIS_OK` | Locked diagnosis reproduced only |
| Complete same-capture state | 1 | `S308_STATE_ADMISSION_UNPROVED` | Unproved |
| Corresponding paired scene | 1 | `S308_PAIRED_SCENE_UNPROVED` | Blocked before capture |
| Exact source-bound edge/interior RGBA | 1 | `S308_STRICT_RASTER_UNPROVED` | Not measured |

The missing prerequisite includes independent child-clock/allocation and
registration/intro/scene joins. No paired capture, classification or renderer
causation is claimed. The fixed-evidence diagnostic is intentionally not an
accepting trace schema: changing flags, rows or image counts requires new
independent analysis and cannot promote this slice to proved.

The next discriminator requires complete state admission outside this cut.
Only after that admission, capture the corresponding scene and bind the source
glyph/frame, PlaceObject/MOVE lifetime, placement, transform, compositing and
capture boundary. Then classify unchanged exact RGBA at identical coordinates
with source-bound edge/interior membership and retain exact differing channels.
A pixel's proximity to an edge does not establish rasterizer causation. Camera
differences do not prove HUD camera inheritance or a rounding defect.

## Source-first and scope

The five source-first answers remain locked to
[s262's source contract](../s262/source-contract.json) and
[s274's audit](../s274/README.md): Sprite1810 frame1 stops, frames2–10 have no
DoAction; Sprite1813 places a new ones digit at frame1/depth3 and removes it at
frame10. Callback gotoAndStop differs from actual child entry; frame1 reentry
is not allocation identity. No label end implies return. Source invariants and
historical same-input observations remain distinct from full scene admission.
These incomplete answers authorize neither runtime changes nor product completion.

The diagnostic and this report enforce: no admission repair, tolerance, offset
search, image substitution, camera rounding or renderer rewrite. No game/,
scripts/, runtime, contracts, shared sampler/threshold/validator changes. No edits
under s254–s307. AFTER-s299 ranks 1–8 are not executed. Only s308 and proportionate
tracking/manifest updates change. No builds, player/Godot launches, captures,
images, merge or deployment.

## Reproduce and validation

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s308/diagnose.py --output /tmp/s308.json
# Each independently expects exit 1:
PYTHONPATH=. python3 evidence/sampling-upgrade/s308/diagnose.py --output /tmp/s308-state.json --require-state-admission
PYTHONPATH=. python3 evidence/sampling-upgrade/s308/diagnose.py --output /tmp/s308-pair.json --require-paired-scene
PYTHONPATH=. python3 evidence/sampling-upgrade/s308/diagnose.py --output /tmp/s308-raster.json --require-thin-raster
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s308 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s299 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s290 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s281 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest tools.tests.test_strict_raster_admission tools.tests.test_encoded_digit_lifetime tools.tests.test_callback_visual_state tools.tests.test_countdown_phase_tape tools.tests.test_rgba_clock_diagnosis tools.tests.test_sampling_bitmap tools.tests.test_sampling_native
python3 tools/verify.py
python3 tools/check_handoff.py
```

[Gates](gates.json), [project checks](project-checks.json),
[scope audit](scope-audit.json), [manifest audit](manifest-audit.json) and
[session timing](session-timing.json) record actual outcomes and measured costs.
Initial reading/design and person-days remain unknown. No contract or Godot
check applies to this evidence-only change. Tests protect evidence rejection
boundaries, including identity changes at every tick, hidden differences,
image substitution and invented zero residuals; they do not prove pixel parity.

Validation: **100 tests pass** (11 focused, 9 retained s299, 8 retained s290,
7 retained s281 and 65 retained tool tests). Integrity, handoff and diff checks
pass. All three proof requirements retain exit 1; audit exit 0 proves only
reproducibility of the locked diagnosis.
