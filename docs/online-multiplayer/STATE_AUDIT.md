# Battle state audit — native checkpoint implementation

2026-09-22. `battle_checkpoint.gd` now implements the local whole-match graph.
`MAIN_FIELDS` and `MAIN_EXTERNAL` explicitly classify Main's script properties;
a newly added unclassified Main field fails capture. Other owners capture all
script variables except the listed immutable metadata and diagnostic bindings.
Unrecognized native node classes, anonymous callbacks and live timers fail capture.

Read-only tables stay shared; HealthHud saves only its mutable `spec.placement`.
KoTimeline placement dictionaries resolve to their exact compiled-table entries,
because ScriptedTimelinePreview uses identity when finding a live child. Native
nodes are retained locally; this format is not a transferable savegame. Expanded
coverage and Chrome/performance release gates remain separate from this map.

| Owner | State/reference requirements | Current restoration status |
|---|---|---|
| `main.gd` | Physics tick, source frame sequence, pending child operations, match inputs, pause counters, intro/KO/timeout flags, selected resources | Main graph and ordered pending named callables captured; native/direct input stays disabled during replay |
| `game_session.gd`, `match_input.gd` | Setup, root label, score/rules, delivery cursor/previous held values, ordered control position | Session/input locals captured; producers are explicitly external bindings |
| `fighter_runtime.gd` | All backing motion/source scalars, inherited timelines, contact instances, pending goto/frame work, source variables, aliases, AI BODY/controller references | All script state captured; computed coordinates use backing fields plus native position/rotation/scale/skew |
| `timeline_preview.gd` | Root/child clocks, offsets, retained instances, source entry serial, sound placement generations, transforms/colors, immutable resource identity | Retained clips, clocks, colors and sound generations captured; render refresh skips clock/audio advancement |
| `helper_runtime.gd`, `helper_clip_callback.gd` | Activation/stop/deferred generations, root and nested callbacks, undefined `sw`, owner and opponent references | Helpers and their callback references restored by the shared graph; no placement callbacks rerun |
| `ai_source_state.gd`, body/context/controller hosts and generated controller classes | Source fields including null, locals, hook generations, pending natural frames, context object links and input history | Generated classes/contexts reconstructed, preserving shared dictionaries and typed fields |
| `ai_controller_instances.gd`, `source_body_callbacks.gd` | `_next_generation`, ordered live paths, controller objects, placement and registration IDs, enabled callbacks | Shared graph reconstructs controller/BODY/projectile objects, weak aliases, locals and pending callbacks |
| `source_callback_registry.gd` | `_next_id`, ordered entries, current tick, no mid-dispatch checkpoint | Whole graph restores ordered registry entries and rebinding to recreated targets |
| `source_random.gd` | Shared RNG seed/state, tape/cursor/failure; all consumers use restored shared instance | Service save/load and seeded setup tested |
| `source_clock.gd` | Recorded tape/cursor or explicit observed time, failure/counters | Service save/load tested; external timer phase policy still separate |
| `ai_source_timeouts.gd`, `ai_random_clock.gd` | Registration sequence, due delivery, cancellation, target/method and callback arguments | Recorded BODY queues restored; external immutable event journal drives delivery; live timers rejected, PvP-only adapter |
| `match_countdown.gd`, `battle_intro.gd` | Interval registration and pending delivery, local digit/timeline fields, ready/curtain state, loaded flags, poll order and phase | Locals, controller graph, digit/intro state and nextfight timer nodes restored; round fixture passes |
| `ko_timeline.gd`, `source_health_rules.gd` | Nested clip graph/generations, callbacks/load callbacks, pending/executing operations, health HUD fields | Graph aliases preserved; outgoing KO dispatch cycles broken; terminal navigation waits for confirmation |
| `hit_effect_runtime.gd`, `super_runtime.gd`, `super_presentation.gd` | Shared RNG consumption, effect age/lifetime, pause/release counts, camera/black background/flash | Gameplay effect state captured; retired nodes revived from the retained pool; frozen shadow resources retained |
| `ai_combat_services.gd`, `stage_hit_registry.gd`, `game_world.gd` | Spawned effect identities, attack lookup order, helper links, focus/map/clamp state | Services, ordered registries, camera and spawned references included in the graph |
| Audio/diagnostics/scene navigation | Event identity, already-published effects, committed outputs | Sounds deduplicated outside rollback state; display lists refreshed silently; result commit requires confirmation; diagnostic logs remain external |

Reconstruction rules retained by the implementation:

- `main.gd::_queue_source_child_frame` stores bound operations. Examples are
  `helper_runtime.gd::_run_deferred_frame/_apply_root_stop` and
  `ai_controller_host.gd` nested rename/sound work. Persist stable owner/method/
  arguments/generation, not an object address or anonymous closure. Validate
  stale generations the same way as the current source lifecycle.
  `pending_operation_state.gd` supplies the component contract; the battle graph
  now binds these operations as part of the whole-match restoration.
- `AiSourceTimeouts` stores callback plus live Timer; deleting/recreating actors
  invalidates those callback targets. Preserve source registration/cancel/fire
  phase and reconstruct the binding after objects exist.
  Recorded mode now has atomic queue restoration; it does not supply missing
  source delivery timing or convert a running Godot timer into a frame counter.
- `HitEffectRuntime.queue_free` and Main's KO/title scene changes destroy objects.
  A retained dictionary cannot undo deletion. Deferred deletion and reference
  restoration need explicit boundaries; a predicted terminal result cannot escape.
- `TimelinePreview` retains child and sound generation clocks. Re-seeking only
  its root frame resets retained instances and loses the prior branch's state.
- `manual_match_step.gd` retains its narrow component-test contract. The new
  `rollback_battle.gd` supports KO/round restoration with explicit callback envelopes;
  it does not invent a production timer/control scheduling authority.

## Source-first five questions for the current additive interfaces

1. **Frame/handler source:** the step delegates the existing Main phases, compiled
   fighter controllers and intro scripts without changing their sequence. Root
   intro/key rules are `scripts/main.json::DefineSprite_1991/frame_1/DoAction.as`;
   countdown is `DefineSprite_1813/frame_1/DoAction.as`; pause/effect/random calls
   are in `frame_8/DoAction.as`. The complete retained audits are
   [input boundary](../../evidence/input-decoupling/README.md),
   [intro scripts](../../evidence/intro-source.json),
   [timeout scripts and timelines](../../evidence/ai/match-timeout-source.json).
   The new state/test utilities introduce engineering contracts, not new source
   action frame scripts or guessed attack timing.
2. **Placement/MOVE:** source instance registration remains unchanged. Registry
   restore preserves IDs and placed ticks; dispatch still skips the placement
   tick and iterates in reverse registration order. See
   [lifecycle probe](../../evidence/probes/schedule/clip_lifecycle.log) and
   [execution profile](../../godot/generated/main/execution_profile.json).
   The registry unit test remains component-scoped; real battle/roster tests now
   exercise dynamic graph restoration separately.
3. **Exits:** no source goto/stop/fallthrough rule is changed. Existing Main drains
   deferred target scripts in its current source sequence. Automatic KO/title
   teardown is blocked in the rollback adapter until result confirmation.
4. **Invariants:** existing source registry placement/order, held input delivery,
   null-versus-false and random tape consumption are retained. Snapshot ownership,
   immutable input, build rejection and predicted-input correction are engineering
   invariants. Synthetic tests are labeled explicitly; their 100 ms/33 ms clock
   samples and 15-step callbacks are not assertions about original timer cadence.
5. **Original same input:** the immutable shared PvP and training timer traces are
   rerun unchanged (602 states each). Earlier r13/r14/r15 evidence remains scoped
   to its measured fields; the existing r15 failure is not declared fixed here.
   No new original runtime trace certifies a virtualized full-match timer policy.

The source rule remains: `setInterval(time, 1000)` is not proven equivalent to
"subtract once every 30 battle frames". Explicit clock readings do not settle
callback scheduling, and successful local service restore cannot close that gap.
