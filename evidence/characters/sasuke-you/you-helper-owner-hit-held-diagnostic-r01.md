# You owner-hit heldstart20 diagnostic r01

This is a read-only diagnosis of the first divergence in the explicit You
helper owner-hit fixture. It does not change `game/`, `scripts/`, or runtime.

## Evidence and scope

- Fixture: `/private/tmp/sasuke-you-kakashi-owner-hit-held-r01.json`
- Original events: `evidence/characters/sasuke-you/you-helper-owner-hit-held-native-r01.events.jsonl.gz`
- Native states: `/private/tmp/sasuke-you-kakashi-owner-hit-held-native-r01/native.json`
- Existing comparison: `evidence/characters/sasuke-you/you-helper-owner-hit-held-native-r01.compare.json`
- Fixture is explicit: Sasuke p1 with You, Kakashi p2 with Kon; p1 summon is
  held on ticks 10..13 and p2 attack is held on ticks 20..180.
- Current file hashes at audit time: native `2e9e49c58e2c920a6f6c334429406681107dcb6779956d9025b5174c8c7cdbe4`,
  comparison `e417dfd01ab2b7136a22cec9a14333e0d9d726aefb18ff265a7f58aded2f83f3`,
  original events `a7f80a4e04e49f5c562dff76a5212830e1cdda4377064e014c346c9be4d9ef23`.
- Source/runtime audit inputs: `scripts/fighter/Sasuke.json`
  `b0075fdab80fc600cd344d4df5c0ac3727c484f4c6bc4ff6bf198509709cb097`,
  `godot/fighter_runtime.gd`
  `cbb079e264c2777610a2dfb33728906c75e72c20ad6751f2da2669677e78c07d`,
  `godot/source_callback_registry.gd`
  `aa66f0e2baad51fcddaaf6cb5c94dbf6ba96426783df5082fcbdd7aefe76b3d2`.

## Source order

The relevant Sasuke root timeline is `scripts/fighter/Sasuke.json`,
`DefineSprite_603`:

- frame 861 `DoAction.as`: `hited = 0; play();`
- frame 862 `DoAction.as`: `onBeHit();`
- frame 863 `PlaceObject2_16_30` enterFrame: `_parent.beidax();`
- frame 864 `PlaceObject2_2_28` enterFrame: `beida();`
- frame 867 `DoAction.as`: `stop();`

The source `beidax()` moves and increments `hstm`, while its root-pause guard
returns before either operation. The source capture records p1 at frame 868,
`hstm=20`, x=209, y=-81 on tick 92. On tick 93 the fourth receiver callback
has already moved the playhead to frame 861, with the same position and
`hstm=20`; frame 862 executes on tick 94, changing HP 930 to 870 and hits 3 to
4. The root becomes paused on tick 95 at frame 863.

## Native first divergence

Native and source agree through p1 tick 92 (`frame=868`, `hstm=20`,
`x=209`, `y=-81`, unpaused). Native tick 93 instead advances the hurt body to
`frame=869`, `hstm=21`, `x=205`, `y=-85`; no fourth receive occurs. It reaches
frame 870/hstm 22 on tick 94, then frame 1 and frame 56 on ticks 95..96 while
remaining unpaused at HP 930 and hits 3. The p1 You helper is parked at frame 1
and `attacking=false` throughout this window; Kon is also not the source of
the divergence.

## Finding and boundary

The first proven mismatch is the tick-93 receive-versus-hurt-step phase: the
source receives before the next visible hurt-step result, whereas native takes
that hurt step without receiving. The later `paused` and queued-standing
differences are consequences of the missed fourth hit, rather than evidence
that the shared hurt timer or standing transition fired early.

The current logs do not capture the receiver callback's pre-query `bdmn`,
attack AABB, or exact dispatch order. Therefore they do not prove whether the
native miss is caused by callback ordering or by a boundary geometry difference
at x=205/y=-85. No timer, pause, standing, or one-frame delay patch is
justified by this record. A minimal follow-up, if authorized, is one
instrumented tick-92..94 run that records the pre/post
`CombatResolver.resolve_incoming` query and both world AABBs; any fix must
preserve source `beidax` and queued frame semantics and be shared rather than
You-specific.
