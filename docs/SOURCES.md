# 来源、证据和选型依据

检查/编制日期：2026-09-03。网络来源对应本次读取时的内容，具体二进制按哈希锁定。

| 来源 | 用途与证据边界 |
|---|---|
| 用户 `166.swf` → `game/main.swf` | 普通 2.6 的版本、舞台、帧率、配置与主逻辑基准；SHA-256 在根 SPEC 和 manifest 中 |
| [Ruffle 问题记录 #12788](https://github.com/ruffle-rs/ruffle/issues/12788) | 提供公开 2.6 launcher 的资源地址；不证明模拟器行为完全等同原播放器 |
| [公开 launcher](https://flashga.me/public/storage/games/bleach-vs-naruto-2.6-files/launcher.swf) | 之前与用户入口逐标签对比，仅一处初始化脚本不同，脚本差异为 fullscreen/normal；对应资源有逐文件来源与哈希 |
| [Brx86/BVN2.6 固定提交](https://github.com/Brx86/BVN2.6/tree/f53f104d5b5b480c249fef4b33137c12c8d3a625) | 审计得到“社长改”、29 FPS、改版形态和大小写问题；仅复用 25 个相同资源 |
| [JPEXS 26.2.1](https://github.com/jindrapetrik/jpexs-decompiler/releases/tag/version26.2.1) | 本次反编译使用的工具版本；导出源码需结合原字节码/运行检查 |
| [Godot 官方版本归档](https://godotengine.org/download/archive/) | 官方列出 4.7.2-stable（2026-08-18）；本方案选定该版本，项目内尚未验证 |
| [Godot Web 导出文档](https://docs.godotengine.org/en/stable/tutorials/export/exporting_for_web.html) | WebAssembly/WebGL2、Compatibility、单线程导出及音频/浏览器限制的选型依据 |

逐资源记录已集中在 `manifest.json` 的 `assets` 和 `repository_review`。本包没有复制一套新的“社长改”资源；不同版本的比较结论不授权把它们互换为原版。

Godot 的 Web 文档说明当前 Godot 4 C# 项目无法 Web 导出，因此采用 GDScript。单线程有利于简化网页部署；Compatibility 为 WebGL2 路径。上述是官方能力说明，不是本游戏性能测试结果。

原版可见菜单模式名、动态帧顺序、准确判定边界和完整运行效果等未验证信息集中在 STATUS 与 REVERSE_ENGINEERING。不得将静态推断升级成已实测结论。
