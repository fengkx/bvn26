# Remaining assist roster

All 17 entries use the original helper SWF, frame scripts, placement lifetimes and exported artwork. The local selector and matchmaking service catalog now contain all 26 assist IDs from the source catalog.

The diagnostic fixtures start Ichigo and Naruto at x=300 and x=450. Every assist has a P1 summon. The P2 cases repeat the summon from the other side. Each fixture includes its exact inputs, original Flash projector events and build configuration, native actor trace and helper projection. The final column records the opponent's health at the end of the P1 fixture (initial HP 1000).

| Assist | Source ID | Cases | Rows per stream | P2 final HP |
| --- | --- | ---: | ---: | ---: |
| 手鞠 | shouju | 1 | 372 | 825 |
| 夜一 | yeyi | 2 | 914 | 800 |
| 天天 | tenten | 2 | 914 | 800 |
| 志志雄 | shishio | 1 | 372 | 680 |
| 自来也 | jiraiya | 1 | 372 | 700 |
| 蒂雅 | harribel | 1 | 372 | 890 |
| 葛力姆乔 | grimmjow | 1 | 372 | 690 |
| 四代 | sidai | 2 | 914 | 800 |
| 史塔克 | stake | 2 | 804 | 870 |
| 纲手 | gangshou | 1 | 372 | 880 |
| 八千流 | baqianliu | 1 | 372 | 900 |
| 牛头白一护 | yihuxuliu | 1 | 372 | 720 |
| 雏田 | zhitian | 1 | 372 | 850 |
| 碎蜂 | soifong | 2 | 914 | 600 |
| 水月 | shuiyue | 1 | 372 | 900 |
| 涅音梦 | nemu | 2 | 914 | 860 |
| 斑 | ban | 2 | 914 | 700 |

The 24 cases match 10,008 rows on each stream. The strict comparisons cover 14 actor fields and six helper fields. Full audiovisual parity, browser gameplay, exhaustive guard/interrupt boundaries and rollback across the entire roster remain open. The service catalog requires deployment before live matchmaking exposes the new IDs.

Ban's moving clip exposes its attack name in callback order. Charging helpers can retain or replace the moving clip at a contact jump. Soifong's child projectile stops at contact and its renamed attack becomes observable after the target frame script. Tenten's five projectiles reference an unbound slot on their immediate holder and continue moving. These behaviors are exercised by the retained replays.
