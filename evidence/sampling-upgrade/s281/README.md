# s281 — Strict digit-edge raster residual (unproved)

Base: master `7101756b6e5e0ccec00ef2bccfb72c3e6446bb7e` / #158.
Branch: `feat/s281-strict-raster`. Exclusive scope:
[AFTER-s272 rank 9](../next-fix-priority-after-s272.md).
`production_admitted=false`; `native_parity_proven=false`.
M0-02 remains pending; zero product obligations closed.

**Evidence-only. Complete same-capture state admission is still missing, so no
matched scene is captured and no edge/interior raster residual is classified.**
The candidate remains countdown digit glyph edges (Sprite1810). This is not a
claim that digit rasterization caused the historical full-frame RGBA failure.

## What this slice establishes

[Diagnosis](diagnosis.json) replays the locked s272 and s274 diagnostics from raw
captures, verifies their existing source/build/receipt checks and requires exact
equality with the saved diagnoses. [Input hashes](input-sha256.json) pin the
read-only inputs. No receipt is resealed and no new execution is attested.

| Evidence | Revalidated observation | Why it cannot admit rank 9 |
| --- | --- | --- |
| s262 via s272 | 32,227 events, 61 native bitmap frames, 68 callbacks | Wrong glyph state, incomplete visual phase, zero same-capture Godot images |
| s274 | 26,828 events, 63 callbacks, 57 in-memory encoding windows, four natural target-entry joins | Local experiment admission only; no scene join, no pixel payloads |
| s253 historical strict comparison | 0/61 exact full frames, reproduced separately by its unchanged checker | Historical pair has unproved phase; cannot replace images for either later capture |

The new audit binds each run ID and raw capture hash separately. The s274 lifetime
observation does not repair s262 by transitivity: its callback history and capture
identity differ. Reading and replaying s274 is prerequisite diagnosis only, not
implementation or extension of rank 2. Ranks 1–8 are not implemented here.

The s262 scene has digit differences in 57 tens rows and 55 ones rows. At
fight tick13/display463/callback25, native tens/ones frames are 5/10, versus 1/1
in the locked scene. Camera X differs in 12 rows and exact serialized scale in
61 rows. These camera facts block whole-scene admission; they do not establish
that root-level HUD glyphs inherit the game camera or prove a rounding defect.
Neither the old scene observations nor s274 are current-tip Godot execution.

The report records **null**, not zero, for edge and interior residuals: no
admitted image pair exists to measure them. Synthetic negative controls reject
cross-capture relabeling, substituted images, local-to-scene admission promotion
and production/parity claims. Existing tests retain the stronger check that even
matching all selected fields cannot prove the missing visual phase.

## Boundary and next discriminator

The source-first references remain the locked [source contract](../s262/source-contract.json)
and [s274 source/build audit](../s274/README.md): Sprite1810 frame1 stops,
frames2–10 have no DoAction; Sprite1813 places a new ones digit at frame1/depth3
and removes it at frame10; callback gotoAndStop is separate from observed actual
frame entry. A retained frame1 re-entry is not a new birth. No runtime mechanism
is changed, and missing independent child-clock/allocation and registration-to-
intro joins are not guessed.

Before this family can be classified, one capture must supply complete state
admission and its own corresponding scene image. Bind glyph frame, placement,
transform, compositing and capture boundary first. Then compare unchanged RGBA
at identical coordinates and report exact differing channels with source-bound
edge/interior membership. Spatial proximity alone would still not prove a
renderer cause. This future step is unexecuted: upstream repair falls outside
s281. No tolerance, offset search, image substitution, camera-rounding assumption,
renderer rewrite, HUD reset, callback transplant or relaxed strict gate.

## Reproduce and validate

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s281/diagnose.py --output /tmp/s281.json
PYTHONPATH=. python3 evidence/sampling-upgrade/s281/diagnose.py --output /tmp/s281-required.json --require-thin-raster # exit 1
PYTHONPATH=. python3 evidence/sampling-upgrade/s274/diagnose.py --output /tmp/s281-state.json --require-state-admission # exit 1
PYTHONPATH=. python3 evidence/sampling-upgrade/s253/diagnose.py --output /tmp/s281-rgba.json --strict-rgba # exit 1
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s281 -p 'test_*.py'
python3 tools/verify.py
python3 tools/check_handoff.py
```

[Gate results](gates.json) include the focused and retained regression commands,
actual/expected exits and measured subprocess times. [Project checks](project-checks.json)
record verify/handoff. [Scope audit](scope-audit.json) and
[manifest audit](manifest-audit.json) record the reviewed changes and tracked hash
updates. [Session timing](session-timing.json) records actual elapsed time through
packaging, not person-days or future capture estimates.

Zero new builds, native captures, Godot launches or images. A capture before the
known state admission gap is resolved would not isolate a raster residual.
Only new s281 files and the four authorized tracking files change. All
s254–s280 evidence, locked inputs, runtime contracts, shared samplers, thresholds
and validators remain unchanged. No merge, deployment or production readiness.
