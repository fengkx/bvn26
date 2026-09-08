# Current fighter move SOP audit — 2026-09-08

Scope: Naruto/Ichigo base forms and the original common Move List. **SOP is not
complete.** This is a current source/artifact/test audit, not original-player
same-input acceptance. No combat rules were changed by this audit.

## Original Move List

`main.swf` Sprite 2010 frame 10 contains EditText 2006: A=slash (default J),
B=skill (default U), C=special (default I), with up/down combinations and air
availability qualified as character-dependent. It is common to all fighters;
there is no character-specific move-name selector or dynamic key substitution.

| Original input | Naruto base label / entry frame | Ichigo base label / entry frame |
|---|---|---|
| A / J | 砍1 / 170 | 砍1 / 173 |
| ↑+A / W+J | 砍技2 / 322 | 砍技2 / 284 |
| ↓+A / S+J | 砍技1 / 260 | 砍技1 / 232 |
| B / U | 招1 / 375 | 招1 / 320 |
| ↑+B / W+U | 招3 / 472 | 招3 / 414 |
| ↓+B / S+U | 招2 / 412 | 招2 / 357 |
| C / I | 必杀 / 504 | 必杀 / 446 |
| ↑+C / W+I | 上必杀 / 609 | 上必杀 / 528 |
| ↓+C / S+I | 超必杀 / 750 | 超必杀 / 582 |
| Air A / J | 跳砍 / 127 | 跳砍 / 127 |
| Air B / U | 跳招 / 143 | 跳招 / 143 |

These entries are wired, not independently accepted. Complete chains include
subsequent labels and conditional transitions; an entry-frame test alone is not
sufficient. The base source timelines have no `空中必杀` label although the shared
controller references it. Do not invent an aerial special or call this alone an
importer omission; the original table explicitly says only some fighters support it.

## SOP A–E

| Step | Current evidence | Verdict |
|---|---|---|
| A: common receive chain | `HitReceiveChainTests`: all 35 playable bundles share functions; 26 helpers have no receive chain | Static checks pass |
| B: compile form tables and presentation | Naruto gjl1/2/3: 21/16/16 attacks; Ichigo: 14/15/19; reset frames, hit/defence events, super calls and face labels exist | Tables extracted; only base-form runtime content loaded |
| C: shared runtime interpretation | Shared hit resolver, root freeze, conditional stopMc/playMc, combo and super presentation exist; previous two freeze findings now covered | Partial; gaps below |
| D: source-invariant regressions | 41 Python tests pass; COMBAT_SMOKE_OK, including rotation, recreated hitboxes, X-only warp, hurt hover and freeze gates | Representative coverage, not exhaustive per-move acceptance |
| E: original same-input traces | No accepted traces for the seven cases required by HIT_RECEIVE_SOP | Missing; M2-04 remains pending |

## Concrete remaining gaps

1. **Transformation dispatch is not transformation completion.** Both catalogs
   mark `万解` wired. Source Naruto Sprite 764 frame 1382 and Ichigo Sprite 638
   frame 1055 execute `_parent.gotoAndStop(2)`. Current FighterRuntime stays on
   the base sprite/combat model; no form switch/retained-state loading interprets
   these parent jumps. Extracting gjl2/3 does not implement them.
2. **Effect shake is not connected to the stage.** HitEffectRuntime emits
   `shake_requested`; main.gd connects pause/resume/shine but no shake receiver.
   SOP's source `XG_*x` root X/Y movement is therefore incomplete.
3. **Sound playback is partial.** HitEffectRuntime explicitly warns that
   SOUNDINFO in_point/out_point/loop_count/sync_stop are unhandled, then plays
   whole streams. Envelope gain uses the first record's channel mean; this is
   not per-channel or time-varying envelope reproduction.
4. **Super presentation remains partial.** Shape 1516 gradient is not rendered
   by TimelinePreview, and the full KO sequence/round lifecycle is not present.
   Imported blackMu/ts_face assets alone do not satisfy SOP C/E.
5. **Catalog gaps require semantic review.** Naruto `螺旋手里剑1`/`跳招2` and
   Ichigo `招21` remain catalog_only; cinematic 开场/胜利/失败 do too. Some labels
   may still be reached through a timeline fallthrough or cancel, so catalog_only
   must not automatically be reported as wholly unimplemented. Each needs its
   source path, full chain and original replay checked.
6. **Five-question evidence is not complete for every move.** Source frames,
   clip placements and event paths are indexed, but an index is not an audit of
   every script/empty frame/terminal behavior. ExecutionProfile is provisional;
   exact original input/timing and presentation comparisons are missing.

The machine inventory lists every catalog label, source range, source event path,
compiled exit/super calls and parent jumps: [current-moves-audit.json](current-moves-audit.json).
Regenerate with `python3 tools/audit_current_moves.py`. `wired` counts (Naruto
36/42, Ichigo 30/35) measure dispatch metadata only and are not completion rates.

Next work should first close parent form transitions and shared presentation
omissions from source, then record the seven SOP E cases and per-move chains.
Keep M2-04/M3-01/M6-02 unaccepted until their actual gates are met.
