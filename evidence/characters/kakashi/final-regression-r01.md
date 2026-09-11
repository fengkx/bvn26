# Kakashi final frozen regression r01

状态：最终冻结回归完成。所有结果来自同一冻结工作树；原始大日志与逐案 native/compare 输出保留在 `/private/tmp/kakashi-final-regression-r01/`，本记录只保存可审计摘要。

## Scope and result

- Base-form Kakashi：20 cases，20/20 `matched`。19 cases compare 602 source/native actor states；`kakashi-863-super-down-special-nohit` compare 2202/2202。
- PVP 与 training-timer：各 602 actor states matched。
- 每个副本 fixture 都显式写入 `p1_helper` 与 `p2_helper`，值直接来自对应不可变 source `build.json` 的 `configuration.p1sf/p2sf`，本批实际为 `我爱罗` / `魂`。统一副本清单保留在 `/private/tmp/kakashi-final-regression-r01/fixtures/manifest.json`，机器记录见 [final-regression-r01.json](final-regression-r01.json)。

## Reproduction

20 案 native 使用 Godot 4.7.2、`move_case_reference.gd --batch`，输入副本及输出目录见 `/private/tmp/kakashi-final-regression-r01/plan.json`。每案随后以 `compare_mode_reference.py` 对应原始 events。PVP/training 命令为：

```sh
python3 tools/test_shared_modes.py --godot /tmp/godot-4.7.2/Godot.app/Contents/MacOS/Godot
```

r13/r14/r15 的连续回放均使用以下完整命令模板，`<absolute-events>` 分别指向 `evidence/ai/input-binary-r13/events.jsonl`、`input-binary-r14/events.jsonl`、`match-flow-r15/events.jsonl`；每条命令的实际绝对 argv、tape/build 哈希和新输出路径都记录在机器 JSON 中：

```sh
/tmp/godot-4.7.2/Godot.app/Contents/MacOS/Godot --headless --path /Users/fengkx/me/code/bvn2_6/godot -s res://tests/intro_continuous_reference.gd -- <absolute-events.jsonl> <new-report.json> combat
```

各 source 目录的 `random-tape.json`、`clock-tape.json`、`build.json` 和 r15 的 `post-done-events.jsonl` 是不可变旁证；脚本从 `events.jsonl` 重建 tape，命令不接受隐式或另行传入的 tape 参数。新报告位于 `/private/tmp/kakashi-final-regression-r01/legacy-replay/r13/report.json`、`r14/report.json`、`r15/report.json`。三者均为 `segment_observed_fields_match`，分别有 897、867、6281 frame comparisons，random/clock tape complete。

历史 `/tmp/kakashi-regressions/r13-abs.*`、`r14-abs.*`、`r15-abs.*` 未覆盖。

## Freeze and boundaries

冻结前后 11 个 runtime/compiler/generated 文件哈希完全一致，详见 `/private/tmp/kakashi-final-regression-r01/freeze-after.json`。错误门禁扫描了 `SCRIPT ERROR`、`Parse Error`、`Invalid key`，均未发现；原始日志中的 Godot macOS certificate 与并发 `user://` log-open 错误保留为环境消息，未改变退出码、marker 或报告结果。

旧 r01 重叠 capture、旧 r02 混合哈希记录和旧 super candidate difference 文件均保留，不能替代本次冻结结果。此证据覆盖源驱动状态/几何回放；像素、音频和完整浏览器视听一致性仍按总验收边界处理。
