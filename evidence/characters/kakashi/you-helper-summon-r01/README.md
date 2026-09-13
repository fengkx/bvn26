# Kakashi + You summon regression r01

Status: fixed-data candidate matches the original for the explicit Kakashi + You + Kon control fixture. This is a bounded summon-path result, not full Kakashi acceptance.

The original generated combat artifact had SHA-256 `5336e229a2418c6a6411bc21078d9d59243f138cf37b64e5b96cb64a5ffd4c88` and an empty `summon_events` array. With fixture `p1_helper=鼬`, P1 paid 100 energy but stayed at action 0 and the helper remained parked at frame 1. The preserved red output is `old-red-native.json.gz`.

The compiler rebuilt `godot/generated/fighters/kakashi/combat.json` from the unchanged Kakashi fighter metadata, timeline, and script bundle. The new artifact SHA-256 is `42a7944afd858334d8fc40aaa612af98e902479056173ea5e60d2ceb1dae1c83`. It adds the source-derived direct `yfgj` event at `DefineSprite_710/frame_1035/DoAction.as` (SHA-256 `b58c7dd5a870fbe5a1cd87958761dbf7f43966a3de4158c6f943a285887dd34e`), after the existing energy event at frame 1032. The source call is `_root.yfgj(_parent._name); bs = 1;`; the generic runtime activates the helper instance already bound to that fighter. The event's catalog default helper metadata remains 我爱罗; it does not select the runtime helper and was not changed to special-case 鼬.

Source-first questions:

1. Q1: frame 1032 charges 100 energy; frame 1035 calls `yfgj` and sets `bs=1`.
2. Q2: the fighter timeline calls the root helper function directly; it does not place a helper clip itself. The root function resolves the selected fighter's helper instance, places it at the source offset, and starts it at frame 2.
3. Q3: the selected helper begins at frame 2 and follows its own frozen helper timeline. No helper-frame change was added for Kakashi.
4. Q4: one source call activates exactly the selected helper once, at the source placement and start frame; its activity and natural end are governed by the helper source timeline.
5. Q5: the original Flash capture used the same explicit fixture and 300 fight ticks. Source and native fighter states match 602/602 across 14 fields; helper states match 602/602 across 6 fields.

The original trace contains one P1 `helper_spawn` at fight tick 15 for helper 鼬. Both source and native first observe the active helper at tick 16, frame 2, attacking at `(280,-25)`. The native/helper comparison reports zero differences over 602 rows; P1 energy transitions through the 100-point summon cost. The exact source trace is retained in `source-events.jsonl.gz`, with build metadata and the bound `case.txt` alongside it.

Two native-only routing controls also passed with the same summon input: Kakashi + 我爱罗 activated 我爱罗, and Sasuke + 鼬 activated 鼬. They are retained in the adjacent `/private/tmp/kakashi-you-diagnostic` workspace; they are not original-player comparisons.

## Scope and next checks

The deterministic rebuild also materializes source-backed Kakashi projectile velocity and on-hit fields and `clip_placements` metadata for `dogs`/`cbs1atm`. The follow-up focused original/native checks are recorded in [projectile runtime r01](../projectile-runtime-r01/README.md): the frame-162 air projectile and frame-425–443 ground projectiles match all fighter and helper rows, including the four observed hits. The `dogs` and `cbs1atm` placements are source-reviewed but were not triggered by those inputs. Older archived Kakashi regression entries have summaries only, not raw traces to replay. The production selection roster remains unchanged.
