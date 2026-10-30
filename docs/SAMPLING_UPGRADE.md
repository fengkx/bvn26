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

## s51：ranged 单格子显示列表与镜头

仅 `didala__ranged__neutral__ground__near`：真实原生 8,083 事件，61/61 样本、
1,512 节点记录，收据与结构校验通过；缺样本/角色节点拒绝，恢复后复验通过。
完整显示/镜头 gate exit 1：122 条 AImain 源帧缺口与 70 条特效层符号绑定缺口保留。
动态 mask、完整相机对照仍未证明；s50 几何来源缺口不因本次采样解除。
BitmapData/DoAction 为后续薄切片，两标志 false。见 [s51](../evidence/sampling-upgrade/s51/README.md)。

## s52：ranged 单格 BitmapData 与严格 RGBA 比较

仅 `didala__ranged__neutral__ground__near`：真实 Flash/Godot 各 61/61 图，
原生 29,273 事件，收据/图片校验通过；严格比较 0/61 精确，
24,121,725 通道不同、8,970,029 像素不同，最大 Δ255，gate exit 1。
缺原生帧/行、缺 Godot 图片及单通道修改均拒绝，恢复后复验。
时钟/阶段、画面构图与渲染差异未归因；s50 几何和 s51 显示绑定缺口仍保留。
DoAction 为后续薄切片，两标志 false。见 [s52](../evidence/sampling-upgrade/s52/README.md)。

## s53：ranged 单格 DoAction 入口覆盖

仅 `didala__ranged__neutral__ground__near`：原生 5,134 事件、61/61 根样本，
374 次入口/36 个源块；战斗窗口 39 次入口/23 块。收据与结构收集通过。
固定 1,072 条源码清单中 475 块插桩，439 未访问、597 未插桩保留，完整 AS gate exit 1。
删除入口、样本或源码义务均拒绝，恢复后复验；入口不证明语句/调用/分支所有权。
clip-action/call 为后续薄切片，两标志 false。见 [s53](../evidence/sampling-upgrade/s53/README.md)。

## s54：ranged 单格 clip-action 入口

仅 `didala__ranged__neutral__ground__near`：原生 7,981 事件、61/61 根样本，
2,933 次 clip 入口/12 源处理器（战斗窗口 296 次），另有 371 次帧块入口/36 块。
收据与结构收集通过；缺事件/样本/源码义务拒绝，恢复后复验。
固定清单保留 608 未访问项（439 帧块/169 处理器）、416 未插桩脚本，完整 AS gate exit 1。
内部调用/分支、精确生命周期及既有几何/显示/像素差异仍后续，两标志 false。
见 [s54](../evidence/sampling-upgrade/s54/README.md)。

## s55：ranged 单格调用点与真假分支

仅 `didala__ranged__neutral__ground__near`：原生 9,130 事件、61/61 根样本；
选定 enterFrame 中 gameRunning→doAllAction 有 417 次完整观察（396 假/21 真且调用前后配对）。
另一次 tick 10 真分支到 call_before 后缺 call_after/end，选定边界 gate exit 1，未补造返回。
六类缺标记、缺样本/事件/源码义务均拒绝，原始诊断复验；608 未访问、416 未插桩保留。
callee 内部与完整 AS 所有权未证明，两标志 false。见 [s55](../evidence/sampling-upgrade/s55/README.md)。

## s56：第五个迪达拉原生单格（special）

仅 `didala__special__neutral__ground__near`：原生 4,647 事件、122 双方状态，
原生 i/73 意图 tick 10–12 与源按键读取一致；收据复验、Godot required-native
单格 1/324 执行通过，无错误。缺收据/错案例/缺样本拒绝；整批因其他格缺收据 exit 1。
未重跑前四格；本格几何/DL/镜头/BitmapData/DoAction/所有权均为后续项。
不宣称玩法/像素一致，两标志 false。见 [s56](../evidence/sampling-upgrade/s56/README.md)。

## s57：special 单格全局几何（完整门槛拒绝）

仅 `didala__special__neutral__ground__near`：原生 5,000 事件、61/61 结构样本，
177 hurt/27 attack 框记录、13 实例 ID；收据/结构校验通过，缺样本/框负例拒绝。
完整 gate exit 1：tick 11 的 p1（源运行帧 474）没有 receiver，tick 10/12 有 bdmn/mian。
须核该帧放置/移除/初始化与观测阶段，不补造框、不推断无敌、不忽略该 tick。
完整原生几何及 Godot 对照未证明；其他维度后续，两标志 false。见 [s57](../evidence/sampling-upgrade/s57/README.md)。

## s58：special 单格子显示列表与镜头

仅 `didala__special__neutral__ground__near`：原生 7,716 事件、61/61 样本、
1,567 节点记录，收据与结构校验通过；缺样本/角色节点拒绝，恢复后复验。
完整显示/镜头 gate exit 1：122 条 AImain 源帧缺口、142 条特效层符号缺口保留。
动态 mask/完整镜头对照未证明，s57 tick 11 几何缺口不因本次采样解除。
BitmapData/DoAction 后续，两标志 false。见 [s58](../evidence/sampling-upgrade/s58/README.md)。

## s59：special 单格 BitmapData 与严格 RGBA 比较

仅 `didala__special__neutral__ground__near`：真实 Flash/Godot 各 61/61 图，
原生 28,948 事件，收据/图像校验通过；严格比较 0/61 精确，
20,213,338 通道、8,090,967 像素不同，最大 Δ255，gate exit 1。
缺原生帧/行、缺 Godot 图和单通道修改均拒绝，恢复后复验。
时钟/阶段与渲染差异未归因，s57/s58 缺口保留；DoAction 后续，两标志 false。
见 [s59](../evidence/sampling-upgrade/s59/README.md)。

## s60：special 单格 DoAction 入口覆盖

仅 `didala__special__neutral__ground__near`：原生 5,147 事件、61/61 根样本，
400 次入口/29 个源块；战斗窗口 45 次入口/16 块。收据与结构收集通过。
固定 1,072 条源码清单中 475 块插桩，446 未访问、597 未插桩保留，完整 AS gate exit 1。
删除入口、样本或源码义务均拒绝，恢复后复验；入口不证明语句/调用/分支所有权。
clip-action/call 后续，两标志 false。见 [s60](../evidence/sampling-upgrade/s60/README.md)。

## s61：special 单格 clip-action 入口

仅 `didala__special__neutral__ground__near`：原生 7,701 事件、61/61 根样本，
2,873 次 clip 入口/12 源处理器（战斗窗口 254 次），另有 374 次帧块入口/29 块。
收据与结构收集通过；缺事件/样本/源码义务拒绝，恢复后复验。
固定清单保留 615 未访问项（446 帧块/169 处理器）、416 未插桩脚本，完整 AS gate exit 1。
内部调用/分支、精确生命周期及既有几何/显示/像素差异仍后续，两标志 false。
见 [s61](../evidence/sampling-upgrade/s61/README.md)。

## s62：special 单格调用点与真假分支

仅 `didala__special__neutral__ground__near`：原生 8,858 事件、61/61 根样本；
选定 enterFrame 中 gameRunning→doAllAction 有 407 次完整观察（397 假/10 真且调用前后配对）。
另一次 tick 10 真分支到 call_before 后缺 call_after/end，选定边界 gate exit 1，未补造返回。
六类缺标记、缺样本/事件/源码义务均拒绝，原始诊断复验；615 未访问、416 未插桩保留。
callee 内部与完整 AS 所有权未证明，两标志 false。见 [s62](../evidence/sampling-upgrade/s62/README.md)。

## s63：第六个迪达拉原生单格（summon）

仅 `didala__summon__neutral__ground__near`：原生 4,858 事件、122 双方状态，
o/79 意图 tick 10–12 与源读取一致；收据复验、Godot required-native 单格通过。
done 后同 tick/显示帧有 4 条随机记录；保留原始尾部，校验改为最终状态后唯一 done，
尾部不得跨 tick/显示帧且全量哈希绑定。提前/重复完成、跨帧尾部及错配/缺失均拒绝。
整批因其他格缺收据 exit 1。本格其余维度后续，两标志 false。见 [s63](../evidence/sampling-upgrade/s63/README.md)。

## s64：summon 单格全局几何（援助来源缺口）

仅 `didala__summon__neutral__ground__near`：原生 5,349 事件，收据复验通过。
原始 61 对样本边界/238 条绑定框记录，tick 58–60 的 p1fz.atm1 三次报 unbound，
完整 gate exit 1；仅 tick 0–57 前缀 58 样本/228 框结构验证通过，缺样本/框拒绝。
须核我爱罗援助 atm1 的源放置、生命周期与探针 stamp，不按名称猜绑定或忽略援助框。
完整原生/Godot 几何未证明，其余维度后续，两标志 false。见 [s64](../evidence/sampling-upgrade/s64/README.md)。

## s65：summon 单格子显示列表与镜头

仅 `didala__summon__neutral__ground__near`：原生 8,283 事件、61/61 样本、
1,538 节点记录，收据/结构校验通过；缺样本/角色节点拒绝，恢复后复验。
完整显示/镜头 gate exit 1：122 条 AImain 源帧缺口和 76 条特效符号缺口保留。
动态 mask/完整镜头对照未证明；s64 援助框来源缺口不因显示采样解除。
BitmapData/DoAction 后续，两标志 false。见 [s65](../evidence/sampling-upgrade/s65/README.md)。

## s66：summon 单格 BitmapData 与严格 RGBA 比较

仅 `didala__summon__neutral__ground__near`：真实 Flash/Godot 各 61/61 图，
原生 29,376 事件，收据/图像校验通过；严格比较 0/61 精确，
17,613,026 通道、6,973,018 像素不同，最大 Δ255，gate exit 1。
缺原生帧/行、缺 Godot 图及单通道修改均拒绝，恢复后复验。
时钟/阶段与渲染差异未归因，s64/s65 缺口保留；DoAction 后续，两标志 false。
见 [s66](../evidence/sampling-upgrade/s66/README.md)。

## s67：summon 单格 DoAction 入口覆盖

仅 `didala__summon__neutral__ground__near`：原生 5,446 事件、61/61 根样本、
380 次入口/32 源块（战斗窗口 42 次/18 块），收据和入口结构校验通过。
固定 1,072 项源码义务中 475 块已插桩；443 未访问、597 未插桩仍保留，
完整 AS gate exit 1。缺入口/样本/源码义务均拒绝，恢复后复验。
函数内部、分支、clip-action 与调用所有权后续；s64/s65/s66 残留不变，
production_admitted=false、native_parity_proven=false。
见 [s67](../evidence/sampling-upgrade/s67/README.md)。

## s68：summon 单格 clip-action 处理器入口

仅 `didala__summon__neutral__ground__near`：原生 8,238 事件、61/61 根样本、
2,935 次 clip 入口/10 源处理器（战斗窗口 328 次）；另有 369 次 DoAction/32 块。
收据和入口结构校验通过；缺 clip 事件/样本/源码义务均拒绝，恢复后复验。
614 未访问（443 块 + 171 处理器）、416 未插桩保留，完整 AS gate exit 1。
处理器内部调用/分支与完整所有权后续，s64/s65/s66 残留不变；
production_admitted=false、native_parity_proven=false。
见 [s68](../evidence/sampling-upgrade/s68/README.md)。

## s69：summon 单格调用点与分支观察

仅 `didala__summon__neutral__ground__near`：原生 9,548 事件、61/61 根样本，
所选 `gameRunning()` / `doAllAction()` 处理器有 428 次完整观察（410 假/18 真）。
tick 10 另一次到达 call_before 后缺 call_after/end，原始记录保留，gate exit 1。
六类缺标记、缺事件/样本/源码义务均拒绝，原始诊断和收据复验；
614 未访问、416 未插桩保留，callee 内部与完整 AS 所有权未证明。
s64/s65/s66 残留不变；production_admitted=false、native_parity_proven=false。
见 [s69](../evidence/sampling-upgrade/s69/README.md)。

## s70：茶渡首个原生单格（attack）

仅 `chad__attack__neutral__ground__near`：原生 4,910 事件、122 双方状态，
攻击键 74 意图 tick 10–12；1,569 次源读取与意图一致。收据复验通过，
Godot required-native 单格执行 1/324、无错误；缺失/错配收据、缺原生样本拒绝。
整批因其他格缺收据 exit 1。几何、显示/镜头、BitmapData、DoAction/所有权后续，
不宣称行为或像素一致；production_admitted=false、native_parity_proven=false。
见 [s70](../evidence/sampling-upgrade/s70/README.md)。

## s71：茶渡 attack 单格全局几何

仅 `chad__attack__neutral__ground__near`：原生 5,562 事件、61/61 几何样本，
238 条受击框 + 2 条攻击框、9 个观察实例；双方每个样本均有受击候选，
援助/舞台攻击数组显式为空。收据复验及原生几何 gate 通过；缺样本/框拒绝，恢复后复验。
仅证明根观察边界的来源绑定候选；精确生命周期、帧内瞬态与 Godot 几何对照仍未证明。
DL/镜头、BitmapData、DoAction/所有权后续，两标志 false。
见 [s71](../evidence/sampling-upgrade/s71/README.md)。

## s72：茶渡 attack 单格子显示列表与镜头

仅 `chad__attack__neutral__ground__near`：原生 8,438 事件、61/61 样本、
1,532 节点记录，收据与结构检查通过；缺样本/角色节点拒绝，恢复后复验。
完整 gate exit 1：122 条 AImain 源帧缺口、45 条 xgmc0 特效符号缺口保留。
动态 mask、帧内生命周期和完整 Godot 镜头对照未证明；Chad XML 来源哈希锁定。
BitmapData/DoAction 后续，production_admitted=false、native_parity_proven=false。
见 [s72](../evidence/sampling-upgrade/s72/README.md)。

## s73：茶渡 attack 单格 BitmapData 与严格 RGBA 比较

仅 `chad__attack__neutral__ground__near`：真实 Flash/Godot 各 61/61 图，
原生 29,564 事件，收据与图像校验通过；严格比较 0/61 精确，
17,616,253 通道、6,832,516 像素不同，最大 Δ255，gate exit 1。
缺原生帧/行、缺 Godot 图及单通道修改均拒绝，恢复后复验。
时钟/观察阶段与渲染差异未归因，s72 来源/mask 缺口保留；DoAction 后续，
production_admitted=false、native_parity_proven=false。
见 [s73](../evidence/sampling-upgrade/s73/README.md)。

## s74：茶渡 attack 单格 DoAction 入口覆盖

仅 `chad__attack__neutral__ground__near`：原生 5,527 事件、61/61 根样本、
424 次入口/28 源块（战斗窗口 59 次/16 块），收据和入口结构校验通过。
固定 1,050 项源码义务中 453 块已插桩；425 未访问、597 未插桩保留，
完整 AS gate exit 1。缺入口/样本/源码义务均拒绝，恢复后复验。
函数内部、分支、clip-action 与调用所有权后续；s72/s73 残留不变，
production_admitted=false、native_parity_proven=false。
见 [s74](../evidence/sampling-upgrade/s74/README.md)。

## s75–s76：茶渡 attack 单格 clip-action 与调用/分支（同一 PR）

s75 原生 8,299 事件、61/61 根样本、2,786 次 clip 入口/13 处理器；
缺事件/样本/义务拒绝，完整 AS gate exit 1：594 未访问、415 未插桩保留。
s76 原生 9,464 事件、61/61 根样本；Chad 源 Sprite607 处理器 441 次完整
调用点观察（396 假/45 真），tick 10 另一次缺 call_after/end，gate exit 1。
六类标记删除均拒绝，原始诊断/收据复验；探针只增加精确源路径绑定，
源码变化与多处理器歧义拒绝，未改运行时。
这完成本格七维观察材料收集，不等于完整所有权或原生一致；callee 内部、
生命周期、s72 来源/mask 与 s73 像素/时钟残留仍开放，两标志 false。
见 [s75](../evidence/sampling-upgrade/s75/README.md)、[s76](../evidence/sampling-upgrade/s76/README.md)。

## s77–s83：恋次 attack 单格七维（同一角色 PR）

仅 `renji__attack__neutral__ground__near`，未执行其他角色/招式。

| 证据 | 结果 | 完整门槛 |
|---|---|---|
| s77 原生/收据 | 5,107 事件、122 状态；Godot required-native 单格通过 | 整批缺其他收据 exit 1 |
| s78 几何 | 61/61 样本，238 受击 + 2 攻击框，9 实例 | 原生 gate exit 0；未作 Godot 几何对照 |
| s79 显示/镜头 | 61/61 样本、1,527 节点 | 167 来源义务，exit 1；动态 mask 未证明 |
| s80 BitmapData | 双方各 61 图，0/61 精确；17,860,537 通道不同 | 严格 RGBA exit 1，时钟/渲染差异未归因 |
| s81 DoAction | 435 入口/29 块 | 444 未访问、594 未插桩，exit 1 |
| s82 clip-action | 2,802 入口/13 处理器 | 608 未访问、417 未插桩，exit 1 |
| s83 调用/分支 | 448 完整（405 假/43 真），另一次缺返回/结束 | tick 10 缺口保留，exit 1 |

各维缺收据/样本/框/节点/图/入口/标记负例均拒绝并恢复复验。
唯一探针扩展为 Renji Sprite717/PlaceObject2_16_29 精确源码绑定；源码改写、
多处理器歧义仍拒绝。127 项聚焦测试通过，原生入参/语义未改；
production_admitted=false、native_parity_proven=false。七维观察材料齐备不等于
完整所有权或行为/像素一致。后续应核 tick10 调用退出/接收者寿命、显示来源/mask、
时钟阶段和 RGBA 残留；不以清空清单或容差宣称通过。
见 [角色证据总览](../evidence/sampling-upgrade/s77/README.md) 与其复现说明。

## s84–s90：小李 attack 单格七维（同一角色 PR）

仅 `lee__attack__neutral__ground__near`，未执行宁次或其他角色/招式。

| 证据 | 结果 | 完整门槛 |
|---|---|---|
| s84 原生/收据 | 5,402 事件、122 状态；Godot required-native 单格通过 | 整批缺其他收据 exit 1 |
| s85 几何 | 61/61 样本，242 受击 + 2 攻击框，7 实例 | 原生 exit 0；未作 Godot 几何对照 |
| s86 显示/镜头 | 61/61 样本、1,506 节点 | 122 AImain 源帧义务，exit 1；动态 mask 未证明 |
| s87 BitmapData | 双方各 61 图，0/61 精确；17,650,119 通道不同 | 严格 RGBA exit 1，时钟/渲染差异未归因 |
| s88 DoAction | 448 入口/26 块 | 461 未访问、612 未插桩，exit 1 |
| s89 clip-action | 2,814 入口/11 处理器 | 647 未访问、415 未插桩，exit 1 |
| s90 调用/分支 | 449 完整（405 假/44 真），另一次缺返回/结束 | tick10 缺口保留，exit 1 |

各维缺收据/样本/框/节点/图/入口/标记负例均拒绝并恢复复验。
唯一探针扩展为 Lee Sprite518/PlaceObject2_18_31 精确源码绑定；源码改写与
多处理器歧义仍拒绝。128 项聚焦测试通过，未改运行时；
production_admitted=false、native_parity_proven=false。七维材料齐备不等于
完整所有权或行为/像素一致。显示来源/mask、调用退出/接收者寿命、
时钟阶段和 RGBA 残留继续开放。
见 [角色证据总览](../evidence/sampling-upgrade/s84/README.md) 与复现说明。

## s91–s97：宁次 attack 单格七维（同一角色 PR）

仅 `neji__attack__neutral__ground__near`，未执行其他角色/招式。

| 维度 | 实采结果 | 门槛 |
|---|---|---|
| s91 原生/收据 | 5735 事件、122 状态；Godot 单格通过 | 整批缺其他收据 exit 1 |
| s92 几何 | 61/61 样本、241 受击 + 2 攻击框、8 实例 | 原生 exit 0；未作 Godot 几何对照 |
| s93 显示/镜头 | 61/61 样本、1,505 节点 | 122 AImain 源帧缺口，exit 1 |
| s94 BitmapData | 双方 61 图，0/61 精确，17,099,973 通道不同 | 严格 RGBA exit 1 |
| s95 DoAction | 429 入口/26 块 | 438 未访问/611 未插桩，exit 1 |
| s96 clip-action | 3045 入口/11 处理器 | 623 未访问/415 未插桩，exit 1 |
| s97 调用/分支 | 453 完整（409 假/44 真），1 次边界缺失 | 缺口保留，exit 1 |

各维缺收据/样本/框/节点/图/入口/标记负例均拒绝并恢复复验。
唯一探针扩展为 Neji Sprite535/PlaceObject2_20_31 精确源码绑定；源码改写与
多处理器歧义仍拒绝。129 项聚焦测试通过，未改运行时；
production_admitted=false、native_parity_proven=false。材料齐备不等于完整所有权
或行为/像素一致。动态 mask、来源帧、调用退出/接收者寿命及像素/时钟差异仍开放。
见 [角色总览](../evidence/sampling-upgrade/s91/README.md) 与复现说明。

## s98–s104：小樱 attack 单格七维（同一角色 PR）

仅 `sakura__attack__neutral__ground__near`；原版角色名“樱”，源 `Sakura.swf`。

- **s98 Native receipt:** 5275 native events; receipt revalidation and Godot required-native selected execution pass (1/324). Full campaign rejects other missing receipts.
- **s99 Global geometry:** 61/61 samples; {'hurt': 238, 'attack': 2} box records; 9 sampled instances. Native gate passes; Godot geometry comparison remains open.
- **s100 Child display list and camera:** 61/61 samples; 1483 nodes; full gate exits 1 with 167 source obligations: 122 missing source frames, 45 unresolved runtime symbols. Dynamic masks/full camera remain unproven.
- **s101 BitmapData and RGBA:** 61 native and 61 actual Godot images, 600x400 opaque RGBA. Strict gate exits 1: 0/61 exact; 17422535 differing channels, 6771071 differing pixels; max channel delta 255. No alignment, cropping, reference rewriting or tolerance.
- **s102 DoAction entry coverage:** 61/61 samples; 440 entries / 30 blocks. Full gate exits 1: 441 unvisited, 606 uninstrumented.
- **s103 Clip-action handler coverage:** 61/61 samples; 2803 clip entries / 13 handlers. Full gate exits 1: 619 unvisited, 415 uninstrumented.
- **s104 Call-site and branch observations:** 61/61 samples; 454 complete invocations (410 false / 44 true); 1 incomplete. Full ownership gate exits 1; callee bodies, other branches and Godot ownership remain unproven. Exact incomplete boundaries retained in callsite-summary.json.

各维缺失负例拒绝且恢复复验。130 项聚焦测试通过；无游戏运行时改动。
production_admitted=false、native_parity_proven=false。完整原生一致性、源绑定、
动态 mask、Godot 几何、像素/时钟差异和完整 AS 所有权仍为后续工作。
[角色总览与复现](../evidence/sampling-upgrade/s98/README.md)。

## s105–s111：银 attack 单格七维（同一角色 PR）

仅 `yin__attack__neutral__ground__near`；原版角色名“银”，源 `yin.swf`。

- **s105 Native receipt:** 5433 native events; receipt revalidation and Godot required-native selected execution pass (1/324). Full campaign rejects other missing receipts.
- **s106 Global geometry:** 61/61 samples; {'hurt': 238, 'attack': 2} box records; 9 sampled instances. Native gate passes; Godot geometry comparison remains open.
- **s107 Child display list and camera:** 61/61 samples; 1523 nodes; full gate exits 1 with 169 source obligations: see source-gap-summary.json for exact reasons and paths. Dynamic masks/full camera remain unproven.
- **s108 BitmapData and RGBA:** 61 native and 61 actual Godot images, 600x400 opaque RGBA. Strict gate exits 1: 0/61 exact; 18273627 differing channels, 7057400 differing pixels; max channel delta 255. No alignment, cropping, reference rewriting or tolerance.
- **s109 DoAction entry coverage:** 61/61 samples; 450 entries / 30 blocks. Full gate exits 1: 430 unvisited, 599 uninstrumented.
- **s110 Clip-action handler coverage:** 61/61 samples; 2759 clip entries / 13 handlers. Full gate exits 1: 601 unvisited, 415 uninstrumented.
- **s111 Call-site and branch observations:** 61/61 samples; 457 complete invocations (418 false / 39 true); 1 incomplete. Full ownership gate exits 1; callee bodies, other branches and Godot ownership remain unproven. Exact incomplete boundaries retained in callsite-summary.json.

各维缺失负例拒绝且恢复复验。131 项聚焦测试通过；无游戏运行时改动。
production_admitted=false、native_parity_proven=false。完整原生一致性、源绑定、
动态 mask、Godot 几何、像素/时钟差异和完整 AS 所有权仍为后续工作。
[角色总览与复现](../evidence/sampling-upgrade/s105/README.md)。

## s112–s118：剑八 attack 单格七维（同一角色 PR）

仅 `jianba__attack__neutral__ground__near`；原版角色名“剑八”，源 `jianba.swf`。

- **s112 Native receipt:** 5098 native events; receipt revalidation and Godot required-native selected execution pass (1/324). Full campaign rejects other missing receipts.
- **s113 Global geometry:** 61/61 samples; {'hurt': 238, 'attack': 2} box records; 9 sampled instances. Native gate passes; Godot geometry comparison remains open.
- **s114 Child display list and camera:** 61/61 samples; 1543 nodes; full gate exits 1 with 170 source obligations: see source-gap-summary.json for exact reasons and paths. Dynamic masks/full camera remain unproven.
- **s115 BitmapData and RGBA:** 61 native and 61 actual Godot images, 600x400 opaque RGBA. Strict gate exits 1: 0/61 exact; 17963256 differing channels, 6939053 differing pixels; max channel delta 255. No alignment, cropping, reference rewriting or tolerance.
- **s116 DoAction entry coverage:** 61/61 samples; 435 entries / 30 blocks. Full gate exits 1: 445 unvisited, 610 uninstrumented.
- **s117 Clip-action handler coverage:** 61/61 samples; 2938 clip entries / 13 handlers. Full gate exits 1: 627 unvisited, 415 uninstrumented.
- **s118 Call-site and branch observations:** 61/61 samples; 436 complete invocations (390 false / 46 true); 1 incomplete. Full ownership gate exits 1; callee bodies, other branches and Godot ownership remain unproven. Exact incomplete boundaries retained in callsite-summary.json.

各维缺失负例拒绝且恢复复验。132 项聚焦测试通过；无游戏运行时改动。
production_admitted=false、native_parity_proven=false。完整原生一致性、源绑定、
动态 mask、Godot 几何、像素/时钟差异和完整 AS 所有权仍为后续工作。
[角色总览与复现](../evidence/sampling-upgrade/s112/README.md)。

## s119–s125：重吾 attack 单格七维（同一角色 PR）

仅 `juggo__attack__neutral__ground__near`；原版角色名“重吾”，源 `juggo.swf`。

- **s119 Native receipt:** 5358 native events; receipt revalidation and Godot required-native selected execution pass (1/324). Full campaign rejects other missing receipts.
- **s120 Global geometry:** 61/61 samples; {'hurt': 238, 'attack': 2} box records; 9 sampled instances. Native gate passes; Godot geometry comparison remains open.
- **s121 Child display list and camera:** 61/61 samples; 1535 nodes; full gate exits 1 with 170 source obligations: see source-gap-summary.json for exact reasons and paths. Dynamic masks/full camera remain unproven.
- **s122 BitmapData and RGBA:** 61 native and 61 actual Godot images, 600x400 opaque RGBA. Strict gate exits 1: 0/61 exact; 16990923 differing channels, 6614373 differing pixels; max channel delta 255. No alignment, cropping, reference rewriting or tolerance.
- **s123 DoAction entry coverage:** 61/61 samples; 387 entries / 29 blocks. Full gate exits 1: 483 unvisited, 619 uninstrumented.
- **s124 Clip-action handler coverage:** 61/61 samples; 2882 clip entries / 13 handlers. Full gate exits 1: 673 unvisited, 416 uninstrumented.
- **s125 Call-site and branch observations:** 61/61 samples; 443 complete invocations (398 false / 45 true); 1 incomplete. Full ownership gate exits 1; callee bodies, other branches and Godot ownership remain unproven. Exact incomplete boundaries retained in callsite-summary.json.

各维缺失负例拒绝且恢复复验。133 项聚焦测试通过；无游戏运行时改动。
production_admitted=false、native_parity_proven=false。完整原生一致性、源绑定、
动态 mask、Godot 几何、像素/时钟差异和完整 AS 所有权仍为后续工作。
[角色总览与复现](../evidence/sampling-upgrade/s119/README.md)。

## s126–s132：小南 attack 单格七维（同一角色 PR）

仅 `konan__attack__neutral__ground__near`；原版角色名“小南”，源 `konan.swf`。

- **s126 Native receipt:** 5120 native events; receipt revalidation and Godot required-native selected execution pass (1/324). Full campaign rejects other missing receipts.
- **s127 Global geometry:** 61/61 samples; {'hurt': 238, 'attack': 3} box records; 9 sampled instances. Native gate passes; Godot geometry comparison remains open.
- **s128 Child display list and camera:** 61/61 samples; 1528 nodes; full gate exits 1 with 169 source obligations: see source-gap-summary.json for exact reasons and paths. Dynamic masks/full camera remain unproven.
- **s129 BitmapData and RGBA:** 61 native and 61 actual Godot images, 600x400 opaque RGBA. Strict gate exits 1: 0/61 exact; 18441332 differing channels, 7122911 differing pixels; max channel delta 255. No alignment, cropping, reference rewriting or tolerance.
- **s130 DoAction entry coverage:** 61/61 samples; 381 entries / 30 blocks. Full gate exits 1: 441 unvisited, 596 uninstrumented.
- **s131 Clip-action handler coverage:** 61/61 samples; 2753 clip entries / 12 handlers. Full gate exits 1: 610 unvisited, 415 uninstrumented.
- **s132 Call-site and branch observations:** 61/61 samples; 449 complete invocations (407 false / 42 true); 1 incomplete. Full ownership gate exits 1; callee bodies, other branches and Godot ownership remain unproven. Exact incomplete boundaries retained in callsite-summary.json.

各维缺失负例拒绝且恢复复验。134 项聚焦测试通过；无游戏运行时改动。
production_admitted=false、native_parity_proven=false。完整原生一致性、源绑定、
动态 mask、Godot 几何、像素/时钟差异和完整 AS 所有权仍为后续工作。
[角色总览与复现](../evidence/sampling-upgrade/s126/README.md)。

## s133–s139：白哉 attack 单格七维（同一角色 PR）

仅 `byakuya__attack__neutral__ground__near`；原版角色名“白哉”，源 `Byakuya.swf`。

- **s133 Native receipt:** 5200 native events; receipt revalidation and Godot required-native selected execution pass (1/324). Full campaign rejects other missing receipts.
- **s134 Global geometry:** 61/61 samples; {'hurt': 238, 'attack': 2} box records; 9 sampled instances. Native gate passes; Godot geometry comparison remains open.
- **s135 Child display list and camera:** 61/61 samples; 1539 nodes; full gate exits 1 with 167 source obligations: see source-gap-summary.json for exact reasons and paths. Dynamic masks/full camera remain unproven.
- **s136 BitmapData and RGBA:** 61 native and 61 actual Godot images, 600x400 opaque RGBA. Strict gate exits 1: 0/61 exact; 17098339 differing channels, 6661071 differing pixels; max channel delta 255. No alignment, cropping, reference rewriting or tolerance.
- **s137 DoAction entry coverage:** 61/61 samples; 445 entries / 31 blocks. Full gate exits 1: 553 unvisited, 643 uninstrumented.
- **s138 Clip-action handler coverage:** 61/61 samples; 2780 clip entries / 13 handlers. Full gate exits 1: 767 unvisited, 416 uninstrumented.
- **s139 Call-site and branch observations:** 61/61 samples; 441 complete invocations (396 false / 45 true); 1 incomplete. Full ownership gate exits 1; callee bodies, other branches and Godot ownership remain unproven. Exact incomplete boundaries retained in callsite-summary.json.

各维缺失负例拒绝且恢复复验。135 项聚焦测试通过；无游戏运行时改动。
production_admitted=false、native_parity_proven=false。完整原生一致性、源绑定、
动态 mask、Godot 几何、像素/时钟差异和完整 AS 所有权仍为后续工作。
[角色总览与复现](../evidence/sampling-upgrade/s133/README.md)。

## s140–s146：带土 attack 单格七维（同一角色 PR）

仅 `daitu__attack__neutral__ground__near`；原版角色名“带土”，源 `daitu.swf`。

- **s140 Native receipt:** 5188 native events; receipt revalidation and Godot required-native selected execution pass (1/324). Full campaign rejects other missing receipts.
- **s141 Global geometry:** 61/61 samples; {'hurt': 238, 'attack': 2} box records; 9 sampled instances. Native gate passes; Godot geometry comparison remains open.
- **s142 Child display list and camera:** 61/61 samples; 1535 nodes; full gate exits 1 with 170 source obligations: see source-gap-summary.json for exact reasons and paths. Dynamic masks/full camera remain unproven.
- **s143 BitmapData and RGBA:** 61 native and 61 actual Godot images, 600x400 opaque RGBA. Strict gate exits 1: 0/61 exact; 16686821 differing channels, 6507282 differing pixels; max channel delta 255. No alignment, cropping, reference rewriting or tolerance.
- **s144 DoAction entry coverage:** 61/61 samples; 418 entries / 31 blocks. Full gate exits 1: 552 unvisited, 665 uninstrumented.
- **s145 Clip-action handler coverage:** 61/61 samples; 2952 clip entries / 13 handlers. Full gate exits 1: 789 unvisited, 415 uninstrumented.
- **s146 Call-site and branch observations:** 61/61 samples; 447 complete invocations (402 false / 45 true); 1 incomplete. Full ownership gate exits 1; callee bodies, other branches and Godot ownership remain unproven. Exact incomplete boundaries retained in callsite-summary.json.

各维缺失负例拒绝且恢复复验。136 项聚焦测试通过；无游戏运行时改动。
production_admitted=false、native_parity_proven=false。完整原生一致性、源绑定、
动态 mask、Godot 几何、像素/时钟差异和完整 AS 所有权仍为后续工作。
[角色总览与复现](../evidence/sampling-upgrade/s140/README.md)。

## s147–s153：我爱罗 attack 单格七维（同一角色 PR）

仅 `gaara__attack__neutral__ground__near`；原版角色名“我爱罗”，源 `gaara.swf`。

- **s147 Native receipt:** 5615 native events; receipt revalidation and Godot required-native selected execution pass (1/324). Full campaign rejects other missing receipts.
- **s148 Global geometry:** 61/61 samples; {'hurt': 238, 'attack': 2} box records; 9 sampled instances. Native gate passes; Godot geometry comparison remains open.
- **s149 Child display list and camera:** 61/61 samples; 1544 nodes; full gate exits 1 with 169 source obligations: see source-gap-summary.json for exact reasons and paths. Dynamic masks/full camera remain unproven.
- **s150 BitmapData and RGBA:** 61 native and 61 actual Godot images, 600x400 opaque RGBA. Strict gate exits 1: 0/61 exact; 17998331 differing channels, 7015427 differing pixels; max channel delta 255. No alignment, cropping, reference rewriting or tolerance.
- **s151 DoAction entry coverage:** 61/61 samples; 432 entries / 29 blocks. Full gate exits 1: 446 unvisited, 590 uninstrumented.
- **s152 Clip-action handler coverage:** 61/61 samples; 3029 clip entries / 12 handlers. Full gate exits 1: 608 unvisited, 416 uninstrumented.
- **s153 Call-site and branch observations:** 61/61 samples; 435 complete invocations (391 false / 44 true); 1 incomplete. Full ownership gate exits 1; callee bodies, other branches and Godot ownership remain unproven. Exact incomplete boundaries retained in callsite-summary.json.

各维缺失负例拒绝且恢复复验。137 项聚焦测试通过；无游戏运行时改动。
production_admitted=false、native_parity_proven=false。完整原生一致性、源绑定、
动态 mask、Godot 几何、像素/时钟差异和完整 AS 所有权仍为后续工作。
[角色总览与复现](../evidence/sampling-upgrade/s147/README.md)。

## s154–s160：鼬 attack 单格七维（同一角色 PR）

仅 `itachi__attack__neutral__ground__near`；原版角色名“鼬”，源 `itachi.swf`。

- **s154 Native receipt:** 5179 native events; receipt revalidation and Godot required-native selected execution pass (1/324). Full campaign rejects other missing receipts.
- **s155 Global geometry:** 61/61 samples; {'hurt': 238, 'attack': 4} box records; 10 sampled instances. Native gate passes; Godot geometry comparison remains open.
- **s156 Child display list and camera:** 61/61 samples; 1525 nodes; full gate exits 1 with 164 source obligations: see source-gap-summary.json for exact reasons and paths. Dynamic masks/full camera remain unproven.
- **s157 BitmapData and RGBA:** 61 native and 61 actual Godot images, 600x400 opaque RGBA. Strict gate exits 1: 0/61 exact; 17713306 differing channels, 6882344 differing pixels; max channel delta 255. No alignment, cropping, reference rewriting or tolerance.
- **s158 DoAction entry coverage:** 61/61 samples; 372 entries / 30 blocks. Full gate exits 1: 443 unvisited, 600 uninstrumented.
- **s159 Clip-action handler coverage:** 61/61 samples; 2819 clip entries / 13 handlers. Full gate exits 1: 615 unvisited, 415 uninstrumented.
- **s160 Call-site and branch observations:** 61/61 samples; 429 complete invocations (389 false / 40 true); 1 incomplete. Full ownership gate exits 1; callee bodies, other branches and Godot ownership remain unproven. Exact incomplete boundaries retained in callsite-summary.json.

各维缺失负例拒绝且恢复复验。138 项聚焦测试通过；无游戏运行时改动。
production_admitted=false、native_parity_proven=false。完整原生一致性、源绑定、
动态 mask、Godot 几何、像素/时钟差异和完整 AS 所有权仍为后续工作。
[角色总览与复现](../evidence/sampling-upgrade/s154/README.md)。

## s161–s167：自来也 attack 单格七维（同一角色 PR）

仅 `jiraiya__attack__neutral__ground__near`；原版角色名“自来也”，源 `jiraiya.swf`。

- **s161 Native receipt:** 5481 native events; receipt revalidation and Godot required-native selected execution pass (1/324). Full campaign rejects other missing receipts.
- **s162 Global geometry:** 61/61 samples; {'hurt': 238, 'attack': 2} box records; 9 sampled instances. Native gate passes; Godot geometry comparison remains open.
- **s163 Child display list and camera:** 61/61 samples; 1535 nodes; full gate exits 1 with 170 source obligations: see source-gap-summary.json for exact reasons and paths. Dynamic masks/full camera remain unproven.
- **s164 BitmapData and RGBA:** 61 native and 61 actual Godot images, 600x400 opaque RGBA. Strict gate exits 1: 0/61 exact; 18612303 differing channels, 7163226 differing pixels; max channel delta 255. No alignment, cropping, reference rewriting or tolerance.
- **s165 DoAction entry coverage:** 61/61 samples; 437 entries / 29 blocks. Full gate exits 1: 440 unvisited, 607 uninstrumented.
- **s166 Clip-action handler coverage:** 61/61 samples; 2948 clip entries / 13 handlers. Full gate exits 1: 619 unvisited, 415 uninstrumented.
- **s167 Call-site and branch observations:** 61/61 samples; 461 complete invocations (416 false / 45 true); 1 incomplete. Full ownership gate exits 1; callee bodies, other branches and Godot ownership remain unproven. Exact incomplete boundaries retained in callsite-summary.json.

各维缺失负例拒绝且恢复复验。138 项聚焦测试通过；无游戏运行时改动。
production_admitted=false、native_parity_proven=false。完整原生一致性、源绑定、
动态 mask、Godot 几何、像素/时钟差异和完整 AS 所有权仍为后续工作。
[角色总览与复现](../evidence/sampling-upgrade/s161/README.md)。

## s168–s174：卡卡西 attack 单格七维（同一角色 PR）

仅 `kakashi__attack__neutral__ground__near`；原版角色名“卡卡西”，源 `Kakashi.swf`。

- **s168 Native receipt:** 5121 native events; receipt revalidation and Godot required-native selected execution pass (1/324). Full campaign rejects other missing receipts.
- **s169 Global geometry:** 61/61 samples; {'hurt': 237, 'attack': 2} box records; 9 sampled instances. Native gate passes; Godot geometry comparison remains open.
- **s170 Child display list and camera:** 61/61 samples; 1481 nodes; full gate exits 1 with 167 source obligations: see source-gap-summary.json for exact reasons and paths. Dynamic masks/full camera remain unproven.
- **s171 BitmapData and RGBA:** 61 native and 61 actual Godot images, 600x400 opaque RGBA. Strict gate exits 1: 0/61 exact; 17199106 differing channels, 6692930 differing pixels; max channel delta 255. No alignment, cropping, reference rewriting or tolerance.
- **s172 DoAction entry coverage:** 61/61 samples; 383 entries / 30 blocks. Full gate exits 1: 453 unvisited, 609 uninstrumented.
- **s173 Clip-action handler coverage:** 61/61 samples; 2816 clip entries / 13 handlers. Full gate exits 1: 634 unvisited, 415 uninstrumented.
- **s174 Call-site and branch observations:** 61/61 samples; 434 complete invocations (392 false / 42 true); 1 incomplete. Full ownership gate exits 1; callee bodies, other branches and Godot ownership remain unproven. Exact incomplete boundaries retained in callsite-summary.json.

各维缺失负例拒绝且恢复复验。138 项聚焦测试通过；无游戏运行时改动。
production_admitted=false、native_parity_proven=false。完整原生一致性、源绑定、
动态 mask、Godot 几何、像素/时钟差异和完整 AS 所有权仍为后续工作。
[角色总览与复现](../evidence/sampling-upgrade/s168/README.md)。

## s175–s181：蓝染 attack 单格七维（同一角色 PR）

仅 `lanran__attack__neutral__ground__near`；原版角色名“蓝染”，源 `lanran.swf`。

- **s175 Native receipt:** 5570 native events; receipt revalidation and Godot required-native selected execution pass (1/324). Full campaign rejects other missing receipts.
- **s176 Global geometry:** 61/61 samples; {'hurt': 237, 'attack': 2} box records; 9 sampled instances. Native gate passes; Godot geometry comparison remains open.
- **s177 Child display list and camera:** 61/61 samples; 1531 nodes; full gate exits 1 with 167 source obligations: see source-gap-summary.json for exact reasons and paths. Dynamic masks/full camera remain unproven.
- **s178 BitmapData and RGBA:** 61 native and 61 actual Godot images, 600x400 opaque RGBA. Strict gate exits 1: 0/61 exact; 17599336 differing channels, 6833010 differing pixels; max channel delta 255. No alignment, cropping, reference rewriting or tolerance.
- **s179 DoAction entry coverage:** 61/61 samples; 431 entries / 30 blocks. Full gate exits 1: 491 unvisited, 625 uninstrumented.
- **s180 Clip-action handler coverage:** 61/61 samples; 2809 clip entries / 13 handlers. Full gate exits 1: 684 unvisited, 419 uninstrumented.
- **s181 Call-site and branch observations:** 61/61 samples; 435 complete invocations (395 false / 40 true); 1 incomplete. Full ownership gate exits 1; callee bodies, other branches and Godot ownership remain unproven. Exact incomplete boundaries retained in callsite-summary.json.

各维缺失负例拒绝且恢复复验。138 项聚焦测试通过；无游戏运行时改动。
production_admitted=false、native_parity_proven=false。完整原生一致性、源绑定、
动态 mask、Godot 几何、像素/时钟差异和完整 AS 所有权仍为后续工作。
[角色总览与复现](../evidence/sampling-upgrade/s175/README.md)。

## s182–s188：鸣人 attack 单格七维（同一角色 PR）

仅 `minren__attack__neutral__ground__near`；原版角色名“鸣人”，源 `minren.swf`。

- **s182 Native receipt:** 5383 native events; receipt revalidation and Godot required-native selected execution pass (1/324). Full campaign rejects other missing receipts.
- **s183 Global geometry:** 61/61 samples; {'hurt': 238, 'attack': 3} box records; 9 sampled instances. Native gate passes; Godot geometry comparison remains open.
- **s184 Child display list and camera:** 61/61 samples; 1539 nodes; full gate exits 1 with 167 source obligations: see source-gap-summary.json for exact reasons and paths. Dynamic masks/full camera remain unproven.
- **s185 BitmapData and RGBA:** 61 native and 61 actual Godot images, 600x400 opaque RGBA. Strict gate exits 1: 0/61 exact; 17610428 differing channels, 6839703 differing pixels; max channel delta 255. No alignment, cropping, reference rewriting or tolerance.
- **s186 DoAction entry coverage:** 61/61 samples; 422 entries / 28 blocks. Full gate exits 1: 683 unvisited, 717 uninstrumented.
- **s187 Clip-action handler coverage:** 61/61 samples; 2992 clip entries / 13 handlers. Full gate exits 1: 965 unvisited, 422 uninstrumented.
- **s188 Call-site and branch observations:** 61/61 samples; 453 complete invocations (406 false / 47 true); 1 incomplete. Full ownership gate exits 1; callee bodies, other branches and Godot ownership remain unproven. Exact incomplete boundaries retained in callsite-summary.json.

各维缺失负例拒绝且恢复复验。142 项聚焦测试通过；无游戏运行时改动。
production_admitted=false、native_parity_proven=false。完整原生一致性、源绑定、
动态 mask、Godot 几何、像素/时钟差异和完整 AS 所有权仍为后续工作。
[角色总览与复现](../evidence/sampling-upgrade/s182/README.md)。

## s189–s195：大蛇丸 attack 单格七维（同一角色 PR）

仅 `orochimaru__attack__neutral__ground__near`；原版角色名“大蛇丸”，源 `orochimaru.swf`。

- **s189 Native receipt:** 5543 native events; receipt revalidation and Godot required-native selected execution pass (1/324). Full campaign rejects other missing receipts.
- **s190 Global geometry:** 61/61 samples; {'hurt': 238, 'attack': 2} box records; 9 sampled instances. Native gate passes; Godot geometry comparison remains open.
- **s191 Child display list and camera:** 61/61 samples; 1533 nodes; full gate exits 1 with 169 source obligations: see source-gap-summary.json for exact reasons and paths. Dynamic masks/full camera remain unproven.
- **s192 BitmapData and RGBA:** 61 native and 61 actual Godot images, 600x400 opaque RGBA. Strict gate exits 1: 0/61 exact; 17299599 differing channels, 6762877 differing pixels; max channel delta 255. No alignment, cropping, reference rewriting or tolerance.
- **s193 DoAction entry coverage:** 61/61 samples; 459 entries / 29 blocks. Full gate exits 1: 438 unvisited, 598 uninstrumented.
- **s194 Clip-action handler coverage:** 61/61 samples; 3038 clip entries / 13 handlers. Full gate exits 1: 608 unvisited, 415 uninstrumented.
- **s195 Call-site and branch observations:** 61/61 samples; 432 complete invocations (388 false / 44 true); 1 incomplete. Full ownership gate exits 1; callee bodies, other branches and Godot ownership remain unproven. Exact incomplete boundaries retained in callsite-summary.json.

各维缺失负例拒绝且恢复复验。142 项聚焦测试通过；无游戏运行时改动。
production_admitted=false、native_parity_proven=false。完整原生一致性、源绑定、
动态 mask、Godot 几何、像素/时钟差异和完整 AS 所有权仍为后续工作。
[角色总览与复现](../evidence/sampling-upgrade/s189/README.md)。

## s196–s202：佩恩 attack 单格七维（同一角色 PR）

仅 `pain__attack__neutral__ground__near`；原版角色名“佩恩”，源 `pain.swf`。

- **s196 Native receipt:** 5524 native events; receipt revalidation and Godot required-native selected execution pass (1/324). Full campaign rejects other missing receipts.
- **s197 Global geometry:** 61/61 samples; {'hurt': 238, 'attack': 3} box records; 9 sampled instances. Native gate passes; Godot geometry comparison remains open.
- **s198 Child display list and camera:** 61/61 samples; 1535 nodes; full gate exits 1 with 167 source obligations: see source-gap-summary.json for exact reasons and paths. Dynamic masks/full camera remain unproven.
- **s199 BitmapData and RGBA:** 61 native and 61 actual Godot images, 600x400 opaque RGBA. Strict gate exits 1: 0/61 exact; 17726881 differing channels, 6871237 differing pixels; max channel delta 255. No alignment, cropping, reference rewriting or tolerance.
- **s200 DoAction entry coverage:** 61/61 samples; 427 entries / 30 blocks. Full gate exits 1: 447 unvisited, 598 uninstrumented.
- **s201 Clip-action handler coverage:** 61/61 samples; 2833 clip entries / 13 handlers. Full gate exits 1: 617 unvisited, 415 uninstrumented.
- **s202 Call-site and branch observations:** 61/61 samples; 449 complete invocations (405 false / 44 true); 1 incomplete. Full ownership gate exits 1; callee bodies, other branches and Godot ownership remain unproven. Exact incomplete boundaries retained in callsite-summary.json.

各维缺失负例拒绝且恢复复验。144 项聚焦测试通过；无游戏运行时改动。
production_admitted=false、native_parity_proven=false。完整原生一致性、源绑定、
动态 mask、Godot 几何、像素/时钟差异和完整 AS 所有权仍为后续工作。
[角色总览与复现](../evidence/sampling-upgrade/s196/README.md)。

## s203–s209：日番谷 attack 单格七维（同一角色 PR）

仅 `rifagu__attack__neutral__ground__near`；原版角色名“日番谷”，源 `rifagu.swf`。

- **s203 Native receipt:** 5274 native events; receipt revalidation and Godot required-native selected execution pass (1/324). Full campaign rejects other missing receipts.
- **s204 Global geometry:** 61/61 samples; {'hurt': 237, 'attack': 3} box records; 9 sampled instances. Native gate passes; Godot geometry comparison remains open.
- **s205 Child display list and camera:** 61/61 samples; 1529 nodes; full gate exits 1 with 167 source obligations: see source-gap-summary.json for exact reasons and paths. Dynamic masks/full camera remain unproven.
- **s206 BitmapData and RGBA:** 61 native and 61 actual Godot images, 600x400 opaque RGBA. Strict gate exits 1: 0/61 exact; 17337041 differing channels, 6746417 differing pixels; max channel delta 255. No alignment, cropping, reference rewriting or tolerance.
- **s207 DoAction entry coverage:** 61/61 samples; 421 entries / 29 blocks. Full gate exits 1: 560 unvisited, 653 uninstrumented.
- **s208 Clip-action handler coverage:** 61/61 samples; 2891 clip entries / 13 handlers. Full gate exits 1: 781 unvisited, 419 uninstrumented.
- **s209 Call-site and branch observations:** 61/61 samples; 444 complete invocations (402 false / 42 true); 1 incomplete. Full ownership gate exits 1; callee bodies, other branches and Godot ownership remain unproven. Exact incomplete boundaries retained in callsite-summary.json.

各维缺失负例拒绝且恢复复验。144 项聚焦测试通过；无游戏运行时改动。
production_admitted=false、native_parity_proven=false。完整原生一致性、源绑定、
动态 mask、Godot 几何、像素/时钟差异和完整 AS 所有权仍为后续工作。
[角色总览与复现](../evidence/sampling-upgrade/s203/README.md)。

## s217–s223：佐助 attack 单格七维（同一角色 PR）

仅 `sasuke__attack__neutral__ground__near`；原版角色名“佐助”，锁定源 `Sasuke.swf` / `Sasuke.json`，基础形态 Sprite 603。

- **s217 Native receipt:** PASS (exit 0): 5404 native events, 122 actor observations; required-native selected Godot execution passes (1/324). Full campaign rejects missing receipts. This is not a parity result.
- **s218 Global geometry:** FAIL (exit 1): all four captures rejected events beyond the completion boundary. No receipt issued; zero admitted geometry samples. Final full trace contains 63 geometry_begin and 249 geometry_box events, including the rejected suffix. No Godot geometry comparison claimed.
- **s219 Child display list and camera:** FAIL (exit 1): all three captures rejected events beyond the completion boundary. No receipt issued; source joins not evaluated. Final full trace contains 62 display_begin/camera and 1,553 node events, including the rejected suffix. Source XML and hashes retained; no camera/mask completeness claimed.
- **s220 BitmapData and RGBA:** FAIL (exit 1): 61 native and 61 actual Godot images, 600x400 opaque RGBA; 0/61 exact, 17732741 differing channels, 6864492 differing pixels, max channel delta 255. No alignment, cropping or tolerance.
- **s221 DoAction entry coverage:** FAIL (exit 1): receipt and 61 samples pass; 428 entries / 30 visited blocks. Full coverage retains 596 unvisited and 662 uninstrumented source items.
- **s222 Clip-action handler coverage:** FAIL (exit 1): receipt and 61 samples pass; 2849 clip entries / 13 handlers. Full coverage retains 825 unvisited and 420 uninstrumented source items.
- **s223 Call-site and branch observations:** FAIL (exit 1): both captures rejected events beyond the completion boundary. No receipt issued. Unadmitted full-stream diagnostic retains 444 complete invocations (43 true / 401 false) and one incomplete invocation. This diagnostic does not establish valid sample boundaries, callee bodies or Godot ownership.

144 项测试通过。几何、显示、调用维度共 9 次捕获被完成边界校验拒绝，保留完整轨迹，不裁剪、不补造收据。
这三个维度的采样准入仍未完成；Godot 几何、显示源绑定、动态 mask、像素差异与完整 AS 所有权仍待解决。
production_admitted=false、native_parity_proven=false；无游戏运行时改动。
[角色总览与复现](../evidence/sampling-upgrade/s217/README.md)。

## s210–s216：露琪亚 attack 单格七维（同一角色 PR）

仅 `rukia__attack__neutral__ground__near`；原版角色名“露琪亚”，源 `rukia.swf`。

- **s210 Native receipt:** 5074 native events; receipt revalidation and Godot required-native selected execution pass (1/324). Full campaign rejects other missing receipts.
- **s211 Global geometry:** 61/61 samples; {'hurt': 238, 'attack': 3} box records; 9 sampled instances. Native gate passes; Godot geometry comparison remains open.
- **s212 Child display list and camera:** 61/61 samples; 1525 nodes; full gate exits 1 with 167 source obligations: see source-gap-summary.json for exact reasons and paths. Dynamic masks/full camera remain unproven.
- **s213 BitmapData and RGBA:** 61 native and 61 actual Godot images, 600x400 opaque RGBA. Strict gate exits 1: 0/61 exact; 17278469 differing channels, 6718476 differing pixels; max channel delta 255. No alignment, cropping, reference rewriting or tolerance.
- **s214 DoAction entry coverage:** 61/61 samples; 419 entries / 30 blocks. Full gate exits 1: 533 unvisited, 644 uninstrumented.
- **s215 Clip-action handler coverage:** 61/61 samples; 2902 clip entries / 13 handlers. Full gate exits 1: 749 unvisited, 415 uninstrumented.
- **s216 Call-site and branch observations:** 61/61 samples; 430 complete invocations (391 false / 39 true); 1 incomplete. Full ownership gate exits 1; callee bodies, other branches and Godot ownership remain unproven. Exact incomplete boundaries retained in callsite-summary.json.

各维缺失负例拒绝且恢复复验。144 项聚焦测试通过；无游戏运行时改动。
production_admitted=false、native_parity_proven=false。完整原生一致性、源绑定、
动态 mask、Godot 几何、像素/时钟差异和完整 AS 所有权仍为后续工作。
[角色总览与复现](../evidence/sampling-upgrade/s210/README.md)。


## s224–s230：ichigo 零段 attack 单格七维

指定源 `ichigo.swf` / `ichigo.json` 对应原版「一护2／零段」Sprite 274；普通「一护」是另一资产 yihu。当前 Godot 目录没有 ichigo，campaign 按原门槛拒绝；本次仅用既有 fixture 函数生成原生单格输入，没有新增角色实现或替换为 yihu。

- **s224 Native receipt:** PASS (exit 0); 5031 native events, 122 actor observations. Campaign exit 1; Godot execution unavailable.
- **s225 Global geometry:** PASS (exit 0); 61 samples, {'hurt': 238, 'attack': 2}, 9 observed lifetimes. Godot geometry parity untested.
- **s226 Display list / camera:** INCOMPLETE (exit 1); receipt rejected: native evidence: events beyond completion boundary
- **s227 BitmapData / RGBA:** INCOMPLETE (exit 1); 61 native images, 0 Godot images. Pixel comparison not evaluated (missing ichigo implementation).
- **s228 DoAction:** INCOMPLETE (exit 1); receipt rejected: native evidence: events beyond completion boundary
- **s229 Clip-action:** INCOMPLETE (exit 1); 61 samples, 3333 entries, 42 visited / 772 unvisited / 417 uninstrumented items. Entry kinds: {'doaction_entry': 438, 'clipaction_entry': 2895}.
- **s230 Call / branch:** INCOMPLETE (exit 1); 61 samples, 3264 entries, 42 visited / 772 unvisited / 417 uninstrumented items. 453 complete invocations (47 true / 406 false), 1 incomplete.

148 项工具与探针测试通过。完整原生一致性、Godot 对照、动态 mask、源绑定和完整 AS 所有权仍未验收。两标志 false，无游戏运行时改动。[总览与复现](../evidence/sampling-upgrade/s224/README.md)。


## s231–s237：一角 attack 单格七维（同一角色 PR）

仅 `yijiao__attack__neutral__ground__near`；锁定小写源路径 `scripts/fighter/yijiao.json` 与 `game/fighter/yijiao.swf`。

- **s231 Native receipt:** FAIL (exit 1): native evidence: events beyond completion boundary. No receipt issued; zero admitted samples. Full raw trace and build retained.
- **s232 Global geometry:** FAIL (exit 1): native evidence: events beyond completion boundary. No receipt issued; zero admitted samples. Full raw trace and build retained.
- **s233 Child display list and camera:** FAIL (exit 1): native evidence: events beyond completion boundary. No receipt issued; zero admitted samples. Full raw trace and build retained.
- **s234 BitmapData and RGBA:** FAIL (exit 1): 61 native and 61 actual Godot viewport frames; 0/61 exact, 17818352 differing channels and 6910686 differing pixels. Maximum channel delta 255; no tolerance or image alignment.
- **s235 DoAction entry coverage:** FAIL (exit 1): native evidence: events beyond completion boundary. No receipt issued; zero admitted samples. Full raw trace and build retained.
- **s236 Clip-action handler coverage:** FAIL (exit 1): 61/61 samples; 2844 clip entries / 13 handlers; 626 unvisited and 416 uninstrumented obligations.
- **s237 Call-site and branch observations:** FAIL (exit 1): native evidence: events beyond completion boundary. No receipt issued; zero admitted samples. Full raw trace and build retained.

148 项聚焦测试通过。失败原始轨迹完整保留；无游戏运行时改动。
`production_admitted=false`、`native_parity_proven=false`。
[角色总览与复现](../evidence/sampling-upgrade/s231/README.md)。

## s238–s244：玉龙 attack 单格七维（同一角色 PR）

仅 `yulong__attack__neutral__ground__near`；锁定小写源路径 `scripts/fighter/yulong.json` 与 `game/fighter/yulong.swf`。

- **s238 Native receipt:** PASS (exit 0): 4742 native events, 122 actor observations. Required-native selected Godot execution passes (1/324); full campaign rejects missing receipts.
- **s239 Global geometry:** FAIL (exit 1): native receipt valid; 61 raw geometry boundaries, three missing-source-list errors for k1atm.mian at ticks 16–18. Full geometry and Godot comparison remain open.
- **s240 Child display list and camera:** FAIL (exit 1): native evidence: events beyond completion boundary. No receipt issued; zero admitted samples. Full raw trace and build retained.
- **s241 BitmapData and RGBA:** FAIL (exit 1): 61 native and 61 actual Godot viewport frames; 0/61 exact, 17595960 differing channels and 6839571 differing pixels. Maximum channel delta 255; no tolerance or image alignment.
- **s242 DoAction entry coverage:** FAIL (exit 1): 61/61 samples; 416 entries / 31 visited blocks; 428 unvisited and 592 uninstrumented obligations.
- **s243 Clip-action handler coverage:** FAIL (exit 1): 61/61 samples; 2758 clip entries / 14 handlers; 591 unvisited and 415 uninstrumented obligations.
- **s244 Call-site and branch observations:** FAIL (exit 1): 61/61 samples; 438 complete invocations (36 true / 402 false), 1 incomplete. Full AS/callee/Godot ownership remains unproven.

123 项聚焦测试通过。失败原始轨迹完整保留；无游戏运行时改动。
`production_admitted=false`、`native_parity_proven=false`。
[角色总览与复现](../evidence/sampling-upgrade/s238/README.md)。


## s245：茶渡 tick-10 调用退出／接收者寿命残留

按用户选择接续 s76，仅复用 Chad attack 单格 tape。原生 9,486 事件、61 根样本、
122 状态，收据复验 exit 0。调用入口、callee 入口和普通攻击 goto 前沿仍是同一
接收者；tick11 独立根观测见父帧 183、原深度槽为空、保存接收者的父/帧失效。
goto 后沿、callee 出口及 caller 后沿均未观测到，新退出 gate 与原 AS gate 均 exit 1；
不据此推断 VM 返回/中止语义。原 AS 594 未访问、415 未插桩保留。132 项测试通过，
122 个战斗状态与保留 s76 原生轨迹相同；不代表 Godot 一致性。两标志 false，
无游戏运行时改动，M0-02 保持 pending。[证据与复现](../evidence/sampling-upgrade/s245/README.md)。


## s246：迪达拉 summon 援助 atm1 几何来源残留

按用户选择接续 s64，仅原 summon tape。源帧44新放置 Woailuo Sprite48 / depth2 /
atm1，子 Sprite 唯一 DoAction 在帧33。九条新增原生观测确认：父帧44 stamp 只命中
援助根，随后 load 前后及 tick58–60 子帧1–3 的 ID/source/birth 均 undefined。
DoAction-only stamp 缺少首次查询前的子实例绑定，不能继承父 stamp 或猜源。
5,498 原生事件，收据 exit 0；来源绑定 gate 与原完整几何 gate 均 exit 1，保留
三条 unbound 错误。141 项测试通过，122 状态与 s64 原生保留轨迹相同；无 Godot
对照或运行时改动，两标志 false，M0-02 pending。[证据](../evidence/sampling-upgrade/s246/README.md)。


## s247：玉龙 attack k1atm.mian source-list 残留

按用户选择接续 s239，仅原 attack tape。九条新增观测确认 tick16–18 的 stamp 完整，
三个列表长度96/5/10，唯一失败条件是 target undefined：直接父级 k1atm.pn 未定义，
再上一层角色主体 pn=2。源放置链为 Sprite345/f188 → Sprite104/k1atm → Sprite2/mian；
函数存在触发的接收器扫描尚未证明该嵌套实例的受击所有权，不替换父级查找。
5,079 原生事件，收据 exit 0，来源诊断及完整几何 gate 均 exit 1；150 项测试通过，
122 状态与 s239 原生轨迹相同。两标志 false，M0-02 pending，无运行时改动，
未处理 s240 完成边界。[证据](../evidence/sampling-upgrade/s247/README.md)。


## s248：玉龙 display/camera 完成边界残留

仅接续 s240，同 attack tape。旧两条完整轨迹仍被原 validator 拒绝：tick60 done 后
根观察继续到61/62。新增仅此格启用的窗口关闭：保留终止根周期回调，在下一根回调
递增前关闭探针。两次正常退出捕获收据有效但未触发关闭分支；显式延迟退出对照
实际保留 done 后36条事件，再记录关闭标记，无 tick61。该对照7,981事件，
收据/61样本结构 exit 0，完整显示 gate 仍 exit 1（122源帧+44符号义务）。
159项测试通过，两标志 false，无游戏改动。约定的玉龙专项残留队列已留证：
s239由s247诊断，s240由本切片补齐捕获边界证据；不重开s241–s244，不代表全角色
或M0-02通过。[证据及对照条件](../evidence/sampling-upgrade/s248/README.md)。


## s249：修复优先级第一项——普通 display 完成窗口

先按跨角色收益、隔离程度与机制证据写[五类排序](../evidence/sampling-upgrade/next-fix-priority.md)，
本刀仅推广 s248 已证实的终止周期关闭到普通单维 display；混合模式及其他维度保持原行为。
一角 s233 原 tape 新正常/延迟退出均获有效收据、61样本/1533节点；延迟对照 done 后
保留34条同周期事件再关闭，无 tick61。完整显示仍169项义务 exit 1，旧拒绝轨迹不变。
两标志 false，M0-02 pending，玉龙专项证据队列不重开。[证据](../evidence/sampling-upgrade/s249/README.md)。

## s250：排名第二项——AImain 来源/帧归属诊断

s86/s93/s100/s248/s249 原始日志重算与既有报告一致：610条 AImain
记录全部为 frame 0、无 source stamp、无子节点；源放置归属角色 Sprite 3，
不是 main.swf。源 initCtrl 非 AI 分支执行 unloadMovie，但现有显示 ID
不能证明卸载前后的连续身份。禁止将0别名为1或删除节点；本次为 evidence-only，
未修复任何缺帧义务。新增源时间轴/节点保留负例；完整显示仍 exit 1，
两标志 false，M0-02 pending。[证据与下一步观测](../evidence/sampling-upgrade/s250/README.md)。

## s251：排名第三项——单一援助放置的 load stamp

仅原 s64 summon tape，显式 `--deidara-atm1-load-stamp` 在已核哈希的
Woailuo frame44 / Sprite48 / depth2 / atm1 load 末尾调用既有 stamp，
原 load 语句与 DoAction 不变。新原生捕获确认首次赋值与 tick58–60 子帧1–3
身份延续，三条 unbound 消失；61样本/241框可结构读取，完整几何仍因
tick11/41 缺 P1 receiver 而 exit 1（旧 s64/s246 原始记录也缺），不放宽义务。
收据和局部证明 exit 0；122状态与两份旧捕获完全相同，不代表 Godot 一致。
两标志 false，M0-02 pending，其他排名不重开。[证据](../evidence/sampling-upgrade/s251/README.md)。


## s252：排名第四项——AS 调用退出与 receiver 归属

原 s76 Chad tape 用现有 s245 探针在 master 5bd0d797 上新采一次，
9,423事件、61样本；goto 前深度占用，下一 root 样本深度为空，三个退出标记仍缺。
捕获 SWF 的 P-code 证明 goto 后与 caller 后的插桩已编入；这不是执行 PC 或 VM 返回证明。
不合成 call_after、不把消失当返回、不猜 ancestor pn。s247 原日志重算仍为 target 未定义，
属于独立的嵌套归属问题。本次证据型交付，无退出模型/玩法/验证器改动。
收据 exit 0，退出/调用/完整 AS 均 exit 1；594未访问、415未插桩义务保留。
122状态与 s76/s245 一致，两标志 false，M0-02 pending。
[完整观察、编译交叉检查与后续判别条件](../evidence/sampling-upgrade/s252/README.md)。

## s253：排名第五项——严格 RGBA / 时钟对齐诊断

只重算 s217 tape 对应的 s220 原生/Godot 配对，不重开 s241–s244 或排名1–4。
tick1–60 的120条角色状态在14字段完全一致；tick0 的两条 touchFloor
undefined/null 差异保留。tick13 源帧205/7匹配，但原图倒计时47/59。
原生每帧 BitmapData 编码中位1980ms，tick0到60耗时120118ms；
Godot逐图重建并同步推进，倒计时仍由独立墙钟 Timer 驱动。两侧均缺
倒计时回调 tape，因此相同 root-observer 标签不证明共同视觉相位。
没有证明安全的时钟修复，不调整运行时或渲染。严格RGBA重算保持
0/61、17732741通道/6864492像素差异、最大255，exit1。
历史收据不重签；当前完整CLI失败与原始结构重验分开报告。
两标志false，M0-02 pending。[证据与复现](../evidence/sampling-upgrade/s253/README.md)。

## s254：s253 后重排第一项——非 display 完成边界诊断

[新排序](../evidence/sampling-upgrade/next-fix-priority-after-s253.md) 优先恢复
非 display 捕获入口，随后是 AImain 卸载身份、几何 receiver、AS 正向续执行证明、
共同倒计时观测。只执行第一项，未开始其他排名。
s232 完整5705事件重算：done后34条仍在tick60/display525，16条在tick61/display526；
后者包含额外完整几何样本与第二次done。归档根回调先递增，再采样，再请求退出，
没有闭窗。该证据支持重入诊断，不证明向geometry推广s249闭窗；未改运行时或插桩。
原严格原生验证仍exit1、零准入样本，未发收据、未裁剪终止回调；完整几何闸门受阻，
未评估下游义务。两标志false，M0-02 pending。[证据与复现](../evidence/sampling-upgrade/s254/README.md)。


## s255：AFTER-s253 排名第二项——AImain 卸载身份

从 master `544ec6f5` / #132 出发，仅在一角 P1 的一次 initCtrl 卸载前后、
下一根边界与首采样记录保存引用、按名称查找和 getInstanceAtDepth 槽位对象。
复用 s231 锁定 tape，一次原生捕获8238事件。前三个边界仍为frame1/total2；
首采样变为0/0，source stamp及临时身份标记消失，父标记保留。
引用相等不等于底层分配身份，尚不能排除间隔内同槽替换；不做0→1映射或卸载豁免。
下一判别点是逐根定位首次0/0，并取得能区分保留引用与同槽替换的身份对照。
receipt和61样本结构通过；122条角色状态的14字段与s249完全一致；
完整显示保留169义务、exit1。生产运行时、严格验证器、排名1/3/4/5均未修改。
两标志false，M0-02 pending。[证据与复现](../evidence/sampling-upgrade/s255/README.md)。

## s256：AFTER-s253 排名第三项——P1 receiver tick11 可用性

仅观测 s251 同一原 tape 的迪达拉 P1 bdmn：源840非 MOVE 新放置，841无槽位变化。
新捕获 tick11 命名/depth对象存在，但两个接收函数、三个列表和stamp均undefined；
tick12初始化齐全。保存的旧引用也读到新字段，不能据引用相等声称实例连续。
证据不足以安全修改eligibility，保持原闸门；不补stamp、不替换ancestor pn。
一次5400事件、122角色状态与s251完全相同；receipt/诊断exit0，完整几何exit1，
61项聚焦测试通过。下一判别为该次跳转、Sprite2初始化及首个enterFrame的直接顺序观测。
两标志false，M0-02 pending；排名1/2/4/5、tick41、玉龙、BitmapData和玩法均未扩展。
[证据、成本与复现](../evidence/sampling-upgrade/s256/README.md)。

## s257：AFTER-s253 排名第四项——独立 AS continuation 判别

仅针对 Chad s76 tick10 的原始调用，使用预存普通对象和函数引用，
goto 后先寄存器写入，观察器入口先写入再执行旧 guard/receiver 查询。
调用前对照成功，tick11/12 post 与入口仍为0；编译序列存在不等于已执行 PC，
没有正向后续执行或 VM 返回证明，不实现退出模型。一次9727事件捕获，
122条角色状态与s252完全相同。91项测试通过，receipt/诊断exit0，
退出/调用/完整AS保留exit1（594未访问、415未插桩）。两标志false、M0-02 pending。
下一判别需精确 goto/Pop/SetMember 的执行 PC 和栈展开观测，分别记录移除与返回。
排名1/2/3/5、s254–s256、运行时和严格验证器未动；
[证据、捕获恢复说明与复现](../evidence/sampling-upgrade/s257/README.md)。

## s258：AFTER-s253 排名第五项——实际倒计时回调 tape

旧s220/s253无回调记录，不能从墙钟反推；保持同一输入和61帧原快照边界，
一次新捕获记录Sprite1813注册、70次回调的guard/数字帧及快照前后顺序。
15次暂停不递减但更新数字；现有源编译回调隔离重放70/70吻合，
122条角色状态与s220一致。新tick13倒计时50，旧47/59配对保持原样。
这只证明该tape的倒计时字段，完整子显示列表/相机共同视觉相位未证，
不接入生产时钟适配器，不按毫秒或30Hz猜回调，不重置计时或搜索图像偏移。
严格RGBA及历史完整bitmap gate保留exit1；receipt/诊断/编译回调重放exit0。
两标志false，M0-02 pending；排名1–4、s254–s257、运行时、阈值与验证器未动。
下一判别为同一回调快照契约下完整视觉状态绑定及配对Godot场景重放。
[证据、成本与复现](../evidence/sampling-upgrade/s258/README.md)。

## s259：s258 后重排——独立几何完成窗口

[新排序](../evidence/sampling-upgrade/next-fix-priority-after-s258.md) 根据 s254–s258
新证据调整为：几何完成窗口、receiver 初始化顺序、AImain 清空身份、回调绑定视觉状态、
Chad 执行 PC。只执行第一项，其他项未开始。

固定 s232 一角 tape 的独立包装器启用终止周期闭窗，未修改共享 builder。正常/延迟退出
收据与本格几何 gate 均 exit0（61样本/240框）；延迟对照保留34条终止回调，在下一根
计数前闭窗，无tick61。122条角色状态及输入相同；随机值不同且原样留存，不宣称随机
tape 重放或普遍行为不变。旧s232完整流仍exit1。67项测试通过，其他非display模式
不推广；production_admitted=false、native_parity_proven=false，M0-02 pending。
[证据与复现](../evidence/sampling-upgrade/s259/README.md)。

## s260：s258 后排名第二项——receiver 初始化顺序

仅跟进[AFTER-s258 排名2](../evidence/sampling-upgrade/next-fix-priority-after-s258.md)，
沿用s256/s64原输入与tick11采样边界，一次新捕获补齐源跳转前、Sprite2 frame1入口/出口、
首个bdmn enterFrame。事件序号证明几何结束早于frame1初始化，首回调已到父帧841；
根计数尚为tick11，不能把它误称放置当帧回调。跳转后标记缺失不推导VM返回语义。
初始化时序已观测，eligibility修复未证；不提前初始化、不移动采样、不改运行时。
5274事件全流保留，122角色状态、61输入与954按键读取对s256相同，随机差异保留。
68测试通过，receipt/诊断exit0，完整几何仍exit1（tick11缺P1 receiver）。
production_admitted=false、native_parity_proven=false，M0-02 pending。
下一判别是在同一未初始化区间观察真实源碰撞查询及其操作数，带正向观测对照，
不得人工调用方法或豁免接收方。排名1/3/4/5、s254–s259、tick41、nested Yulong、
ancestor-pn、严格验证器及基准未动。[证据、成本与复现](../evidence/sampling-upgrade/s260/README.md)。

## s261：s258 后排名第三项——AImain 内容清空与身份

2026-10-30（采样 s261，s258 后排名第三项）：仅跟踪一角 P1 AImain 卸载后的每根 root，root8仍1/2、root9首次0/0。独立保留/同名同深度替换对照证明旧引用相等不能判身份；替换与保留实例但删标记信号相同，清空后身份判别仍未证明，不做映射修复。一次8290事件捕获，122角色状态与s255一致；receipt/诊断exit0，完整显示169义务、exit1。两标志false，M0-02 pending；排名1/2/4/5和s254–s260未动。

下一判别需要在root8/9间记录原生播放器分配身份，并以保留内容清空与同路径替换校准；AS2引用和丢失标记不足。
[证据、成本与复现](../evidence/sampling-upgrade/s261/README.md)。

## s262：s258 后排名第四项——回调绑定的视觉状态

2026-10-30（采样 s262，AFTER-s258 排名第四项）：一次有界新捕获扩展回调快照，记录32227事件、2194视觉节点和9次frame1初始化；68次回调重放吻合，122角色状态与s258一致。数字frame1重入不能当出生；Godot配对场景的HUD选定字段一致，但tick13相机X为原版-0.05/Godot0，寿命与开场回调连接仍未证明。成像前拒绝exit1，不写新Godot图片、不接生产适配器；两标志false，M0-02 pending；排名1/2/3/5及s254–s261未动。

下一判别是独立于frame1重入的PlaceObject寿命对照，以及注册至首快照期间HUD子时钟、相机更新与Godot开场边界的连接；先过状态断言再成像。旧s258 tick13=50、s220 47/59均保留，新捕获tick13=49不移植到旧图。
[证据、成本与复现](../evidence/sampling-upgrade/s262/README.md)。


## s263：s258 后排名第五项——Chad goto 执行后续判别

2026-10-30（采样 s263，AFTER-s258 排名第五项）：复用锁定s257构建，一次新捕获9774事件；同一root定义函数的保留/移除动态接收者对照均完成寄存器写入，移除后槽位为空有独立正观测。但这不等于Chad函数定义时间轴失效；原goto后的post/entry仍0，精确PC/栈与退出模型未证明。122角色状态与s257一致，95聚焦测试通过；receipt/诊断exit0，精确continuation/生命周期/调用/完整AS均exit1。两标志false，M0-02 pending；排名1–4、s254–s262、生产运行时与严格验证器未动。

下一判别需要在原生子时间轴内定义函数、绑定定义上下文并配对保留/移除goto；root定义函数只换this不足以证明上下文失效。仍无正对照时需精确CallMethod/Pop/SetMember的原生执行PC与栈观测。
[证据、成本与复现](../evidence/sampling-upgrade/s263/README.md)。
