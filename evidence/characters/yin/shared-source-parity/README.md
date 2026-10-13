# Shared source-event parity fixes

This supplements PR #11's bitmap-mask work. The retained input is the user's
117-case Gin investigation (`bvn2_6-pr5-sample/verification/analysis.json`).
No source SWF, input window, random tape, reference state or comparison tolerance
was changed. Full raw Flash events, build identities and fixtures are retained in
`references.tar.gz`; `suite-index.json` records the archive hash and the original
13 failures. The archive additionally contains 19 existing Chad/Rukia/Lee cases.

## Source-first findings

| Rule | Authored scripts / placement and exit | Invariant and same-input evidence |
| --- | --- | --- |
| Container scale is separate from BODY direction | Gin `DefineSprite_435/frame_407/DoAction.as` changes `_parent._xscale` and warps beside the opponent. Frame 411 places movement controller 16 at depth 36; it leaves at 416. Frame 421 places the retreat controller. Frame 432 explicitly goes to standing and plays. | The warp never writes `scale_X`. BODY pressure still reads that variable until `updateDirect` changes both values. Compiling the write as `set_facing` changed pressure by 5 px starting at 414/415. Both compiler output and runtime branch selection now use `_xscale`. Clean and matrix up+J cases test both contact timing and positions. |
| Argumentless guard effects have no receiver | Byakuya frame 852 places child 572, whose enterFrame calls `bdfyxg()`. Frame 857 explicitly returns to standing. Main frame 8 defines `bdfyxg(selfmc)` / `bdfyxg2(selfmc)` and switches on `selfmc.bdzl`; no fighter overrides either function. | Missing `selfmc` cannot borrow the fighter's previous blocked-hit strength. The old adapter incorrectly spawned another guard effect and pause when guard was released. Compile these no-argument calls as no-ops; explicit onDefence calls are unchanged. Gin super versus guarding Byakuya covers tick 244. Chad uses the same faulty call form. |
| Queued summon calls survive another goto | Gin frame 906 contains only `doZhaoHuan();`. Main timeline DoActions already queued for that display remain pending when an incoming hit changes the playhead to 1000. The source function checks `hurtSkling`, writes `bs`, consumes 100 energy and calls yfgj. | Dispatch the retained frame's call once, with its source guard, rather than inspecting only the new current action/frame. All 35 fighter bundles have standalone doZhaoHuan call frames; the compiler now rejects mixed statements until their ordering is compiled. The Renji random case's tick 1087 records the helper activation and energy cost before hit settlement. |
| Unqualified hitTest targets the whole projectile | Byakuya frame 148 places sprite 109 (`tzatm`); load initializes `played=0` and `movspeed=speed`. Subsequent enterFrames test the entire clip against opponent bdmn/attack clips, otherwise move both axes. A collision conditionally sets played, stops motion and goes to frame 5; frame 6 renames it to abcd. | Python `re.findall` returns an empty string for an unmatched optional receiver, not None. Compile that as `self`, not an unnamed child. The previous child-only query stopped the projectile at random-case tick 1413 and lost the source hit at 1414. No hitbox dimensions or tolerances changed. |
| External play retains the delivery display | Main KO `nextfight()` resumes the existing stopped Ready clip with `play()`, alongside the existing actor goto calls. Ready frame 2 clears nxtfht; frame 127 calls startFight; playback eventually wraps to stopped frame 1. | Like the actor destination-frame handling, an externally resumed intro clip retains its current frame on the delivery display. Advancing Ready immediately unlocked combat one frame early. Preserve this play state in BattleIntro; checkpoint serialization retains it. The two original timer tapes and the Renji random next round cover pause, position and touchFloor. |

`ready-observer/` is a fresh native Flash capture with observational startFight
and Ready-frame logging. Its timestamps distinguish callbacks before the next
root observation from callbacks in the preceding display: nextfight resumes
Ready at frame 1, the first following root sample still sees frame 1, and only
the subsequent sample sees frame 2. startFight remains after actor callbacks
and before the root observation. No global callback reordering or tick-0 field
rewrites are part of the fix.

The generated-data changes are scoped to body warps/frame calls, projectile
receiver fields and the two no-argument guard callbacks. `generated-audit.json`
checks these against the retained source/compiler output. The projectile receiver correction is also present in merged PR #10 and is
retained from upstream. Existing unrelated stale fields are not silently regenerated. Combat-model dependency hashes and
the online compatibility manifest are refreshed after review. Master integration
also adds Ikkaku: its two timelines received the same mask-only refresh (14
shapes each), with a second run confirming zero further changes. See
`ikkaku-mask-regeneration.json`. PR #7, #8 and #10 are all included through
master `e5b46fbb`; no other worktree was modified.

## Reproduction

From the repository root, with Godot 4.7.2:

```sh
python3 tools/test_source_parity_suite.py \
  --suite evidence/characters/yin/shared-source-parity/references.tar.gz \
  --godot /path/to/Godot --output /tmp/bvn-shared-source-parity --jobs 4
python3 -m unittest discover -s tools/tests
python3 tools/test_rollback_foundations.py --godot /path/to/Godot
python3 tools/verify.py
python3 tools/check_handoff.py
python3 tools/validate_contracts.py
python3 tools/build_online_manifest.py --check
python3 tools/test_online_manifest.py
```

The suite checks raw reference/fixture/build hashes and locked source inputs,
then compares every fighter row on all 14 scalar fields without tolerance or
row shifts. Two round fixtures replay actual recorded nextfight callbacks;
random cases use their existing explicit source clock. Reports separate existing
trace comparison from fresh engine execution. This is bounded same-input
acceptance, not a claim that all possible fights or visual pixels are identical.
Final execution results are recorded in `checks.json` and `comparison.json`.

## Final merged-code results

All 136 cases matched 94,232 Flash states exactly, including all 13 previously
failing cases. The 58 upstream projectile regressions matched 40,476 states;
three child-projectile references matched 1,806 fighter and 70 projectile states.
Python ran 296 tests successfully (two skipped). All 17 selected Godot checks,
15 rollback checks, and seven online-manifest tests passed. The mask corpus now
covers 1,666 shapes, including Ikkaku. Five broad smoke failures reproduce the
stored baseline errors; see `known-failures.json`. Shutdown resource warnings
remain recorded separately in `checks.json`. Full milestones remain pending.
