# s353 — AFTER-s344 rank #9 strict digit residual

Base: origin/master `037214a4c5527518a6c3d437da81744b58e7455a` (s352 #230).
Branch: `feat/s353-strict-digit-residual`.
Authority: [AFTER-s344 rank 9](../next-fix-priority-after-s344.md).
**Evidence-only, honest-unproved.** `production_admitted=false`;
`native_parity_proven=false`; M0-02 pending; zero product obligations closed.
Only AFTER-s344 rank 9 is executed. Ranks 1–8 were delivered as s345–s352 and remain closed. This is the final rank of the unchanged authority table; no re-ranking is performed.

## Result and evidence boundary

The prerequisite is still absent in locked s344: all **61 boundaries** fail
complete same-capture state admission, with zero same-capture Godot image pairs.
Consequently no corresponding scene capture or exact source-bound edge/interior
RGBA classification was attempted. This is delivery of a blocked evidence cut,
not completion of its proposed pixel experiment. No new independent runtime
observations were obtained. There is no new measured residual or rasterizer cause.

[diagnose.py](diagnose.py) pins the authority and every s344 artifact, replays the
entire locked s344 diagnosis (including its transitive raw checks), requires full
equality, and reuses its existing boundary rejection guards. This avoids a new
admission policy or copied shared validator. [diagnosis.json](diagnosis.json)
retains every run/raw hash/tick/display/callback identity, mismatch and ordered
gate. The s353 wrapper/tests establish handoff integrity and rejection behavior
only; reproduction of prior proof is **retained validation, not new progress**.
There is no accepting live-input schema in this fixed-evidence diagnostic.

Historical facts retained from [s344](../s344/README.md): tens differ on 57 rows,
ones on 55, camera scale on 61 and camera X on 12. Tick13/display463/callback25
has native digit frames 5/10 versus scene 1/1. Every boundary has glyph and other
selected-state mismatches. The s262 capture contains 32,227 events, 68 callbacks
and 61 native bitmap frames; these do not supply corresponding Godot images.
The distinct s274 entry/lifetime capture cannot fill the same-capture gap.
Earlier s253 RGBA cannot substitute for the missing pair. These are historical
observations, not observations of this worktree's runtime.

Per-boundary source-bound edge/interior membership, exact RGBA residuals and
differing channels remain **null (unmeasured), not zero**. Complete visual-phase
admission is stronger than equality of selected fields. Neither a nearby edge
nor a camera difference establishes rasterizer causation or HUD camera inheritance.

## Ordered gates

| Mode | Exit | Meaning |
| --- | --- | --- |
| Base diagnosis | 0 | Retained evidence reproduced; admission and parity false |
| `--require-state-admission` | 1 | `S353_STATE_ADMISSION_UNPROVED` |
| `--require-paired-scene` | 1 | `S353_PAIRED_SCENE_UNPROVED` |
| `--require-thin-raster` | 1 | `S353_STRICT_RASTER_UNPROVED` |

The first unmet gate for all 61 boundaries is complete same-capture state.
The existing independent child-clock/allocation and registration/intro/scene
joins are not supplied by this cut. No admission repair is authorized here.
Only after complete admission outside this cut may the corresponding scene be
captured, binding glyph/source frame, PlaceObject/MOVE lifetime, placement,
transform, compositing and capture boundary. Then unchanged exact RGBA at
identical coordinates can be classified with source-bound edge/interior membership
and exact differing channels. No tolerance, offset search, image substitution,
camera rounding or renderer rewrite is allowed.

## Source-first and scope

The source-first answers remain incomplete and locked to
[s262 source contract](../s262/source-contract.json) and [s274 audit](../s274/README.md):
Sprite1810 frame1 stops; frames2–10 have no DoAction. Sprite1813 places a new ones
digit at frame1/depth3 and removes it at frame10. Callback gotoAndStop is not actual
child entry; frame1 reentry is not allocation identity; label end does not imply
return. Historical same-input evidence is distinct from full scene admission.
No runtime mechanism is changed or claimed complete.

Zero builds, player launches, captures and new images. Ranks 1–8 are not executed.
The authority table and every s254–s352 tree remain unchanged. Allowed changes
are this tree and minimal STATUS/SAMPLING_UPGRADE/tasks/manifest tracking only.
No game/, scripts/, runtime, contracts or shared sampler/threshold/validator edits.
No merge, ready-for-review transition or deployment.

## Reproduction and validation

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 evidence/sampling-upgrade/s353/diagnose.py --output /tmp/s353.json
# Each proof flag independently expects exit 1:
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 evidence/sampling-upgrade/s353/diagnose.py --output /tmp/s353-state.json --require-state-admission
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 evidence/sampling-upgrade/s353/diagnose.py --output /tmp/s353-pair.json --require-paired-scene
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 evidence/sampling-upgrade/s353/diagnose.py --output /tmp/s353-raster.json --require-thin-raster
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s353 -p 'test_*.py'
python3 tools/verify.py
python3 tools/check_handoff.py
```

[Gates](gates.json) and [project checks](project-checks.json) retain commands,
actual exits and measured subprocess times, including s344 and retained strict-raster/sampling tests. Local tests check the entire handoff,
identity substitution at every boundary, non-boundary alteration, invented proof
and the CLI exits. They are not synthetic positive pixel proof. No contract or
Godot checks apply because neither contracts nor Godot implementation changes.

[Scope audit](scope-audit.json) compares with the full base SHA.
[Manifest audit](manifest-audit.json) records reviewed tracking hash updates.
[Input hashes](input-sha256.json) pin retained inputs; transitive raw hashes are
checked during replay. [Artifact hashes](artifact-sha256.json) cover every slice
file except the index itself. [Session timing](session-timing.json) records the
measured packaging interval; initial reading/design and person-days are unknown.

Validation: **77 tests pass**; base exit 0; three proof gates exit 1; verify.py, check_handoff.py and whitespace checks exit 0. These checks establish retained evidence integrity and rejection behavior only, not pixel or product acceptance.
