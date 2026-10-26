# Remaining component pixels (current renderer)

Every comparison is exact; the columns below are maximum absolute RGB channel deltas. Clock samples match4242/4242. Native references are pinned r03 captures; no new Flash captures this turn.

| SWF | Exact images | R | G | B |
| --- | ---: | ---: | ---: | ---: |
| game/fighter/fz/jinye.swf | 1/4 | 159 | 137 | 159 |
| game/fighter/jiraiya.swf | 0/4 | 42 | 38 | 40 |
| game/fighter/lanran.swf | 0/4 | 35 | 35 | 35 |
| game/main.swf | 6/12 | 177 | 159 | 159 |
| game/fighter/orochimaru.swf | 0/10 | 132 | 112 | 122 |
| game/fighter/yijiao.swf | 2/6 | 51 | 138 | 90 |
| game/fighter/yulong.swf | 0/14 | 80 | 106 | 114 |

See component-pixels.json for every owner sprite, placement frame/depth, child clip/frame, tick, changed-channel counts and worst-pixel coordinates. Large component deltas are not explained by the isolated one-level arithmetic differences; an unfiltered-raster isolation is still needed before attributing them to filter math.

Other measured blockers: color3/5 exact (Matrix100%, chain100% differ by1); order2/4 exact (Glow100%/50% each one channel differs by1); scalar ColorMatrix20/24 exact; XG_rush21/21 entered frames match but234/5103 RGB channels differ, max135. See adjacent strict comparator reports.
