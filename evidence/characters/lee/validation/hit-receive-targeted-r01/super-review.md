# Lee 超必杀九段命中与防御

结论限于这次同输入的九个接触点。原版采集为 1200 帧，Godot 回放为 300 fight ticks（602 条角色状态行）；九个接触均落在共同观测窗口内。原版与 Godot 的接触锚点、角色位置/朝向、攻击实例和防御结果对应。此结果不代表 1200 帧全程等价。

P1 小李以 I 发动超必杀，P2 一护持续按下防御。原版逐段产生八次 `zl=3`、反应“被打”、`blocked` 接触；每次防御扣 4 HP，连击数保持 0。第九次为 `cbsatm`，`zl=13`、反应“击飞”、`break`，随后 native P2 状态为 HP 818、`hits=1`。这区分了前八段削血与末段破防，不能把整招都归为破防。

| 相对 fight tick | 原版 display tick | 实例 / 源帧 | 结果 | 原版 receiver HP 前值 | Native receiver HP 前值 |
|---:|---:|---|---|---:|---:|
| 71 | 549 | cbs1atm / 854 | zl3，blocked | 1000 | 1000 |
| 87 | 565 | cbs2atm / 864 | zl3，blocked | 996 | 996 |
| 102 | 580 | cbs3atm / 873 | zl3，blocked | 992 | 992 |
| 116 | 594 | cbs4atm / 881 | zl3，blocked | 988 | 988 |
| 133 | 611 | cbs1atm / 892 | zl3，blocked | 984 | 984 |
| 149 | 627 | cbs2atm / 902 | zl3，blocked | 980 | 980 |
| 164 | 642 | cbs3atm / 911 | zl3，blocked | 976 | 976 |
| 178 | 656 | cbs4atm / 919 | zl3，blocked | 972 | 972 |
| 200 | 678 | cbsatm / 935 | zl13，break | 968 | 968 |

九个接触的攻击框与 P2 `bdmn` 世界框逐边核对，最大差约 0.0501 px；用户已接受该级别差异为可忽略。未见更大的落点偏移。差值及两侧原始 bounds 均保留在 JSON 证据中。

source 原始事件位于 `super-source/events.jsonl/events.jsonl`，对应 `source_hit_test` / `source_guard_packet` 成对记录；native 对应 `super-native/native-r01.json.contacts.json`。source 和 native 的 fight-tick 记录基准不同，native contact event 的 fightTick 比 source 多 307；按该固定偏移配对后九组相对 tick 一致。完整路径、SHA-256 与 build 信息见 `targeted-manifest.json`。

没有修改生产运行时代码。
