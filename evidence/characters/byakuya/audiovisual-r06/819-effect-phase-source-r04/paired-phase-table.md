# 819 effect phase paired table

| side | callback | fight tick | actor frame | helper local frame | effect frame | evidence |
|---|---:|---:|---:|---:|---:|---|
| Flash | root observer | 15 | 818 | 1 | undefined | `source/target-events.txt` |
| Flash | root observer | 16 | 819 | 2 | undefined | `source/target-events.txt` |
| Flash | root observer | 17 | 820* | 3 | 2 | `source/target-events.txt` |
| Godot reverted | root observer | 13 | 817 | 1 | absent | `godot/runtime-probe-current-reverted.json` |
| Godot reverted | root observer | 14 | 818 | 1 | absent | `godot/runtime-probe-current-reverted.json` |
| Godot reverted | root observer | 15 | 819 | 2 | 1 | `godot/runtime-probe-current-reverted.json` |
| Godot reverted | root observer | 16 | 820 | 3 | 2 | `godot/runtime-probe-current-reverted.json` |

`*` The source target window records helper frame 3 and effect frame 2 at fight 17; the actor state row is retained in the full raw trace. Source helper spawn is sequence 3963 at display 471/fight 15. The first same-root observer effect record is sequence 4001 at display 473/fight 17. There is no source effect record at the target callback sequence 3973/display 472/fight 16.

The current reverted Godot runtime therefore places/observes effect frame 1 one callback earlier than the source. No runtime correction is accepted here; this table is diagnostic evidence for a generic placement-phase fix.
