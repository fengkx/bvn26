# 白哉固定输入原版捕获 r01

这是可持久复核的最小捕获包，大小约 272 KiB。压缩日志和事件保留完整序列，summary/build/environment 保留配置、计数、源哈希和 done 边界。

文件：

- `original.log.gz`：原版 Flash 全部本 run 事件。
- `events.jsonl.gz`：collector 解码前的事件流。
- `summary.json`：11,503 事件、唯一 `done`、360 个 fight tick、输入绑定、随机 tape 哈希和限制。
- `random-tape.json`：固定随机输入。
- `build.json`、`capture-environment.json`：构建与播放器环境。

哈希（SHA-256）：

```text
original.log.gz  d15207526275dd5f7e4ae070c78f3f6483ca9afb245a3763df900876531ccf79
events.jsonl.gz  2563f887337489d20fffc91780f4fbd9b5c752b3f2f9da94650b9f4c9f712454
summary.json     fdd351d2c4469659e080063c4248f2d0eddfced0b4f8001bc72ed41f210d065a
random-tape.json 94278be1a7b09ca1bbed562a952e8ab3d60c2b7d1cb08c41562924cfa0e85408
```

复现命令见上级 [`native-capture-r01.md`](../native-capture-r01.md)。上级记录中的 `/private/tmp` 路径只用于重跑，不是证据唯一来源。
