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
两者都以案例 ID + `missing native evidence` 硬失败。s02 当时这是明确拒绝的
接入桩，不支持导入任何成功收据，也不把 Godot 输出当原生证据。
未加此选项的 s01 案例与执行覆盖规则不变。

这项门槛可独立送审；捕获适配器、原生轨迹验证及像素对比是后续项。
见 [s02 证据](../evidence/sampling-upgrade/s02/README.md)；当前接入能力见下方 s27。

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

## s22：露琪亚执行证据

露琪亚（rukia）324/324 通过，39,528 条双方状态记录；缺案例报告硬失败，
恢复后复查 324/324 通过。分批累计 22/26 个角色、7,128/8,424 个案例，剩余 4 个。
原生 Flash 一致性、全局判定框、子显示列表、完整镜头、BitmapData 和 DoAction
仍是明确后续项，不阻塞本执行证据切片的合并；`production_admitted=false`，
`native_parity_proven=false`。见 [s22 证据](../evidence/sampling-upgrade/s22/README.md)。

## s23：佐助执行证据

佐助（sasuke）324/324 通过，39,528 条双方状态记录；缺案例报告硬失败，
恢复后复查 324/324 通过。分批累计 23/26 个角色、7,452/8,424 个案例，剩余 3 个。
原生 Flash 一致性、全局判定框、子显示列表、完整镜头、BitmapData 和 DoAction
仍是明确后续项，不阻塞本执行证据切片的合并；`production_admitted=false`，
`native_parity_proven=false`。见 [s23 证据](../evidence/sampling-upgrade/s23/README.md)。

## s24：一护执行证据

一护（yihu）324/324 通过，39,528 条双方状态记录；缺案例报告硬失败，
恢复后复查 324/324 通过。分批累计 24/26 个角色、7,776/8,424 个案例，剩余 2 个。
原生 Flash 一致性、全局判定框、子显示列表、完整镜头、BitmapData 和 DoAction
仍是明确后续项，不阻塞本执行证据切片的合并；`production_admitted=false`，
`native_parity_proven=false`。见 [s24 证据](../evidence/sampling-upgrade/s24/README.md)。

## s25：一角执行证据

一角（yijiao）324/324 通过，39,528 条双方状态记录；缺案例报告硬失败，
恢复后复查 324/324 通过。分批累计 25/26 个角色、8,100/8,424 个案例，剩余 1 个。
原生 Flash 一致性、全局判定框、子显示列表、完整镜头、BitmapData 和 DoAction
仍是明确后续项，不阻塞本执行证据切片的合并；`production_admitted=false`，
`native_parity_proven=false`。见 [s25 证据](../evidence/sampling-upgrade/s25/README.md)。

剩余角色为 `yulong`。Jinye/Yijiao 采样器残差仍为[已知差异](IMPORTER_KNOWN_GAPS.md)，本轮未解决，也不阻塞本执行证据切片。

## s26：雨龙执行证据与分批矩阵覆盖完成

雨龙（yulong）324/324 通过，39,528 条双方状态记录；缺案例报告硬失败，
恢复后复查 324/324 通过。分批累计 **26/26 个角色、8,424/8,424 个案例**，无剩余角色。
已归档的 26 份报告与现有生成器案例集合核对一致，无缺失或重复；未重跑已证明角色，
也未在本提交重新验证其全部轨迹。这是分批累计执行覆盖完成，不是同一版本的一次全阵容重跑。
`full_roster_execution_complete=true` 仅指上述累计执行证据；
`production_admitted=false`、`native_parity_proven=false` 保持不变。

原生 Flash 一致性、BitmapData、全局判定框、子显示列表、完整镜头和 DoAction，
以及 Jinye/Yijiao 采样器残差仍是明确后续项，不阻塞本执行证据切片。
见 [s26 证据](../evidence/sampling-upgrade/s26/README.md)及[已知差异](IMPORTER_KNOWN_GAPS.md)。

## s27：案例绑定的原生捕获适配器

s02 的拒绝桩现可通过 `--native-evidence DIR` 接收逐案例收据。
`python3 -m tools.sampling_native` 复用既有静态 move-case 探针和 Flash 捕获工具，
绑定完整 tape、构建配置、源 SWF、探针、播放器及产物哈希，并核对逐帧双角色记录、
准备姿态和结束事件。`run` 记录收据哈希；`check` 重新校验，缺失、错配或改动均硬失败。
静态案例以外的动态加载收据仍拒绝；绝对路径所指产物必须保留。

本轮仅以明确合成的单案例夹具验证正反向门槛，没有新原生捕获或像素一致性证明。
收据是可信本地构建的审计记录，不是防伪签名。`production_admitted=false`、
`native_parity_proven=false`；实际单案例原生捕获、随机/时钟对齐、BitmapData、判定框、
子显示列表、完整镜头和 DoAction 仍为后续项。Jinye/Yijiao 已知残差未改变。
见 [s27 证据与命令](../evidence/sampling-upgrade/s27/README.md)。

## s28：一个真实原生采样格

迪达拉地面近距离普攻单格通过实际 Flash 捕获：5,572 条事件、双方 0–60 tick
共 122 条状态记录，原生收据绑定并重验通过。同一 tape 经 `--native-evidence`
运行 Godot，明确为 **1/324**；缺失/错案例收据硬失败，恢复后通过。未标记项仍无需收据，
全 campaign 检查仍因其余 323 格缺原生证据而拒绝。未重跑已证明角色。

本轮仅证明真实捕获与收据接入，不比较逐帧行为或像素；
`production_admitted=false`、`native_parity_proven=false`。原生一致性、BitmapData、
判定框、子显示列表、完整镜头、DoAction 及 Jinye/Yijiao 残差保持后续项。
见 [s28 证据、命令及原始产物](../evidence/sampling-upgrade/s28/README.md)。

## s29：一个真实原生格的全局判定框采样

复用 s28 迪达拉 tape，增加可选 `--sampling-geometry` 原生观察器：同一根帧边界
扫描双方及源碰撞列表引用的援助/舞台候选框，记录原始脚本路径、实例 ID、初始化时点、
观察寿命、全局矩阵和局部矩形。61/61 采样、240 条框记录、9 个实例身份；攻击框在
 tick 13–14 出现，双方受击框每帧覆盖。零框按角色类别显式空数组；缺帧、缺框、
未知来源或观察器错误均拒绝。50 项聚焦测试及 19 项探针测试通过。

这里只证明原生根边界的现存碰撞候选框，不等于该帧必定可造成伤害，也不宣称帧内
短命实例、精确销毁时点或 Godot 几何一致性。`production_admitted=false`、
`native_parity_proven=false`；其他采样格、像素、子显示列表、完整镜头和 DoAction 保持后续项。
见 [s29 证据](../evidence/sampling-upgrade/s29/README.md)。

## s30：单格子显示列表与镜头观测（完整门槛仍拒绝）

迪达拉同一 tape 的真实原生捕获含 61/61 根帧、1,538 条 MovieClip 记录；
保留父子关系、深度、实例 ID、源帧、局部/全局矩阵、视口模式、scrollRect、
滤镜顺序及观察间创建/移除。源时间轴补充静态叶节点、clipDepth 和原始放置字段。
缺采样/缺子节点负例硬失败，恢复后结构检查通过。

完整门槛仍 exit 1：AImain frame 0 共 122 条、动态 xgmc0 未绑定 47 条；
动态 setMask 尚未采集。全部记录和缺口原样保留，不用根位置冒充完整镜头证明。
`production_admitted=false`、`native_parity_proven=false`；动态来源/遮罩、完整镜头、
BitmapData、DoAction 和其他采样格为后续项。见 [s30 证据](../evidence/sampling-upgrade/s30/README.md)。

## s31：单格 BitmapData 捕获与严格字节门槛

迪达拉原生真实捕获 61/61 张 600×400 黑底不透明图，58,560,000 个 RGBA 字节；
缺帧/缺行硬失败。新比较器要求两端相位、尺寸、颜色/alpha 语义和逐帧图像完整，
任何单通道差异均拒绝，不缩图、不放宽阈值。Godot 扩展复用同一 runner 的根观察器
终止接口，计划逐目标 tick 重放后读取真实 viewport；默认路径仍通过。

Godot 首次沙箱启动 SIGABRT 后，经用户批准的单命令提权已取得 61/61 张真实图像。
尺寸/不透明 RGBA 和图像哈希检查通过；严格比较 **0/61** 帧精确，18,630,929 个通道值
不同，最大差 255，gate exit 1。缺 Godot 图像负例拒绝，恢复后重验通过。
根冻结截图的舞台/角色显示与 HUD 差异原样保留；采像影响原生外部时钟，时钟及
渲染相位等价仍待证明。两个准入/一致性标志保持 false；
见 [s31 证据与逐帧差异](../evidence/sampling-upgrade/s31/README.md)。

## s32：单格真实 DoAction 入口覆盖

迪达拉同 tape 原生捕获 61/61 根观察点、394 次块入口、28 个源块（含启动）；
战斗观察 tick 内为 50 次入口、16 个块。执行前固定五个 SWF 的 1,072 项源清单，
475 个非主 SWF 的 DoAction 块插桩，447 个仍未访问、597 个脚本未插桩。
源 SWF/脚本哈希、路径、sprite/frame、实例路径与真实事件顺序均保留。
缺收据、缺事件/样本、删源义务或改源码身份都拒绝。

完整 AS 覆盖 gate 仍 exit 1：块入口不证明函数体/分支调用、clip-action 或 Godot
消费者已执行，不能据此让未知调用通过。未访问项是保守覆盖目标，不断言每项在此格可达。
本轮仅交付真实入口证据及明确不完整门槛；全阵容、语句/调用所有权、像素/时钟对齐等为
后续项。两个准入/一致性标志保持 false。见 [s32 证据](../evidence/sampling-upgrade/s32/README.md)。

## s33：单格真实 clip-action 处理器入口

复用 s32 清单/捕获器，新增 `--sampling-clipaction`，在非主 SWF 的原始
`load`/`enterFrame` 处理器内部观察实际调用，绑定 PlaceObject 路径与事件类型。
真实捕获 61/61 根样本、3,138 次处理器入口、12 个源处理器（战斗观察 tick 内 347 次）。
缺事件/样本、删源义务、错事件类型和不支持的包装形式均硬拒绝。

1,072 项源清单中 656 项插桩；剩余 616 未访问、416 未插桩均保留。
完整所有权 gate 仍 exit 1：处理器被调用不等于其内所有函数/分支均执行；
语句/调用、其他事件、主根处理器等仍是后续项。两个标志保持 false。
不重做 s29 几何，不要求全阵容或像素对齐；见 [s33 证据](../evidence/sampling-upgrade/s33/README.md)。

## s34：单格真实分支与调用点边界

迪达拉同格选定 `DefineSprite_542` 的 enterFrame 条件 `gameRunning()`，
保留原调用与求值次数，观察真假分支及 `doAllAction()` 前后边界。
原生 61/61 根样本、454 次完整执行（406 假、48 真）；另有 tick 10 的
一次调用只有前边界，下一入口已是不同实例，不能推断返回或生命周期。
选定边界 gate 保持 exit 1，完整 AS 所有权同样未证明；缺标记/删义务硬拒绝。
函数体、其他语句/分支、全阵容、像素/时钟与显示残差均是后续项，两标志 false。
见 [s34 证据](../evidence/sampling-upgrade/s34/README.md)。

## s35：第二个迪达拉单格原生捕获

新增 `didala__jump__neutral__ground__near`，仅这一格：原生 5,926 事件、
122 双方状态观察（tick 0–60），jump 意图 tick 10–12 与源按键读取验证通过。
案例绑定收据复验通过，Godot required-native 路径 1/324 执行无错误；
缺收据、错案例和缺样本拒绝，整批门槛仍拒绝其他未捕获格。
未重跑首格；本格几何/DL/镜头/BitmapData/DoAction/所有权与行为对照是后续项，
不将捕获完整性称为一致性，两标志 false。见 [s35](../evidence/sampling-upgrade/s35/README.md)。

## s36：jump 单格全局几何

仅 `didala__jump__neutral__ground__near`，复用 s29 未改动的几何探针。
真实原生 6,271 事件、61/61 根采样、242 条受击框、6 个实例身份；双方均纳入，
攻击/援助攻击/舞台攻击为空数组。缺整帧或缺单框负例均拒绝，原记录复验通过。
本格 DL/镜头、BitmapData、DoAction/所有权及 Godot 几何对照仍为后续项；
不将观测完整性称为原生一致性，两标志 false。见 [s36](../evidence/sampling-upgrade/s36/README.md)。

## s37：jump 单格子显示列表与镜头观测

仅 `didala__jump__neutral__ground__near`，复用 s30 未改动的探针/源绑定门槛。
原生 8,968 事件、61/61 结构采样、1,522 节点；缺样本/缺节点均拒绝。
完整显示/镜头 gate exit 1：双方 AImain 各 61 条 frame 0 缺源帧义务均保留，
动态遮罩所有权未证明；Stage/根矩阵/子树变换不等于完整镜头一致性。
本格 BitmapData、DoAction/所有权及完整渲染对照为后续项，两标志 false。
见 [s37](../evidence/sampling-upgrade/s37/README.md)。

## s38：jump 单格 BitmapData 严格比较

仅 `didala__jump__neutral__ground__near`，复用 s31 未改动的原生/Godot 图像路径。
原生 30,295 事件，双方各 61/61 张 600×400 不透明 RGBA 图像；收据与图像验证通过。
逐字节比较 0/61 精确，19,229,825 通道不同、最大差 255，gate exit 1；
缺帧/缺行/缺图像及单字节差异均拒绝。相位/外部时钟、像素一致性仍未证明，
本格 DoAction/所有权是后续项，两标志 false。见 [s38](../evidence/sampling-upgrade/s38/README.md)。

## s39：jump 单格 DoAction 入口覆盖

仅 `didala__jump__neutral__ground__near`，复用 s32 入口探针与严格门槛。
原生 6,196 事件、61/61 根样本、380 次入口/26 源块；战斗观察区间 50 次/12 块。
固定 1,072 项源清单，475 块插桩，449 未访问、597 未插桩逐项保留。
缺入口/根样本/源码义务均拒绝；完整 AS gate exit 1，入口不证明语句/函数体/分支。
本格 clip-action/调用所有权及既有显示/像素残差仍为后续项，两标志 false。
见 [s39](../evidence/sampling-upgrade/s39/README.md)。

## s40：jump 单格 clip-action 入口

仅 `didala__jump__neutral__ground__near`，复用 s33 探针与严格收据/清单门槛。
原生 9,427 事件、61/61 根样本、3,062 次处理器入口/13 源处理器（战斗区间 353 次）。
固定清单保留 617 未访问项、416 未插桩脚本；缺事件/样本/源码义务拒绝。
完整所有权 gate exit 1：处理器入口不证明内部调用/分支，后续再观测，两标志 false。
不重跑几何/图像或其他格。见 [s40](../evidence/sampling-upgrade/s40/README.md)。

## s41：jump 单格分支与调用点边界

仅 `didala__jump__neutral__ground__near`，复用 s34 原始条件/调用点探针。
原生 61/61 根样本、453 次完整执行（416 假、37 真及配对调用）；tick 10
另 1 次缺返回/结束标记，选定边界 gate exit 1，不能补造返回或推断生命周期。
六种标记删除、缺根样本/源码义务均拒绝；617 未访问、416 未插桩逐项保留。
完整 AS/被调函数体所有权仍未证明，两标志 false；其他维度不重跑。
见 [s41](../evidence/sampling-upgrade/s41/README.md)。

## s42：第三个迪达拉原生单格（dash）

仅 `didala__dash__neutral__ground__near`，原生 5,704 事件、122 双方状态；
原生 l/76 按键意图 tick 10–12 与源读取匹配。收据复验及 Godot required-native
单格 1/324 执行通过；缺收据/错案例/缺样本拒绝，整批检查仍拒绝其他缺收据格。
本格几何/DL/镜头/BitmapData/DoAction/所有权均为后续项，不重跑 attack/jump，
不宣称原生一致性，两标志 false。见 [s42](../evidence/sampling-upgrade/s42/README.md)。

## s43：dash 单格全局几何

仅 `didala__dash__neutral__ground__near`，复用既有几何探针与严格门槛。
真实原生 6,236 事件、61/61 根采样、233 受击框、6 实例身份；双方均纳入，
攻击/援助攻击/舞台攻击数组为空。缺整帧/单框均拒绝，原记录复验通过。
Godot 几何对照及本格 DL/镜头、BitmapData、DoAction/所有权均为后续项，
两标志 false，不宣称原生一致性。见 [s43](../evidence/sampling-upgrade/s43/README.md)。

## s44：dash 单格子显示列表与镜头

仅 `didala__dash__neutral__ground__near`，复用既有显示/镜头探针。
原生 8,950 事件、61/61 结构样本、1,497 节点；缺样本/节点拒绝。
完整 gate exit 1：双方 AImain 的 122 条 frame 0 缺源帧义务及动态遮罩缺口保留。
Stage/根矩阵/子树观测不等于完整镜头一致性，两标志 false；本格 BitmapData/
DoAction 是后续项。见 [s44](../evidence/sampling-upgrade/s44/README.md)。

## s45：dash 单格 BitmapData 严格比较

仅 `didala__dash__neutral__ground__near`，复用既有原生/Godot 图像路径。
原生 30,436 事件，双方各 61/61 张 600×400 不透明 RGBA 图像；收据及图像验证通过。
严格比较 0/61 精确，20,354,476 通道不同、最大差 255，gate exit 1；缺帧/行/图像
及单字节差异拒绝。相位/时钟与像素一致性未证明，两标志 false，本格 DoAction
为后续项。见 [s45](../evidence/sampling-upgrade/s45/README.md)。

## s46：dash 单格 DoAction 入口

仅 `didala__dash__neutral__ground__near`，复用既有入口探针。
原生 6,156 事件、61/61 根样本、373 入口/24 源块（战斗区间 47 次/10 块）。
固定清单保留 451 未访问块、597 未插桩脚本；缺入口/样本/源码义务拒绝。
完整 AS gate exit 1，入口不证明函数体/调用/分支，clip-action/调用加深为后续项。
两标志 false。见 [s46](../evidence/sampling-upgrade/s46/README.md)。

## s47：dash 单格 clip-action 入口

仅 `didala__dash__neutral__ground__near`，复用既有处理器入口探针。
原生 9,629 事件、61/61 根样本、3,117 次入口/9 源处理器（战斗区间 334 次）。
623 未访问项、416 未插桩脚本保留；缺事件/样本/源码义务拒绝。
完整所有权 gate exit 1，入口不证明内部调用/分支，两标志 false；
调用点加深为后续项。见 [s47](../evidence/sampling-upgrade/s47/README.md)。

## s48：dash 单格分支与调用点

仅 `didala__dash__neutral__ground__near`，复用既有源码绑定调用点探针。
原生 61/61 根样本、460 次完整执行（416 假/44 真及配对调用）；tick 10
另 1 次缺返回/结束标记，选定边界 gate exit 1，不补造返回或推断生命周期。
缺标记/样本/源码义务拒绝；623 未访问、416 未插桩保留，完整 AS 所有权未证明。
两标志 false。见 [s48](../evidence/sampling-upgrade/s48/README.md)。

## s49：第四个迪达拉原生单格（ranged）

仅 `didala__ranged__neutral__ground__near`，原生 4,736 事件、122 双方状态；
原生 u/85 意图 tick 10–12 与源读取匹配。收据复验及 Godot required-native
单格 1/324 执行通过；缺收据/错案例/缺样本拒绝，整批检查因其他缺收据格 exit 1。
本格几何/DL/镜头/BitmapData/DoAction/所有权均为后续项，不重跑其他格；
两标志 false。见 [s49](../evidence/sampling-upgrade/s49/README.md)。

## s50：ranged 单格几何捕获（完整门槛拒绝）

仅 `didala__ranged__neutral__ground__near`：原生 5,066 事件、收据复验通过。
原始几何有 61 对开始/结束、199 框，但 tick 14 的 `p1.mc.abcd.hitmc`
（DefineSprite_69/frame_1）报 missing-source-list，完整 gate exit 1，不能称 61/61 完整。
仅 tick 0–13 前缀 14 样本/54 框验证通过；缺样本/框负例拒绝。
需逐项读取目标容器/pn 与三个源数组，区分未初始化或所有权问题，不默认空列表。
Godot 几何对照及其他维度仍后续，两标志 false。见 [s50](../evidence/sampling-upgrade/s50/README.md)。
