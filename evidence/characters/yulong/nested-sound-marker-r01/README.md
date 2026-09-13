# Yulong nested StartSound marker r01

This packet proves that the natural `ranged_down` fixed input enters source sprite 185 frame 8 and executes its source StartSoundTag for sound 164. The separate marker DoAction is inserted immediately after the original StartSoundTag in an isolated dynamic build. The instrumentation report records exact normalized XML round-trip equality after marker removal and unchanged source ActionScript/image-alpha semantics.

The native capture contains one marker event and a successful `done`; the same run records Yulong root frame 466 at fight tick 42 and frame 472 at tick 48. Sprite185 frame 7 renames the live instance to `zh21atm`, matching the marker payload at frame 8. This confirms reachability through the fixed case, not audible device output.

The source audit answers SOURCE_FIRST questions 1–5 for this nested sound event. It leaves `RemoveObject`/`unloadMovie` audio lifetime and nontrivial nested SOUNDINFO baking unresolved.
