# Killer Bee / 奇拉比 base-form port

Base: `147155cb3ecd6387dfd9ae60b3e3522dfbb02f78`, branch `feat/qilabi`.
Targeted native and local Web validation pass at the PR #44 evidence scope.
Full character acceptance remains pending. No deployment, merge, or oracle admission.

## Source identity and scope

`source-order.json` records the original selector tail: Juugo, Karin, Mayuri,
Killer Bee. The catalog maps 奇拉比 to `game/fighter/qilabi.swf`, SHA-256
`e78344d921556e1b57ddb4b95f117e5b9ed6da945822b2fe2ea6d93ecb1afd70`.
Its selected base timeline is Sprite 766 (1,301 frames). The source has no
independent Killer Bee assist; its default helper is the existing Itachi.
Karin/Mayuri worktrees, earlier deferred fighters, and form variants are outside
this change. The original selector portrait frame is 57.

## Source-first answers

1. `source-first.json` indexes all 1,301 root frames, their retained script
   paths/hashes, display changes and events, including frames without scripts.
   Full nested source remains in `scripts/fighter/qilabi.json`; extracted
   geometry preserves placement matrices, depths and instance lifetimes.
2. Fourth-normal cancel controller is placed at frame 270, depth 30. Its load
   callback defines `attack(fn)`, which updates facing before jumping to the
   requested label. Frame 289, depth 35 loads a separate controller-local
   `spd = 15`; each unpaused callback moves by that value and decrements it
   while greater than 3. New placements reset this local; MOVE retains it.
   Root frame 493 places Sprite 256 (`abcd`). Its frame 1 stops and initializes
   `played = 0`; collision sets `played = 1`, assigns `movspeed = 0`, and jumps
   to local frame 5. Frame 6 renames it `zh3atm`, frame 9 renames it `aaa`, and
   frame 12 stops it. Those names are source attack lookup changes.
3. Normals return at 203/226/255/281. Cancels use 197/216/245/270 placement
   windows. Low attack returns at 323; upper attack at 371, with explicit
   continuation 372–397 returning to falling at 387. Low ranged contact can
   enter 招21 early, while natural playback also reaches 459; return is 476.
   Air ranged loops at 155 until contact or landing, selects 跳招3/跳招4,
   and ultimately returns at 191. End-of-label is never an invented exit.
   Super freezes/resumes at 527/553 and returns at 631; frame 556 reverses
   display and logical facing and copies only opponent X ±80. Upper super
   uses 645/692 and returns at 746. Ultimate uses 756/807, then another
   813/888 pause/resume pair, returning at 977. Source face labels are
   奇拉比1 and 奇拉比2. There is no source air-super or transformation label.
4. Tests lock those source placements, local declarations, callback resolution,
   frame-one stop and facing/X-only warp. Common receive-chain tests cover
   all 35 fighters and 26 helpers. Root guard calls onDefence(2) at 1035;
   onBeHit runs at 1047/1060, standing clears hits at frame 2, and hurt
   recovery returns at 1056. No character-specific runtime branch or guessed
   hitbox is introduced. PR #37 interrupted-super recovery remains unchanged.
5. Character-SOP dynamic probes use the locked main/fighter source copies,
   recorded fixtures and instrumentation. Every Flash launch is wrapped by
   `/Users/fengkx/me/agent-code/.locks/flash_lock.py run --holder bvn-qilabi
   --wait -1 -- ...`; another session's lock is never stolen. These are
   controlled instrumented character comparisons, not M0-02/native-live/FDB
   oracle captures. Actor-state matching does not establish pixel/audio or
   OS-input/global-clock/initialization proof.

## State lifetime

| State | Owner | Initialize/write | Preserve | Clear |
|---|---|---|---|---|
| `spd` | frame-289 controller instance | load=15; unpaused movement callback decrements to 3 | MOVE, checkpoint/replay | replacement/removal |
| `attack(fn)` | frame-270 controller instance | load-defined function | that placement's lifetime | replacement/removal |
| `played` | Sprite 256 instance | frame 1=0; contact/frame 6=1 | retained child and local stop | new placement |
| `movspeed` | Sprite 256 instance | first contact assignment=0 | retained child | new placement |
| facing/X | fighter wrapper | source frame 556 branches | source writes/round lifecycle | source reinitialization |
| hit count | receiver fighter timeline | shared onBeHit | while hurt | source frame 2 |

## Validation and residuals

- 21 fresh character-SOP cases match 15,162 actor states on all 14 exact fields.
  Twenty positive move/receive cases reach their target ranges; the 99-energy
  super negative correctly never enters the move. `comparisons.json` retains
  fixture/source/native hashes, observed damage and combo counts.
- Source coverage includes all four normal stages, low/upper and aerial moves,
  normal and fourth-normal cancellation, guard chip/receive/interruption,
  super/upper super/ultimate, repeated low attack and repeated supers/ranged.
  Fourth-normal local `attack` dispatch reaches upper super at tick 71 after
  input tick 70; it deals 490 combined damage / 6 hits. Ultimate deals 555 / 14.
  Guard chip is 2 for normal and 30 for super; neither becomes a hit combo.
  Repeated upper super and upper ranged second casts whiff identically to Flash.
- All 216 saved prior-port fixtures match 127,672 states on 14 fields against
  the final runtime. `regressions.json` and compressed process logs retain results.
  Combat and controller generation for all 26 prior bases is unchanged.
- Production rollback covers natural opening, pause/checkpoint restore, delayed
  inputs, round reset and placement-local state across continuous low attacks.
  Standard controller/selection/visual/protected-recovery smokes pass.
  Shared PvP and training-timer references match 602 states each.
- Source-focused tests pass (27 final tests plus the earlier 41-test related
  suite). Contracts, input integrity, handoff and online selection checks pass.
  Matchmaking TypeScript and tests pass after an isolated Wrangler retry with
  permission to write its local registry. Nothing was deployed.
- The initial 1,532-test Python run had 24 failure records and 5 errors. Nine
  records introduced/exposed here are resolved by the source correction and
  explicit new roster expectations. The remaining 15 failures and 5 errors
  concern unchanged historical proof pins or shadow catalog layout; see
  `diagnostics/`. Their baselines remain untouched.

Native Compatibility-renderer screenshots show actual selection and natural
opening followed by super frame 559. They do not prove Flash pixel/audio parity.
Initial incorrectly timed cancel/down-command fixtures and the upper-U first
difference are retained as diagnostics, not additional move coverage.
`checks.json` records timing, hashes and final local Web status. Full
audiovisual/browser-parity/AI/exhaustive boundary acceptance remains pending,
as in PR #44. Source/actor-state coverage does not prove every child clock,
rendering effect, voice overlap or real keyboard lifecycle.

The shared runtime change is only the source-authored projectile property
assignment: a preceding `var` declaration is not required. It does not invent
initial state, collision reach, gravity, or character-specific behavior.
PR #37 interrupted-super recovery remains byte-identical (the existing
intentional recovery deviation is preserved).

All six admission/proof flags remain false: `production_admitted`,
`native_parity_proven`, `oracle_accepted`, `certified_global_tick`,
`os_input_join_proven`, and `native_initialization_complete`.


## Local Web receipt

The exported production UI was exercised at localhost: title, Killer Bee
selection, both helpers, stage, natural opening, movement and held normal attack.
The opponent loses 210 HP through the four-normal chain. Enter pause/resume and
a natural subsequent round are recorded. Browser diagnostics report no errors.
`web-receipt.json` joins runtime build/resource identity to the exact exported
PCK sidecar; screenshots retain selection and in-fight appearance.
Inputs were synthetic DOM keyboard events held across source ticks, not direct
runtime action calls and not human OS input. Focus-loss and audiovisual parity
remain unverified. Both Web builds completed successfully; an early intermediate
log read preceded the first build's final artifact copy. No build-tool change
was needed. Post-import UIDs/settings belong to the build snapshot; incidental
editor UIDs for unrelated workspace files were removed before staging.
