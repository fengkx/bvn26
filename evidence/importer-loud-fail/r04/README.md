# Frame-call and cached-build obligations, r04 (2026-10-23)

Draft PR #48 remains blocked. This checkpoint closes selected call/argument
silent-drop paths and prevents cached fighter AI from bypassing their errors.
It does not complete the exhaustive AS/clip-action audit or filter fidelity work.
Production runtime, generated gameplay data, game/ and scripts/ are unchanged.

## Implemented and newly exposed

- `_root.shunbuxg(_parent)` now compiles through the existing source-verified
  `addChildXG(player,"XG_rush",0,0)` wrapper into a hashed child-effect event.
  `XG_rush` has no shipped generated asset yet. Cached AI has not been replaced;
  this is compiler handling, not a claim that the missing visual is fixed.
- `shine()` and literal RGB24 `shine(color)` compile to the existing screen-flash
  event. Dynamic/unsupported color arguments fail. This reveals dropped colored
  flashes in Deidara (303095), Konan (16409859), and other source frames.
- Exact single-field equality branches containing `stop()` or `play()` compile
  through the existing conditional-frame operation. For example, Deidara sprite
  542 frame 942's `if(sw == true) { stop(); }` was previously omitted.
- Uncompiled self/child/parent playhead calls and unsupported shine/shunbuxg
  arguments now fail with SWF, sprite, frame, line and construct. Supported
  conditional blocks and the existing exact Byakuya exception retain their scope.
- Offline compilation emits frame-call hashes keyed by SWF hash and body sprite.
  The build checks every fighter AI cache against these obligations, including
  source identity, missing catalog entries, changed/deleted/extra calls, and
  explicit compilation errors. Even a matching cache fails if a referenced child
  effect asset is missing. The new gate and catalog ship through the existing
  Vercel/staging input path. It needs no Flash interpreter or source scripts in
  production. It checks calls only; this is not full cached-state validation.

The 26 shipped fighter contexts now compile 21 / reject 5. Rejections are:

| Source | Sprite / frame | Construct |
|---|---|---|
| daitu | 458 / 1309 | `_parent.gotoAndStop(2)` |
| minren | 764 / 1382 | `_parent.gotoAndStop(2)` |
| rukia | 533 / 141 | `gotoAndPlay(130)` |
| Sasuke | 603 / 1232 | `_parent.gotoAndStop(2)` |
| yihu | 638 / 1055 | `_parent.gotoAndStop(2)` |

These real missing behaviors are hard errors, not allowlisted. All 21 compilable
contexts differ from their cached frame-call sequences, so **0/26 caches pass**.
The exact changed calls/frames are in frame-call-audit.json. Build fingerprint
validation now rejects the known unsupported Yihu frame instead of accepting
its stale cache (fingerprint.log). No manifest was regenerated around this gate.
The old runtime/content fingerprints remain unchanged, not newly certified.

The script inventory records 1,438 candidate lines across retained bundles with
SWF/script hashes and line numbers. Candidates include nested numeric controls
that may already have native owners, and declarations; they are review inputs,
not 1,438 confirmed bugs. Frame-1 functions, arbitrary calls/expressions and
clip-action ownership are still incomplete. No new harmless exception was added;
Byakuya 631/985 remains exactly hash/form pinned.

## Source-first scope and checks

1. shared-source.json retains the original main frame-8 shine/shunbuxg functions
   and their hashes. The new tests point to actual stopped conditional source
   and wrapper arguments, not inferred gameplay behavior.
2. Compiler output preserves authored frame/line FIFO and wrapper offsets. No
   placement lifecycle, MOVE inheritance or enterFrame scheduling was changed.
3. Numeric self/parent jumps without a supported consumer are rejected. They are
   not converted to guessed labels. Existing runtime supports the generated
   conditional play/stop operations; no runtime implementation was changed.
4. Mutation tests cover numeric/expression goto, child stop/play, malformed
   service arguments, conditional stop compilation and cached call omissions,
   missing catalogs, source mismatches and explicit error records.
5. No new native player capture was made in r04. New compiler event handling is
   not end-to-end native acceptance; missing assets and stale caches block it.
   GPU comparisons reuse unchanged r03 native samples and remain strict.

Three older compiler unit tests accidentally treated full unimplemented
transformation timelines as accepted inputs. They now first assert the real
full-slice error, then use an explicit frame-1 plus target-frame unit slice for
FIFO assertions. Production timelines and assertions were not relaxed.
The player-visual smoke test now creates a fresh input event for reversal and
waits another process frame for queued teardown; assertions are unchanged.
Initial teardown errors and the clean rerun are both retained under godot/.

## Results

- Python: 380 run, 378 passed, 2 skipped; python-tests.log.
- GPU: 7/7 asserted subsets pass; blur 242/242 / 37,280 alpha samples, blend 38/38.
- Godot smoke: final 4/4 pass. The first player-visual attempt printed its success
  marker but had a resource teardown error; that attempt is not counted green.
- Color: 3/5 canonical groups exact; Matrix100 / Glow→Matrix still have 64/128
  differing channels, maximum 1. Order: 2/4 exact; both Glow cases differ by one
  channel at maximum 1. Both full comparators still exit 1. No filter change here.
- Real component images: not recaptured; r03 remains 9/54 exact, clocks 4,242/4,242.
- All 62 locked SWFs rescanned: the same 34 unsupported placements, every location
  in locked-swf-audit.json. All 88 cached nested-control checks pass. The 34 errors
  remain mode 7 Kenshin (1), mode 13 minrenx (1)/qilabi (30)/main (1), and main
  sprite 1504 frame 1 DropShadow (1). None was allowlisted or silently accepted.
- Protected function remains original: PROTECTED_FUNCTION_OK, 1,086 bytes/hash.
- Roster replay: 227/227, 130,334 states match; roster-report.json / roster.log.
  Integrity, handoff and contracts (6 schemas / 6 examples) pass; see their logs.
  The roster uses existing cached gameplay data, not the rejected
  newly compiled contexts; passing it cannot certify missing source behavior.
- Runtime fingerprint/build acceptance: **FAIL by design**, with the source error
  above. Shipped import acceptance is **FAIL**; this PR must stay Draft.

## Reproduce

```sh
python3 tools/importer/audit_frame_calls.py --output "$OUT/frame-call-audit.json"
# Catalog updates are explicit review inputs, never a build-time auto-acceptance:
python3 tools/importer/audit_frame_calls.py --output "$OUT/frame-call-audit.json" \
  --write-requirements "$OUT/frame_call_requirements.json"
python3 tools/build_online_manifest.py --check
python3 tools/importer/audit_importer.py --ffdec "$FFDEC" --output "$OUT/locked-swfs.json"
python3 -m unittest discover -s tools/tests
python3 tools/test_importer_roster.py --godot "$GODOT" --output "$OUT/roster"
```

Both audits and the fingerprint check currently exit 1 for real blockers.
[Filter commands](../../../tools/probes/flash_filters/README.md) still apply.
Remaining work: exact colors/real-component pixels, native XG_rush asset and
source-call acceptance, numeric/parent goto, exhaustive AS/clip-action ownership,
the 34 placement errors and complete shipped import acceptance. No new ports,
merge, deployment or intentional stability deviation.
