# Visual observations from the first roster pass

These are same-input native Flash/Godot snapshots, not full move-set acceptance.
Native checkpoint sampling was separately calibrated against terminal replay;
all actor states matched and only the real-time countdown differed in that
calibration. The production HUD and particle differences below still require
individual terminal replay and recorded-random checks before narrowing causes.

| Case | Ticks | Observation | Status |
|---|---|---|---|
| Sage Naruto | 175, 205 | Wind arcs were painted as a large white/cyan rectangle | Fixed; 842 actor states and 421 root positions still match |
| Obito | 205, 240 | Original opponent is in front of the statue; native opponent is occluded | Open: source hit/guard `swapDepths` chain and render depth |
| Deidara | 145 | Native smoke has hard pixel edges where original is blurred | Open: filter/raster sampling |
| Deidara | 205, 240 | Explosion fragment positions/scales differ | Recorded-random and child-clock check pending |
| Gaara | 205 | Blood/hit effect orientation differs | Recorded-random check pending |
| Itachi | 175, 240 | Opponent is tinted/occluded by Susanoo; top HUD absent | Open: blend/depth versus sampling |
| Sage Naruto / Jiraiya | 205 / 240 | Top HUD absent in native sample during effects | Open: terminal replay and blend ordering |
| Multiple fighters | after 175 | Original 1P/2P markers visible, native absent | Check real-time presentation callbacks |

The test freezes native external timers for checkpoint sampling. Countdown digits
and energy-bar flash phase therefore are not synchronized visual baselines.
Native random particles have not yet consumed the recorded original random tape;
particle discrepancies are observations, not established source-logic defects.

Reviewed so far: Byakuya, Chad, Obito, Deidara, Gaara, Ichigo 2, Itachi,
Kenpachi, Jiraiya, Sage Naruto and Ichigo Bankai. Remaining contact sheets are
being reviewed as the native Flash batch completes.
