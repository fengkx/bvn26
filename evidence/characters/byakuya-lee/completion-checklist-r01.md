# Byakuya / Lee base-form completion checklist

This checklist defines the remaining acceptance work for the two base forms.
It is an execution plan and status record; a generated artifact or focused
smoke does not satisfy an item without the stated same-input evidence.

## Acceptance gates

| Area | Required evidence | Current status |
| --- | --- | --- |
| Source identity and provenance | Locked SWF/script/timeline hashes, fixture identity, helper identity, input and random/clock tape hashes | Partial. Bounded cases have this; the complete matrix still needs every case to carry it. |
| Controller behavior | Every reachable base-form controller path, including nested child controllers, source-scoped functions, placement lifetime and callback order | Partial. Byakuya 69 and Lee source scopes are compiled; full controller/input coverage remains open. |
| Helper behavior | Source helper load identity, per-tick frame/action/visibility/attack state, child lifetime and pause/stop ordering, compared field by field | Partial. Continuous replay compares available source helper fields per tick, and dedicated summon captures now compare active frame/attack/root pause/nested atm1-3 lifecycle: Lee 84 active rows and Byakuya 101 active rows, zero differences. Parked frame-1 display-list emptiness is source-verified for woailuo and kon. Parent-container frame and inactive display-list visibility remain explicitly unaliased; complete helper matrix remains open. |
| AI and random consumption | Real original CPU replay from a documented checkpoint or boot, all actor/controller/helper fields, random site/index/value order, input reads and clock events | Partial. Byakuya 180-tick bounded and Lee 300-tick bounded replays validate actor fields and tapes; full input coverage and boot/intro parity remain open. |
| Boot and intro | Fresh source and Godot boot, title/menu to fight, real intro completion, `kcplayed`/sound/helper/child callbacks and Ready checkpoint alignment | Partial. Godot `intro_smoke` passes; capture-compatible source-preserving probe is prepared at `/private/tmp/bvn-boot-ready-r06/game/main.swf` with offline lifecycle proof, source Ready/game-running detection, full input/round observation and a locked capture command, but fresh source boot/intro and title/menu alignment still need desktop input. Partial standing checkpoint plus `intro.begin` is explicitly not boot/intro parity. |
| Combat actions | Every base-form label across neutral, held, mirror, wall, air-target, guard/trade and energy boundaries with source and native 602-state comparisons | Partial. The current shared rerun covers 31 cases under the current runtime; the clean Lee 625 kill/dead pair is validated at 802/802 states with zero differences in `evidence/characters/lee/validation/timer-ready-r04/625-current-compare-r05.json`. Current Byakuya and Lee matrix classifications remain separated in their current manifests (`boundary-r11-current-missing5/manifest.json`, `matrix-source-classification-r04.json`); legacy/native-only and disabled-negative rows are not promoted to validated. |
| Hit/receive chain | HIT_RECEIVE_SOP steps A-E, including guard, hit pause, combo count, sparks, projectiles, `bsd/cbsd`, `*atm` lifetime and no-chain helpers | Partial. Focused cases exist; full action/helper matrix and step-E coverage remain open. |
| KO and round lifecycle | Same fixture through KO, timer registration/fire/cancel, reset, next round, helper reload and teardown; source timeout ordering | Partial. Lethal traces and both `p1`/`draw` timeout reference comparisons pass; neither covers a fresh Flash boot, complete next-round intro-to-Ready, return-selection, or post-reset real-input sequence. |
| Web UI and controls | Fresh QA PCK hash; real title→mode→fighter→helper→map→intro→battle keyboard flow for both roles; J/I/helper/pause/resume; console and visible canvas checks | Partial. The latest helper4a0f export is recorded at `evidence/web/qa-hud-current-r03/` with PCK SHA256 `d921f9a062bebc3bc05a9237b8c959801f5e18b44d594de44d8e20801c6bf23c`; this export has no new browser/UI run. The prior default-roster package at `127.0.0.1:8784` with PCK SHA256 `3371c321c38a14fda20574cd409e2ef66e02ed26585734e1f2a3bb10ae2f8572` completed fighter/helper/map→battle for P1 一护/P2 鸣人 with 魂/我爱罗 helpers. Fresh inline screenshots showed battle HUD countdown 57; a same-run pause probe held countdown 50 across 3000ms, then a later resume observation showed countdown 37 with a visible 5-hit rush. This is a bounded smoke, not full Web visual parity or source-level pause parity. The full-roster QA run at `127.0.0.1:8783` with PCK SHA256 `7c3a4c281b7322e692f7556f586d1a86fee285fef87a41c6eeabcb57247d815d` remains the role-selection evidence for P1 白哉/P2 小李. Natural match-end return to selection and short re-entry were observed; explicit pause-menu return-to-selection, I/O/N5/N6 positive paths, and the full Web matrix remain pending. The older `379950...` candidate package is historical. |
| Visual/audio/HUD | Original-player captures and Godot/Web captures for labels, effects, portraits, sounds, HUD, pixels and timing | Partial. Byakuya sound sites 887/581, 934/44 and 944/52 have native/Godot reachability evidence, and 963/619 reaches `IntroCoordinator`; original-player same-input parity remains pending. The current native HUD frame-576 capture is `evidence/characters/byakuya/audiovisual-r06/godot-576-gui-r04/godot-600x400.png`; the current Web HUD was observed inline on page35 at battle countdown 57/50/37; screenshot persistence and original-player pixel parity remain pending. Lee visual authority remains `evidence/characters/lee/visual-parity-r01.json` and `evidence/characters/lee/original/lee-795-bishaSuper-visual-freeze-837-r01/`; clean 625 kill/dead comparisons are validated, while pixel-level visual parity and countdown/source timing remain open. See `evidence/characters/byakuya/audiovisual-r05/audio-gap-r01/reachability-r01.json` and `source-native-plan.json`. |
| Production release | Roster/manifest only after all applicable gates pass; no transform or unrelated role regressions; verify/handoff/contracts green | Closed. Production roster remains closed until root performs final acceptance. |

## Execution order

1. Add field-by-field helper comparison to the continuous acceptance runner,
   keeping source helper rows and native helper rows separate and failing closed
   on missing rows, identity, placement age, frame, action, visibility,
   attacking, pause or teardown fields.
2. Reuse the formal source-input wiring and continuous runner for multi-input
   CPU captures. Each capture must use `/tmp/bvn-native-flash-capture.lock`,
   release the lock after the case, and retain source/build/input/random/clock
   provenance. Do not reuse intervention probes.
3. Establish a fresh boot/intro run for each role and compare the real source
   Ready boundary before extending the replay. Any runtime change requires the
   five SOURCE_FIRST questions and a source first-difference trace.
4. Extend the Web QA matrix only after the local source/native case passes:
   both roles, neutral/held/mirror/wall/air-target/guard/trade, J/I/helper and
   pause/resume, with KO and next-round lifecycle captured separately.
5. Run representative old-role regressions and the complete shared checks;
   keep production availability closed until root reviews the resulting
   evidence and legal manifest changes.

## Machine-checkable completion criteria

- **Controller:** the source audit inventory must enumerate every reachable
  `(source path, sprite scope, placed controller, callback symbol)` and the
  acceptance index must show either a source/native comparison or an explicit
  disabled-negative reason for each row. A passing compiler build alone is not
  coverage.
- **AI:** the continuous validator must report `acceptance_status=validated`,
  exact unique display-tick/slot coverage, all 14 actor fields, available
  helper fields, input transitions, random site/index/value sequence and clock
  sequence. Checkpoint replays must state their scope and may not claim boot
  parity.
- **Boot/intro:** a fresh source and Godot run must record root-entry frame,
  intro steps, `kcplayed`, sound events, helper loads, child callbacks and the
  first Ready state. No manually consumed tape entry or frame shift is allowed.
- **Visual/audio/HUD:** each accepted label needs a source-frame list, visual
  child/effect lifetime, audio event/resource identity and Web/native capture
  hash; pixel/HUD claims require the matching original-player capture.
- **Web:** the fixed 178-case matrix must be driven from the real UI with a
  recorded mode, fighter/helper/map selection sequence, P1/P2 key events,
  action/source-frame output and QA PCK hash. Direct action calls do not count.
- **KO:** each role needs both a lethal and timeout/return-to-selection case
  with timer register/fire/cancel sequence, next-round actor/helper reload and
  source timeout ordering. One successful timer smoke is insufficient.

## Current bounded evidence

- Byakuya continuous AI: `evidence/characters/byakuya/ai-clean-r01/continuous-r03/acceptance.json`, bounded 180 fight ticks.
- Lee continuous AI: `evidence/characters/lee/ai-cpu-r01/continuous-r02/acceptance.json`, source horizon 300 fight ticks.
- Byakuya source matrix: `evidence/characters/byakuya/fixture-inventory-r03.json` and `boundary-r03/manifest.json`.
- Lee source matrix: `evidence/characters/lee/matrix-source-classification-r04.json` and `source-parity-manifest-r03.json`.

These artifacts document partial acceptance only. They do not close the
remaining checklist gates or authorize production roster changes.
