# Lee exact frame-action callback evidence r01

This evidence uses the fixed Lee slot (`p1`, 小李) with P2 一护 and helpers
我爱罗/魂. The original player builds use `body_boundaries=true` and no
frame-order or schedule probe.

- `frame_29/DoAction.as` (`瞬步`): source fixture `lee-20-rush-neutral`, native
  marker at display tick 512 / fight tick 19; Godot marker at local physics tick
  326. Both source and Godot emit enter on source frame 29 followed by exit to
  frame 1 in the same callback boundary.
- `frame_1017/DoAction.as` (`招换`): source fixture
  `lee-callback-summon-r02`, native marker at display tick 505 / fight tick 40;
  Godot marker at local physics tick 347. Both emit enter on source frame 1017
  followed by exit to frame 1 in the same callback boundary.

The clock origins differ (native display/fight ticks versus the Godot move-case
physics tick), so this is exact source callback ordering under the same fixture
input, not a claim of full boot/clock parity. `compare.json` compares the
marker sequence and state fields; the raw native captures remain under
`evidence/characters/lee/original/`.

`exact-marker-index.json` is the machine-readable inventory audit. Across both
captures it retains every `body_boundary` row with its slot and source frame;
the Lee (`p1`) rows directly prove seven previously pending inventory entries:
frames 8, 29, 1017, 1158, 1159, 1161, and 1219. The smallest existing
fixture set-cover for the other frame-action entries is the eight manifests
listed there (ground chain, special continuation, magic chain, intro round,
air actions, recovery/standup, KO entry, and summon). Ten entries remain
uncovered, including the clip-action paths; they are explicitly listed rather
than inferred from a same-label fixture. P2 rows are retained for audit but
are not attributed to Lee in these captures because P2 is 一护.

The index also records the older `lee-body-boundaries-r02` raw capture as
source-executed-only evidence (not paired parity); it reaches pending Lee
frames 634 and 1260 in addition to startup/opening rows. Six remaining
set-cover families have fresh `body_boundaries=true` builds under
`/private/tmp/lee-callback-*-r04*`; they are prepared for the next serialized
original-player capture and are not counted as executed until raw events are
collected. Clip-action entries remain a separate observer gap.

The first serialized r04 captures are recorded in `exact-marker-index.json`: ground-chain completed with Lee frame 172 observed (other requested targets were not reached), and special-continuation completed with frames 660 and 695 observed (its other requested targets were not reached). These are source-executed partial results, not blanket fixture coverage.

Magic-chain and intro-round r04 captures are also complete; their reached/missing callback frames are recorded per fixture in `exact-marker-index.json`.

Recovery/standup (Lee in p2) and KO-entry r04 captures completed; observed and missing source callback frames are recorded per slot in `exact-marker-index.json`.

A temporary schedule-probe recovery capture reached the 1088 and 1098 clip callbacks with enter/exit markers; 1133 was not reached. Counts, sequences, parent targets, and display/fight ticks are in `clip-action-gap-r01.json`; this is source observer evidence only.

Defence-entry r03 and recovery-entry r03 are source-executed partial captures. Their exact reached/missing frames and source-first explanations for ground/magic continuation windows are indexed; original fixtures remain unchanged.

An exploratory multi-edge pass was executed after the single-edge captures. The ground fixture used attack edges at 10-13, 35-38, 60-63, 85-88, and 110-113; it reached Lee source frames 158, 169, and 172 in the chain, but did not reach 193, 197, 235, 240, 268, or 448. The magic fixture used down+ranged at 10-13 followed by ranged edges at 35-38, 60-63, 85-88, and 110-113; it reached body frames 282, 287, 295, 320, 472, 478, 487, and 509; an action field 471 was observed while body frame 1050 was active. It did not reach 325, 332, 370, or 558. Startup/opening rows are retained in the raw captures. These are exploratory source reachability results only; no target was treated as a precondition and no Godot parity claim is made.


The r02 source-causal audit explains the exploratory misses without changing runtime: ground frames 193/197 require the frame-163 `nornalhit()` edge into `砍2`, frames 235/240 require the frame-187 edge into `砍3`, and frame 268 requires the frame-217 edge into `砍4`; the prior attack edges ended before those callbacks. The source-conditioned candidate holds attack from ticks 10-260 (`callback-fixtures-r05-ground-hold.json`). For magic, frame 370 is entered through `砍技2`, whose player input branch is `kis(上)&&kis(斩)`; the candidate uses an up+attack edge (`callback-fixtures-r05-magic-skill2.json`). Frames 325/332 are after an unconditional frame-320 return to `站立` in the generated `招1` range and remain a lifecycle reachability question. Frame 558 requires entering `招3` through the player `magichit3()` branch (`上+招`), while the prior tape used down+ranged. The audit is source reachability only; the candidates have not been captured yet.


The r05 source-conditioned captures were executed. A continuous attack hold from ticks 10-260 reached body markers 235, 240, and 268, while 193 and 197 were not emitted as body markers in this run. A player `上+斩` input reached frame 370 through `砍技2`, and `上+招` reached frame 558 through `招3`. The raw input tapes and every observed body marker are indexed in `exact-marker-index.json`; these remain original-player source execution evidence only, without Godot parity claims.

The follow-up source captures closed the conditioned ground and skill1 markers. The r09 tape uses attack at ticks 10-13, releases, then presses attack at ticks 17-18; it reaches frames 193 and 197 without holding through the frame-187 `砍3` transition. The r06 skill1 tape reaches frame 448. Their raw captures, build hashes, and input provenance are indexed as `source_capture_results_r06` and `source_capture_results_r09`.

The Godot exact-callback probe now consumes fixture-declared `source_callback_targets` (while retaining the legacy 29/1017 targets). It was run against the r09 and r06 fixtures and logged the same enter/exit sequence and action values for 193/197 and 448. This is a bounded callback-order comparison; native and Godot clock origins differ, and it is not full 14-field or boot parity. The paired log/state hashes are in `godot-exact-callback-compare-r01.json`.

Frames 325 and 332 remain classified as normal-input-unreachable for the base `招1` path: exhaustive source search found no numeric or label/child goto targeting either frame, while `DefineSprite_518/frame_320/DoAction.as` unconditionally returns to `站立`. They remain source-control-flow evidence, not fabricated captures.


The original 49 pending inventory entries are now reconciled in `pending-inventory-current-r05.json`, one row per source path/frame/clip kind with the actual Lee slot (including p2 recovery captures). Current current-derived classification is 3 native callback matched (172, 509, 695), 33 source-executed-only, 2 normal-input-unreachable (325, 332), and 11 remaining. Each matched row is explicitly bound to its source build and native fixture. The prior ten native labels are retained only as historical/source-only because their artifacts do not bind current runtime/build provenance. `native-exact-attempts-r03.json` records three additional same-frame four-field Godot observations (172, 509, 695); they remain source-only because the target-filter logs do not carry same-fixture/build provenance. The target-filtered native attempts, including no-target attempts retained as failures, are in `native-exact-attempts-r02.json`; the three r06/r09 source build JSON files are archived under `source-builds-r06-r09/`, so `/private/tmp` is not the provenance authority. Existing 29 is retained in the older native compare and is listed in the aggregate index separately from these original 49 rows.

The earlier `660-ql-audit-r01.json` is explicitly superseded. Its fixed-point decoder incorrectly assumed one exponent; the project decoder in `tools/probes/collect_ai_reference.py` yields `f:1:7:104857600:0 = 200`, matching Godot's ql=200. Decoder regression vectors are recorded in `ql-decoder-regression-r01.json`.


`aggregate_lee_callback_inventory.py` now reads 249 archived native captures across AIREF and JSONL formats with zero parse/slot errors. It correctly attributes recovery markers to Lee p2, recognizes frame 320 and recovery/KO markers from older captures, and reports the 49-row current table from that aggregate rather than hand-edited statuses.

### Current bounded callback index r08

`pending-inventory-current-r08.json` is the current-derived 49-row index after the new r08 same-fixture headless comparisons. Its 19 `native_matched` rows are callback-only matches on `source_frame`, `entering`, decoded `action`, and decoded `ql`; it records 18 `source_only`, 10 `remaining`, and 2 `normal_input_unreachable` rows. The r08 additions are P1 ground frames 235/240/268 and P2 Lee recovery body frames 1086/1087/1096/1098/1112. The 1098 `clip_action` remains distinct and is not counted as matched. Details, raw/build/fixture references, hashes, logs, and the reproduction command are in `evidence/characters/lee/godot/callback-exact-r08/README.md` and `comparison.json`. These counts do not assert full-character parity.


### Current bounded callback index r09

`pending-inventory-current-r09.json` is derived from r08 plus the r09 same-source-run exact comparison. It contains 22 `native_matched`, 16 `source_only`, 9 `remaining`, and 2 `normal_input_unreachable` rows. The three added rows are P1 frame 1070 and P1 frames 95/113; source and native each emitted 10 selected events total with 0 differences across source frame, enter/exit, action, and decoded ql. Frame 95 and 113 each occur twice in the held-jump 600-tick capture. Frame 128 remains source-only pending a matching actual source build; frame 62 was not observed. The source raw/build/fixture provenance and bounded scope are in `evidence/characters/lee/godot/callback-exact-r09/README.md` and `comparison.json`.


### Current bounded callback index r10

`pending-inventory-current-r10.json` adds the exact P1 frame 771 callback comparison to r09: 23 `native_matched`, 16 `source_only`, 8 `remaining`, and 2 `normal_input_unreachable`. Source and native each report enter/exit once at the bound fixture, action 0 and decoded ql 200. Frame 738 was not observed and remains uncovered. The evidence is bounded to four callback fields, with source/native identities and reproduction instructions in `evidence/characters/lee/godot/callback-exact-r10/README.md`.


### Current bounded callback index r11

`pending-inventory-current-r11.json` adds P1 frame 953 and 1057 to the same-source-run callback set: 25 `native_matched`, 16 `source_only`, 6 `remaining`, and 2 `normal_input_unreachable`. Frame 1050 was also compared as a source/native contextual callback (two occurrences) but is outside the fixed 49-row inventory. For the two r11 fixtures, 8 source events and 8 native events have zero differences in source frame, enter/exit, action, and decoded ql. Source fight ticks and Godot observation ticks are recorded separately; this does not establish clock or full-state parity. Frame 738 remains uncovered because the original capture emitted no marker. See `evidence/characters/lee/godot/callback-exact-r11/README.md`.


### Current bounded callback index r18

`pending-inventory-current-r18.json` is the single derived 49-row index after the r18 natural timeout callback, r04 rooftop callback, current four-body comparison, and clip wrapper-return audit. It classifies 44 bounded callback rows as matched, 1 as source-only, 3 as normal-input-unreachable, and 1 as invalid source-fixture precondition. Frame 8 remains source-only because its repeated callback sequence differs (248 source rows versus 92 native). Frame 1083 is excluded from runtime-difference claims because the source Ready state had P2 HP 1000 while the native fixture injected HP 1. Frames 1219 and 1260 match on the P1 kill fixture; P2 recovery evidence is not same-input. Frames 1088/1098 are bounded source-marker/placement-lifecycle projections with raw native wrapper returns preserved, not full clip parity. Frame 1288 matches the four callback fields, but source fight tick 2263 and native fixture tick 2228 remain an independent 35-tick timing gap. Frame 738 matches its bounded callback fields on the rooftop stage; no source/native clock mapping is claimed. See `evidence/characters/lee/godot/callback-exact-r18/README.md`, `evidence/characters/lee/godot/callback-exact-stage-r01/README.md`, and `evidence/characters/lee/godot/callback-exact-body-final-r01/README.md`.
