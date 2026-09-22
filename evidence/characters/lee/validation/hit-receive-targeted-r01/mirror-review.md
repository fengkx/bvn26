# Lee 招1镜像守防：Source / native contact

状态：同输入 source/native 接触证据已归档；只验本次镜像守防，不推广为双向全覆盖。

## Fixture 与运行来源

- Fixture：`fixtures/lee-278-magichit1-guard-mirror-targeted-r01-source.json`（source）和对应 `*-native.json`。两者同为 P1 小李、P2 一护；双方 energy 300；P1 起始 X=350、P2 X=300；P1 `ranged`/U 在 fight tick 10–13，P2 `down`/下箭持续 1–300。native fixture 只额外带 geometry probe。
- P1 alias/key：`ranged=85`（U）；P2 `下箭=40`。Source `input_bindings` 与逐次 `key_read` 证明该映射实际有效：P1 key 85 在 fight tick 10 被读取为 true；P2 key 40 在 fight tick 1–299 共 1142 次读取为 true。
- Source run：`lee-278-magichit1-guard-mirror-targeted-r01`，600 fight ticks。原始采集在 `/private/tmp/lee-hit-receive-targeted-r01/source-mirror-r02/capture/events.jsonl`；build/runtime副本仍在同一 `/private/tmp` build 目录。整理后的 source artifacts 在 `mirror-source/events.jsonl/`。
- Native：`mirror-native/native-r01.json`（602 actor rows）及 `.contacts.json`。当前 runtime 的 test-only probe 运行；没有修改生产实现。

## 接触与结果

Source 在 fight tick 25 / display 504：`source_hit_test` seq 3921 报 `hit=true`，P2 的 `bdmn` 对 P1 `zh1atm`。同一 callback packet seq 3922 是 `pw=50, zl=5, htype=被打, branch=blocked`。按源分支 `zl > 10` 才破防，因此这是守住的招1，不是破防。

Native 的对应 `hit_contact` seq 674 记录 P1 `zh1atm`、Lee source frame 293，P2 防御动作 `防御2`、facing=1、ql=300、contact前 hp=1000。Native tick 300 末 P2 hp=995、仍防御、hits=0；这与源 `blocked` 分支的 5 点防御损伤及不加 hits 一致。双方都面向对手：Source fight tick 25 `state` 为 P1 x=338.2、xscale=-100，P2 x=283.2、xscale=+100；Native 相同相对 tick 行记录相同 X 与朝向（原始 tick0 的朝向在首个站立回调后翻转）。Source receiver packet 的 facing=100（守方右向），native defender facing=1。镜像位置与真实朝向均来自该场次轨迹，而非静态初始设置推断。

| 空间量 | Source `getBounds(_root.game)` | Native `*_game_bounds` |
|---|---:|---:|
| P1 `zh1atm` | x=301.30..337.15, y=-96.50..-21.40 | x=301.30..337.15, y=-96.50..-21.40 |
| P2 `bdmn` | x=280.95..311.55, y=-78.35..-26.05 | x=280.95..311.55, y=-78.30..-26.00 |

坐标边沿约 0.05 px 的差值保留在原始数据中；用户已接受此级别差异为可忽略，本报告不把它认定为缺陷。两端在相同源帧、攻击实例、世界重叠关系和守防结果上对应。

## SHA-256

- source fixture: `ba6a19883264d2bca8bdfd2966e6bc4eaca6699d8fcf1d98a79b8ab89217fb50`
- native fixture: `f8c64d709c76fce92eb699d8b69568950371ba8fb669ffe3b30e19ccdeb3d054`
- parsed source events: `3eb2957a51ff528ff43da515ae56a0faeb4e1b1e03ee15840441d2779aed6caf`
- native actor rows: `faa3afbf86bde185568a034f3aba14607f755f1d539f4905eb2d4e0040c68287`
- native contacts: `f4356e1ad00e62a41577bf04fbc7d575b745b3dfa184ce946462ff1352e66de7`
- source hit/receive instrumentation: `2c9197ef31dfd91f307a4da312351809e68ad145c35f1baf231ec3e7e5bcea11`
