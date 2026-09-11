# You helper guard and owner-hit diagnostic r01

本轮只验证辅助鼬的防御接触与召唤者受击重叠路径，未修改 `game/`、`scripts/` 或冻结 runtime。所有比较沿用 canonical `fight_tick >= 0`，没有偏移或阈值放宽。

| Case | 固定输入与观察 | Fighter compare | Helper compare | 结论 |
| --- | --- | ---: | ---: | --- |
| 近距 guard | 佐助 x=300、卡卡西 x=350；召唤 10..13；卡卡西持续下防御；You/魂 | 482/482 matched | 482/482 matched | 原版 frame48→92；atm2 (`zl=11`) 在首个接触窗口破防并造成 4 hits。 |
| 远距 guard | 同配置，卡卡西 x=800；持续下防御 | 482/482 matched | 482/482 matched | 原版与 native 都未接触，You frame48→75→1，无伤害。 |
| early owner-hit | 佐助 x=300、卡卡西 x=350；召唤 10..13；攻击 20..23 | 722/722 matched | 722/722 matched | 佐助 tick25 受击后，You 仍执行攻击并造成后续伤害。 |
| held start30 | 同配置；卡卡西攻击 30..180 | 722/722 matched | 722/722 matched | 佐助 tick35 起受击/暂停；You frame48@62→92@63，tick100/116/132/148 命中，4 hits。 |
| held start20 | 同配置；卡卡西攻击 20..180 | **different**；首差 p1 tick93 | 722/722 matched | You 未接触：frame48@62→75@89→1@90，tick91 移除；不属于 helper 伤害中断。fighter 另有通用受击时序差：source tick93 frame861/x209/y-81/hstm20，native frame869/x205/y-85/hstm21；source tick94 的第四次受击未在 native 出现，单列为未解决边界。 |

## Reproduction and evidence

- 近距 fixture：`/private/tmp/sasuke-you-kakashi-guard-r01.json`；source/native reports：`you-helper-guard-production-compare-r01.json`、`you-helper-guard-fighter-compare-r01.json`、`you-helper-guard-helper-compare-r01.json`。
- 远距 fixture：`/private/tmp/sasuke-you-kakashi-guard-far-r01.json`；source/native reports：`you-helper-guard-far-fighter-compare-r01.json`、`you-helper-guard-far-helper-compare-r01.json`。
- early owner-hit reports：`you-helper-owner-hit-fighter-compare-r03.json`、`you-helper-owner-hit-helper-compare-r03.json`。
- held start30 reports：`you-helper-owner-hit-held-start30-native-r01.compare.json`、`you-helper-owner-hit-held-start30-helper-compare-r01.json`；source capture：`you-helper-owner-hit-held-start30-native-r01.events.jsonl.gz`。
- held start20 reports：`you-helper-owner-hit-held-native-r01.compare.json`、`you-helper-owner-hit-held-helper-compare-r01.json`；source capture：`you-helper-owner-hit-held-native-r01.events.jsonl.gz`。

源依据为 `scripts/fighter/fz/you.json`：frame48 的 nested `hitTest(...bdmn)` 命中才 `gotoAndPlay("攻击2")`；frame76 的 root `gotoAndStop(1)` 是未命中退出。owner 的 `onBeHit`/`beidax` 只更新 owner 受击状态，不包含停止 helper 的规则。近距 guard 的破防由源 `fangyu` 共用链和 You `atm2` 的 `zl=11` 决定，不是角色专用必中逻辑。

## Runtime and acceptance boundary

当前验证使用冻结 runtime：

```text
godot/helper_runtime.gd 53ca88306f272673b5f22555f87772cbcc346da9f07bc5f23473c1b32f1304fe
godot/combat_resolver.gd 1629558d0e1c0fd2350620784aac8fb328ce82b592ace3af9f498b432acb1332
godot/fighter_runtime.gd cbb079e264c2777610a2dfb33728906c75e72c20ad6751f2da2669677e78c07d
godot/generated/helpers/you/combat.json 4db767abd6c563eb630960c5e5bbef8841ddaa4426ccab58345172ee9fba4c49
```

本轮没有发现 You guard 或 owner-hit gating 的 source/native 行为差异，因此没有 runtime 修复。source-only `hits`/`atm1`/`atm2`/`atm3` 仍不是通用 helper comparator 的全部字段；上表的命中次数来自原始 source/native fighter 轨迹审计。held start20 的 fighter timing 差异保留为待定位边界，不得标作本轮通过。
