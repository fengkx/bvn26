# s362 — AFTER-s353 rank #9: Strict digit

Base: `24282a2205ea7f024980834585c8b7b694bc3fe5` (s361 #239 squash).
Branch: `feat/s362-strict-digit`. Authority: [unchanged rank #9](../next-fix-priority-after-s353.md).
Ranks 1–8 delivered; no later ranks or re-ranking. Evidence-only delivery.
`production_admitted=false`; `native_parity_proven=false`; M0-02 pending.
Zero product obligations closed.

## Independent route and result

[Raw derivation](derive_digit_witnesses.py) takes the receipt-hashed decompressed
s262 capture directly, brackets `s262_begin/visual/end`, and joins the recorded
scene by exact **tick, display and callback firing**, with the capture run ID
checked on every event. It does not consume s353's boundary inventory, s272's
difference summaries, camera comparisons or the shared admission validator.
For each boundary it selects the first contradictory digit in a fixed tens/ones
order, then resolves the two source frames through the retained Sprite1810
PlaceObject character mapping. No frame or shape is guessed from a glyph image.

[61 witnesses](digit-witnesses.json) each retain the raw line, event sequence,
instance path, depth, source frame and shape IDs. **All 61 boundaries have a
digit-frame contradiction independently of camera precision.** At tick0,
display450, firing14, raw line/event3041 reports tens frame7 (source shape1806)
while the recorded scene has frame1 (shape1800). The line numbering is for the
decompressed UTF-8 log. These are source-frame contradictions, not measured
edge coverage, RGBA differences or proof of current loaded instance identity.

This is a new, independently reproducible negative derivation from historical
bytes, **not a new native observation or newly repaired prerequisite**. The
61 rejected boundaries and zero scene pairs were already known. Full locked
s353 replay remains separate retained validation and is compared in its entirety.
No prior proof is presented as new runtime or pixel progress.

Complete same-capture admission remains absent; **no corresponding scene capture
or edge/interior RGBA classification is authorized yet**. No builds, launches,
new captures or images. Exact edge/interior residuals and unmeasured membership
remain null, not zero. Equal digit frames would not prove lifetime, registration,
intro, compositing or complete visual phase; the negative-only route never admits
any input, including the equal-digit test mutation. No positive admission schema
or replacement shared validator is introduced.

## Gates and reproduction

```sh
PYTHONDONTWRITEBYTECODE=1 python3 evidence/sampling-upgrade/s362/derive_digit_witnesses.py > /tmp/s362-witnesses.json
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 evidence/sampling-upgrade/s362/diagnose.py --output /tmp/s362.json
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s362 -p 'test_*.py'
python3 tools/verify.py
python3 tools/check_handoff.py
```

Base diagnose expects **exit 0**, with both admission flags false. Each of
`--require-state-admission`, `--require-paired-scene`, `--require-thin-raster`
expects **exit 1**, as does their combination. The first unmet gate remains
complete same-capture state admission. [Gates](gates.json) and
[checks](project-checks.json) record actual exits, commands and measured time.
Tests cover wrong runs, display/callback substitution, duplicate/missing/truncated
boundaries, unknown source frames, independence from camera/difference summaries,
and refusal to infer admission from equal digits. Retained s353/s344 and shared
raster/sampling tests run unchanged. No Godot/contract changes require additional
runtime or contract testing.

[Input pins](input-sha256.json) cover every s353 file, authority and direct raw
route inputs. [Route pins](route-sha256.json) bind the derivation and its result.
[Scope audit](scope-audit.json) enforces new s362 plus minimal tracking updates
only; game, scripts, runtime, contracts, shared tools and s254–s361 remain unchanged.
[Manifest audit](manifest-audit.json) records reviewed tracking hash updates.
[Artifact index](artifact-sha256.json) pins all package files except itself.
[Timing](session-timing.json) records the implementation/check interval, not
person-days. New tool and input paths are repo-relative; the old receipt's trace
path is used only to retrieve its hash, never to require that temporary file.

## Source-first boundary

1. Retained [source contract](../s262/source-contract.json): Sprite1810 frame1
   `stop()`; frames2–10 have no DoAction. The observer's `_currentframe` field
   order is pinned in [observer.as](../s262/observer.as).
2. Sprite1813 places new ones at frame1/depth3 and removes it at frame10;
   Sprite1810 frame1 places shape1800, frames2–10 MOVE/replace to1801–1809.
   This static map is not independent live allocation/lifetime proof.
3. Callback gotoAndStop is not actual child-entry proof; no label end is treated
   as return or stand. No behavior is changed.
4. Tests assert raw/source and rejection invariants, not invented pixel outcomes.
5. Historical same-input records remain insufficient for full scene admission;
   there is no fresh original/candidate same-input capture in s362.

Next, only after complete same-capture admission outside this cut, capture that
corresponding scene with glyph/source frame, placement/MOVE lifetime, transform,
compositing and boundary identity, then classify unchanged exact RGBA at identical
coordinates with source-bound edge/interior membership and differing channels.
No admission repair, tolerance, offset search, substitution, camera rounding or
renderer rewrite. Only this evidence delivery closes; rank #9's live experiment
and product acceptance remain unproved. Draft PR only; no ready, merge or deploy.

Validation: **90 tests pass**; verify.py, check_handoff.py and whitespace checks
exit 0. Expected proof failures remain exit 1; no pixel/product acceptance.
