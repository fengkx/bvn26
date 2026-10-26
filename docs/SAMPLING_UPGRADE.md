# 输入采样升级：执行覆盖先行

这是 PR #48 fail-loud 安全网之后的独立工作，不改变该 PR 的送审标准。
`production_admitted=false`；它仍是证据状态，不是 FilterGroup 的运行时开关。

## 首个切片

`python3 -m tools.sampling_matrix` 从已发布角色目录自动生成确定性输入 tape，
通过既有 `move_case_reference.gd` 执行，不修改战斗运行时或原生基准。

- 26 名已发布基础角色；未发布原始角色、其他形态不冒充已覆盖。
- 六个动作键：J/K/L/U/I/O 对应 attack/jump/dash/ranged/special/summon。
- 九种方向：无方向、四个单方向、四个对角方向。
- 地面/空中 × 近/中/远；每角色 324 个组合，共 8,424。
- 方向是绝对键位，不是相对朝向。左右出生点、纯方向无动作键、长按/连按、
  受击/资源不足/变身等应作为后续显式维度，不能宣称此矩阵穷举全部操作。

测试参数：现世、P1 x=100，P2 与其相距 50/150/300、双方气量 300，
固定一护对手及我爱罗/魂援助。距离名只是测试分桶，不是原版攻击范围判断。
每例新战斗观察 0–60 tick；空中例先在 [1,2) 按跳跃，目标按键在 [10,13)。
第 10 tick 的输入前观察必须实际满足 `touch` 地面/空中条件，否则硬失败，
不强行改高度，也不把失败准备过程计为空中覆盖。

矩阵清单锁定目录哈希与每条 tape 哈希，读取时重算整个笛卡尔积和 tape 内容。
执行 gate 核对双方每个 tick 的完整状态字段和镜头，拒绝缺帧、重复、乱序、
非有限坐标、准备姿态错误、失败进程、漏跑案例及其他 campaign 的报告。
选跑结果始终显示实际数量；只有 `check` 覆盖整个 campaign 才打印
`MATRIX_EXECUTION_COVERAGE_OK`。子角色 campaign 明确标记 `fighter_subset`。
该 gate 不是防伪证明，也不验证 Flash 行为一致。

```sh
python3 -m tools.sampling_matrix generate --output /tmp/bvn-matrix
python3 -m tools.sampling_matrix run --campaign /tmp/bvn-matrix \
  --output /tmp/bvn-matrix-run --godot /path/to/godot
python3 -m tools.sampling_matrix check --campaign /tmp/bvn-matrix \
  --output /tmp/bvn-matrix-run
```

首轮证据与局部选跑命令见 [s01](../evidence/sampling-upgrade/s01/README.md)。

## 后续数据链与独立门槛

1. **输入与环境**：相同 tape 接入 native Flash 插桩；同时锁源 SWF、探针、
   引擎和产物哈希，保存随机/外部 timer 输入。验证每个采样状态的准备条件。
   目前不自动补 timer 输入、不声明目标招式必然触发。
2. **逐帧几何**：复用既有 geometry_probe；采集所有活动攻击/受击框的源路径、
   实例寿命和全局变换。零框是显式空数组，缺采样是错误；不能只抓当前角色局部框。
3. **子显示列表与镜头**：保留层级、深度、符号、源帧、矩阵、mask/clip、
   创建/移除及滤镜顺序。现有 presentation 仅有根位置，不等于完整镜头证据。
4. **BitmapData**：在一致的根观察相位捕获 native 像素与实际 Godot 输出；
   检查尺寸/颜色与 alpha 语义后逐字节比较。缺帧、缺图和任一通道差异硬失败。
   Jinye/Yijiao 残差可作为已知负例，不上传原生图作纹理、不重写参考。
5. **DoAction 执行覆盖**：源清单给每个 action block 稳定身份
   （SWF 哈希、sprite、frame/tag 位置）；native 探针记录真正执行的 block 及顺序。
   用执行事件对照计划范围，缺事件/未访问 block 输出精确列表。静态存在、编译成功、
   父帧访问都不能替代执行证明；clip-action 的事件类型与实例身份另行保留。

这五类证据应分别报告 coverage 和 parity，不能用一个总绿色掩盖未采集项。
本切片没有 Flash 捕获/像素/DoAction gate，`native_parity_proven` 恒为 false。
完整输入矩阵、生产 54 图和 AS 所有权仍是后续工作，不回填 PR #48 已知差异。

## s02：原生证据预留门槛

生成时添加 `--require-native`，会把要求同时写进案例和矩阵清单。
`run` 检查选中的案例，`check` 检查整个矩阵；必需原生证据尚未接入时，
两者都以案例 ID + `missing native evidence` 硬失败。当前这是明确拒绝的
接入桩，不支持导入任何成功收据，也不把 Godot 输出当原生证据。
未加此选项的 s01 案例与执行覆盖规则不变。

这项门槛可独立送审；捕获适配器、原生轨迹验证及像素对比是后续项。
见 [s02 证据](../evidence/sampling-upgrade/s02/README.md)。

## s03：额外角色执行证据

茶渡（chad）完整矩阵 324/324 通过，39,528 条双方状态记录；缺一条案例结果
的报告仍硬失败，恢复后覆盖检查通过。与 s01 迪达拉合计已证明 2/26 个角色、
648/8,424 个案例，其余 24 个角色保持后续项；不是原生一致性证明。
见 [s03 证据](../evidence/sampling-upgrade/s03/README.md)。

## s04：恋次执行证据

恋次（renji）324/324 通过，39,528 条双方状态记录；缺案例报告仍硬失败，
恢复后通过。分批累计迪达拉、茶渡、恋次 3/26 个角色、972/8,424 个案例；
剩余 23 个角色继续作为后续项，未声明原生一致性。
见 [s04 证据](../evidence/sampling-upgrade/s04/README.md)。

## s05：小李和宁次执行证据

小李（lee）、宁次（neji）分别 324/324 通过，各 39,528 条双方状态记录；
两份缺案例报告均硬失败，恢复后通过。分批累计 5/26 个角色、1,620/8,424 个案例；
剩余 21 个角色仍是后续项，未声明原生一致性。
见 [s05 证据](../evidence/sampling-upgrade/s05/README.md)。

## s06：樱执行证据

樱（sakura）324/324 通过，39,528 条双方状态记录；缺案例报告硬失败，
恢复后通过。分批累计 6/26 个角色、1,944/8,424 个案例；剩余 20 个角色
仍是后续项，未声明原生一致性。见 [s06 证据](../evidence/sampling-upgrade/s06/README.md)。

## s07：银执行证据

银（yin）324/324 通过，39,528 条双方状态记录；缺案例报告硬失败，
恢复后通过。分批累计 7/26 个角色、2,268/8,424 个案例；剩余 19 个角色
仍是后续项，未声明原生一致性。见 [s07 证据](../evidence/sampling-upgrade/s07/README.md)。

## s08：剑八执行证据

剑八（jianba）324/324 通过，39,528 条双方状态记录；缺案例报告硬失败，
恢复后通过。分批累计 8/26 个角色、2,592/8,424 个案例；剩余 18 个角色
仍是后续项，未声明原生一致性。见 [s08 证据](../evidence/sampling-upgrade/s08/README.md)。

## s09：重吾执行证据

重吾（juggo）324/324 通过，39,528 条双方状态记录；缺案例报告硬失败，
恢复后通过。分批累计 9/26 个角色、2,916/8,424 个案例；剩余 17 个角色
仍是后续项，未声明原生一致性。见 [s09 证据](../evidence/sampling-upgrade/s09/README.md)。

## s10：小南执行证据

小南（konan）324/324 通过，39,528 条双方状态记录；缺案例报告硬失败，
恢复后通过。分批累计 10/26 个角色、3,240/8,424 个案例；剩余 16 个角色
仍是后续项，未声明原生一致性。见 [s10 证据](../evidence/sampling-upgrade/s10/README.md)。

## s11：白哉执行证据

白哉（byakuya）324/324 通过，39,528 条双方状态记录；缺案例报告硬失败，
恢复后复查 324/324 通过。分批累计 11/26 个角色、3,564/8,424 个案例，剩余 15 个。
原生 Flash 一致性、全局判定框、子显示列表、完整镜头、BitmapData 和 DoAction
仍是明确后续项，不阻塞本执行证据切片的合并；`production_admitted=false`。
见 [s11 证据](../evidence/sampling-upgrade/s11/README.md)。

## s12：带土执行证据

带土（daitu）324/324 通过，39,528 条双方状态记录；缺案例报告硬失败，
恢复后复查 324/324 通过。分批累计 12/26 个角色、3,888/8,424 个案例，剩余 14 个。
原生 Flash 一致性、全局判定框、子显示列表、完整镜头、BitmapData 和 DoAction
仍是明确后续项，不阻塞本执行证据切片的合并；`production_admitted=false`。
见 [s12 证据](../evidence/sampling-upgrade/s12/README.md)。

## s13：我爱罗执行证据

我爱罗（gaara）324/324 通过，39,528 条双方状态记录；缺案例报告硬失败，
恢复后复查 324/324 通过。分批累计 13/26 个角色、4,212/8,424 个案例，剩余 13 个。
原生 Flash 一致性、全局判定框、子显示列表、完整镜头、BitmapData 和 DoAction
仍是明确后续项，不阻塞本执行证据切片的合并；`production_admitted=false`。
见 [s13 证据](../evidence/sampling-upgrade/s13/README.md)。

## s14：鼬执行证据

鼬（itachi）324/324 通过，39,528 条双方状态记录；缺案例报告硬失败，
恢复后复查 324/324 通过。分批累计 14/26 个角色、4,536/8,424 个案例，剩余 12 个。
原生 Flash 一致性、全局判定框、子显示列表、完整镜头、BitmapData 和 DoAction
仍是明确后续项，不阻塞本执行证据切片的合并；`production_admitted=false`，
`native_parity_proven=false`。见 [s14 证据](../evidence/sampling-upgrade/s14/README.md)。

## s15：自来也执行证据

自来也（jiraiya）324/324 通过，39,528 条双方状态记录；缺案例报告硬失败，
恢复后复查 324/324 通过。分批累计 15/26 个角色、4,860/8,424 个案例，剩余 11 个。
原生 Flash 一致性、全局判定框、子显示列表、完整镜头、BitmapData 和 DoAction
仍是明确后续项，不阻塞本执行证据切片的合并；`production_admitted=false`，
`native_parity_proven=false`。见 [s15 证据](../evidence/sampling-upgrade/s15/README.md)。

## s16：卡卡西执行证据

卡卡西（kakashi）324/324 通过，39,528 条双方状态记录；缺案例报告硬失败，
恢复后复查 324/324 通过。分批累计 16/26 个角色、5,184/8,424 个案例，剩余 10 个。
原生 Flash 一致性、全局判定框、子显示列表、完整镜头、BitmapData 和 DoAction
仍是明确后续项，不阻塞本执行证据切片的合并；`production_admitted=false`，
`native_parity_proven=false`。见 [s16 证据](../evidence/sampling-upgrade/s16/README.md)。

## s17：蓝染执行证据

蓝染（lanran）324/324 通过，39,528 条双方状态记录；缺案例报告硬失败，
恢复后复查 324/324 通过。分批累计 17/26 个角色、5,508/8,424 个案例，剩余 9 个。
原生 Flash 一致性、全局判定框、子显示列表、完整镜头、BitmapData 和 DoAction
仍是明确后续项，不阻塞本执行证据切片的合并；`production_admitted=false`，
`native_parity_proven=false`。见 [s17 证据](../evidence/sampling-upgrade/s17/README.md)。

## s18：鸣人执行证据

鸣人（minren）324/324 通过，39,528 条双方状态记录；缺案例报告硬失败，
恢复后复查 324/324 通过。分批累计 18/26 个角色、5,832/8,424 个案例，剩余 8 个。
原生 Flash 一致性、全局判定框、子显示列表、完整镜头、BitmapData 和 DoAction
仍是明确后续项，不阻塞本执行证据切片的合并；`production_admitted=false`，
`native_parity_proven=false`。见 [s18 证据](../evidence/sampling-upgrade/s18/README.md)。

## s19：大蛇丸执行证据

大蛇丸（orochimaru）324/324 通过，39,528 条双方状态记录；缺案例报告硬失败，
恢复后复查 324/324 通过。分批累计 19/26 个角色、6,156/8,424 个案例，剩余 7 个。
原生 Flash 一致性、全局判定框、子显示列表、完整镜头、BitmapData 和 DoAction
仍是明确后续项，不阻塞本执行证据切片的合并；`production_admitted=false`，
`native_parity_proven=false`。见 [s19 证据](../evidence/sampling-upgrade/s19/README.md)。

## s20：佩恩执行证据

佩恩（pain）324/324 通过，39,528 条双方状态记录；缺案例报告硬失败，
恢复后复查 324/324 通过。分批累计 20/26 个角色、6,480/8,424 个案例，剩余 6 个。
原生 Flash 一致性、全局判定框、子显示列表、完整镜头、BitmapData 和 DoAction
仍是明确后续项，不阻塞本执行证据切片的合并；`production_admitted=false`，
`native_parity_proven=false`。见 [s20 证据](../evidence/sampling-upgrade/s20/README.md)。

## s21：日番谷执行证据

日番谷（rifagu）324/324 通过，39,528 条双方状态记录；缺案例报告硬失败，
恢复后复查 324/324 通过。分批累计 21/26 个角色、6,804/8,424 个案例，剩余 5 个。
原生 Flash 一致性、全局判定框、子显示列表、完整镜头、BitmapData 和 DoAction
仍是明确后续项，不阻塞本执行证据切片的合并；`production_admitted=false`，
`native_parity_proven=false`。见 [s21 证据](../evidence/sampling-upgrade/s21/README.md)。
