# Kakashi original capture r02

状态：`original_capture_completed_not_port_parity`。本批在明确的独占原版 Flash 窗口中串行完成；原始日志、build、收集目录、Godot native 结果和 compare 结果均保留在 `/private/tmp/bvn-kakashi-original-r02/`。r01 与其他 Flash 会话重叠的旧 capture 不计入本批。

Source inputs were the locked `game/main.swf` (`707fac0ec6bb2af1a3d18dc308dd403cb556a0988144b0f6f10555382287f92`) and Kakashi SWF (`48587becee990fccfd7450a1b605a24b2d654dbd15569857659f67346bddb2fc`). The Flash player was launched through `tools/probes/capture_native_player.py` with the shared flock and `--allow-window-activation`; all 20 valid captures ran after the explicit window grant. The native comparisons were generated around a concurrent Kakashi compiler candidate transition; exact per-run data hashes were not recorded, so these results are baseline diagnostics and must be re-run uniformly before candidate acceptance.

No per-case data hash was recorded before each native run. For retrospective reference, the repository `HEAD` versions at the time of this write hash to `data/actions/Kakashi-base.json`: `6bf0b09e24ee95c7afc41ab8599a6e9f43dfe5bf4be78529cd2f951be3646fd0`, and `godot/generated/fighters/kakashi/combat.json`: `334ee99b81cf361c04f6375bcff87f0010616551b8b119c9bdf014542f0db172`; these hashes are not proof that every native result used those exact bytes. The current candidate files hash to `4d135f96adcf01a67c52eb11f4716de3b99c55a5ead0fd38af4dbbe620173891` and `c52e4e7089db5ddc4d1116d8eefe9c44f41c746fbe5a3c44123641715c2b8507`, respectively. A uniform candidate rerun is required.

基准输入固定为 `/private/tmp/kakashi-case-inputs-final/` 下的 19 个 in-scope fixture，另加 `/private/tmp/kakashi-cases-r01/kakashi-863-super-down-special-nohit.json`（1100 ticks）。每个正常案例为 300 fight ticks，均有唯一 `ready`，且 first `done` 达到 300；`kakashi-689-bisha-energy_below` 在 first `done` 后因 Flash 异步退出又发出一次 fight tick 301 的 `done`，该 38 行尾部被单独保留。no-hit 案例为 1100 ticks、2202 source/native 状态。目标帧是否进入按原版收集事件中的 slot 状态判断；negative 案例的目标动作未进入是预期行为。

| Case | Original events | Target reach | Native / compare |
|---|---:|---|---|
| `kakashi-193-nornalhit-neutral` | 12347 | yes | 602/602, matched |
| `kakashi-129-airhit-air_target` | 11889 | yes | 602/602, matched |
| `kakashi-156-airMagichit-air_target` | 11050 | yes | 602/602, matched |
| `kakashi-193-nornalhit-dash_twice` | 12333 | yes | 602/602, matched |
| `kakashi-193-nornalhit-mirror` | 12306 | yes | 602/602, matched |
| `kakashi-22-rush-dash_twice` | 12418 | yes | 602/602, matched |
| `kakashi-22-rush-neutral` | 12596 | yes | 602/602, matched |
| `kakashi-301-skill1-guard` | 8398 | yes | 602/602, matched |
| `kakashi-42-jump-neutral` | 12474 | yes | 602/602, matched |
| `kakashi-689-bisha-energy_exact` | 8709 | yes | 602/602, matched |
| `kakashi-689-bisha-neutral` | 9619 | yes | 602/602, matched |
| `kakashi-74-jump-neutral` | 12168 | yes | 602/602, matched |
| `kakashi-757-bishaUP-energy_exact` | 8519 | yes | 602/602, **different** |
| `kakashi-863-bishaSuper-dash_twice` | 9903 | yes | 602/602, matched |
| `kakashi-863-bishaSuper-energy_exact` | 6689 | yes | 602/602, matched |
| `kakashi-1030-zhaoHuan-energy_below` | 11012 | no (energy gate) | 602/602, matched |
| `kakashi-689-bisha-energy_below` | 11036 | no (energy gate) | 602/602, matched |
| `kakashi-757-bishaUP-energy_below` | 10973 | no (energy gate) | 602/602, matched |
| `kakashi-863-bishaSuper-energy_below` | 12078 | no (energy gate) | 602/602, matched |
| `kakashi-863-super-down-special-nohit` | 32946 | yes (target window; no hit) | 2202/2202, matched |

The only production comparison difference is `kakashi-757-bishaUP-energy_exact`: first difference is tick 77, slot `p2`, source frame `738` versus native frame `2`; at tick 78 source has `action=-1`, `hp=950`, `ql=305`, `hits=1`, while native remains idle at full health. The source state at tick 77 has p1 at frame 823, `(x,y)=(300,-25)`, and p2 at frame 738, `(x,y)=(350,-25)`. The source log records fighter states and does not expose a separate projectile instance field. The independent source diagnosis identified the missing dynamic `sbsatm` name at source frame 821; no runtime or threshold was changed during this capture batch.

The first `kakashi-757-bishaUP-energy_below` attempt used run `kakashi-r02d-kakashi-757-bishaUP-energy_below` and timed out after 9868 events without `done`; that raw log remains retained and is excluded from acceptance. A fresh build/run `kakashi-r02e-757-bishaUP-energy_below` completed with 10973 events and is the row above. The `kakashi-689-bisha-energy_below` log contained a second asynchronous `done` at fight tick 301; collection therefore used `--retain-post-done-frames`, preserving the first done at fight tick 300 in `collected-r02` before comparison.

The 15 successful target-positive cases, four energy negatives, and the separate no-hit case cover the 19 in-scope IDs from `native-matrix-r01.json`; the two null timeline cases remain excluded by scope. Native comparisons were run against the frozen runtime before the pending Kakashi dynamic attack-name candidate is applied; the 757 positive difference must be rechecked after that candidate is built.
