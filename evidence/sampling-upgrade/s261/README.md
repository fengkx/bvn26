# s261 — AFTER-s258 rank 3: AImain content clearing / identity

Baseline master `ef599670` / #138; branch `feat/s261-aimain-content-clearing`.
Exclusive authority: rank 3 in [the AFTER-s258 priority](../next-fix-priority-after-s258.md).
`production_admitted=false`; `native_parity_proven=false`; M0-02 remains pending.
**Evidence-only: mapping_fix_proved=false; zero product obligations closed.**

## Result and identity limitation

One bounded native capture reuses the locked s255/s231 input tape, selected
Yijiao P1 non-AI initCtrl lifetime and existing standalone display builder.
The observer samples every root after the authored unload until the first 0/0;
it stops at that boundary, retaining the ordinary first display sample as well.
The historical s255 tape lacks the intervening roots and independent controls,
so offline analysis cannot supply these observations. Historical evidence is unchanged.

| Boundary | Event sequence | Root period | Current/total frames | Source/token |
| --- | --- | --- | --- | --- |
| Before unload | 24 | 7 | 1/2 | retained |
| After unload returns | 29 | 7 | 1/2 | retained |
| Next root | 36 | 8 | 1/2 | retained |
| Following root, first zero | 44 | 9 | 0/0 | undefined |
| First display sample | 2950 | 437 | 0/0 | undefined |

Saved reference, named lookup and depth occupant agree at every boundary.
The parent token survives, while its frame changes from 1 at root8 to 2 at
root9. Source XML shows the same AImain placement record at parent frames1/2;
this rules out an authored new placement at that boundary, not an internal
player replacement during unload processing. The transition is bounded by
root8/9 observer sites (11399/11424 ms in this run), not proved at an exact
instruction or universally fixed delay. The synchronous-unload explanation
remains disproved.

Independent controls run before unload on a temporary root child, outside the
game tree, with explicit operations and no asynchronous callbacks. The child
is removed before ordinary display sampling. A plain-object token is kept
externally; no token is minted by the display collector for this test.

| Known operation | Saved reference == current slot | Current token == external token |
| --- | --- | --- |
| Retain same instance/content | true | true |
| removeMovieClip, then create same name/depth with a new token | true | false |
| Retain replacement instance, delete only its token property | true | false |

This independently validates the token comparison for intact retention versus
explicit replacement, **but falsifies its applicability after content clearing**.
Reference equality alone also fails the replacement control. The target loses
its token exactly when it becomes 0/0. Thus no independently validated
allocation-identity discriminator survives this target transition:
`identity_discriminator_valid_for_cleared_content=false`. The requested strong
identity prerequisite remains unmet, explicitly, rather than being substituted
with path equality or marker disappearance. Synthetic controls establish these
observability limits; they do not assert the player uses the same operations
for authored unload. No mapping fix follows.

Next discriminator: inspect native player allocation/lifecycle identity between
these exact root8/9 sites, with a positive retained-content-clear control and a
same-name/depth replacement control. Record the occupant allocation generation
before/after clearing and whether the old reference resolves to another object.
A stable slot/path, a missing property, or another AS2 `==` observation cannot
satisfy this. No debugger/engine allocation trace is claimed here.

## Source-first scope

1. Locked `fighter/yijiao#DefineSprite_455/frame_1/DoAction.as` retains the exact
   non-AI `gotoAndStop(1)` / `AImain.unloadMovie()` statements; observations only
   surround unload. Sprite3 frame1 is `stop()`, frame2 has no DoAction and places
   sensors. Source text and full slot records are in `diagnosis.json`.
2. AImain is new Sprite3 at depth1 in parent frame1, not a MOVE. Frame2 retains
   that placement. Parent/source XML hashes are verified against archived exports.
3. Frame1 stops; the non-AI branch unloads. There is no authored frame-zero label.
4. Tests assert captured boundary/control facts and reject missing roots,
   controls or duplicate observations. They do not bless a lifecycle mapping.
5. All 122 fight actor rows / 14 fields equal s255, including tick0. Input tape
   bytes are unchanged. This is not random-tape replay or native/Godot parity;
   complete raw events, including random reads and pre-fight timing, are retained.

Only isolated probe/evidence/tests and tracking are changed. No production
runtime, shared sampler/builder, collector, validator or contract is changed.
No 0→1 alias, unloaded exemption, broad binding, masks/camera, other AImain
families, gameplay change or relaxed threshold. Ranks1/2/4/5 and s254–s260 are
untouched; no merge or deployment.

## Gates and measured cost

One native launch: 8,290 events, one done, 61 display samples, no suffix trimming.
Receipt and diagnosis exit0; full display exit1 retains all 169 obligations.
All 59 focused tests pass. Input integrity, handoff and contracts pass; results are recorded in `gates.json`
and `project-checks.json`, with exact commands, exits and elapsed subprocess time.
Build: 11.933 seconds; capture: 30.239 seconds. An initial sandbox process-inspection
failure launched no player; the authorized escalated retry completed. See
`capture-cost.json` and `native-build.json`. No person-days are inferred.

## Reproduce

Portable diagnosis and tests need no player or external XML cache:

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s261/diagnose.py --output /tmp/s261-diagnosis.json
python3 -m unittest tools.tests.test_aimain_content_clearing tools.tests.test_aimain_unload_identity tools.tests.test_display_source_frame_diagnosis tools.tests.test_sampling_native tools.tests.test_sampling_display tools.tests.test_display_completion_default tools.tests.test_import_guards
python3 tools/verify.py
python3 tools/check_handoff.py
```

For retained receipt/full display gates, extract `native-build.tar.gz` into
`/tmp/bvn-s261-r01-build`, decompress `native-capture.log.gz` into
`/tmp/bvn-s261-r01-capture/native.log` and copy `native-receipt.json` there as
`receipt.json`. Restore the XML paths in `source-exports.json` from s30's
`source-exports.tar.gz` and s233's `yijiao-source-export.tar.gz`. Run `gates.json`
commands with pinned probe sources and `/Volumes/Flash Player/Flash Player.app`.
Do not reseal historical receipts. `artifact-sha256.json` pins archived inputs.

Optional fresh capture (new directories and run ID; existing serialized capture lock):

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s261/build_probe.py --ffdec /tmp/bvn-s66-tools/ffdec/ffdec.jar --output /tmp/bvn-s261-new-build --run-id s261-yijiao-new
mkdir -p /tmp/bvn-s261-new-capture
python3 -m tools.sampling_native --case evidence/sampling-upgrade/s231/yijiao__attack__neutral__ground__near.json --build /tmp/bvn-s261-new-build --trace /tmp/bvn-s261-new-capture/native.log --receipt /tmp/bvn-s261-new-capture/receipt.json --timeout 180 --allow-window-activation
```

Recapture creates new evidence, never replaces the pinned r01 record.
