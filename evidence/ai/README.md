# AI static-analysis evidence

Current reference-input correction: [callback registry and input](callback-registry-and-input.md). Captures made with the old global `Key.isDown` replacement do not prove delivery of the logged input. Use `input-alias-r12` for per-read verified input; preserve all older records as diagnostics.

Date: 2026-09-08. Status: source audit, compiler checks and partial original capture; no port parity acceptance.

The specification is [AI_SPEC.md](../../docs/AI_SPEC.md). The native compiler is
not connected to battle. The original fixed easy fight has been captured but not
replayed against Godot. M5-03 remains pending; the execution profile is provisional.

## Reproduction

```bash
python3 tools/analyze_ai.py
python3 tools/analyze_ai.py --check
python3 tools/verify.py
python3 tools/check_handoff.py
```

`source-audit.json` indexes all 62 retained script bundles and uses the existing
minren/yihu base timeline exports for geometry and display membership. Input
SHA-256 values are embedded. It is analysis evidence, not a production data
contract, compiled AI program, or proof that every discovered controller is
reachable. Existing timeline exports were not regenerated during this analysis.

## Observed static results

- 35 main fighter bundles, 26 assistance bundles, and one main bundle scanned.
- 69 controller scripts in nine exact-source groups; member paths, hashes,
  changed functions and full diffs against the standard controller are retained.
- 49 identical `randAI` definitions across all 35 main fighter bundles.
- The only observed assignments to the five AI random fields are the five
  ordered assignments inside `randAI`.
- 311 source lines contain `Math.random()` or `random(...)`; this is a lexical
  inventory, not a count of executed calls or proof of RNG stream identity.
- Every indexed base-slice Sprite 16 enterFrame placement has matching linear
  display-list membership. Membership includes placement frames and is not
  equivalent to executed callback ticks.
- Both base AImain clips contain 11 sensors on frame 2. The standard controller
  references `absmian`, which is absent from those two frame-2 display lists.

## Initial static-audit validation boundary

The audit freshness check, retained-input verification and handoff checks passed
for this change. They verify source association, reproducibility and document
links/dependencies only. No Godot smoke or new Flash AI test was run: no runtime
code or schema was changed. The specification lists the required future tests
as AI-T01 through AI-T14 and unresolved runtime questions as AI-U01 through
AI-U09. A missing reference, timer-lifetime issue or decompiler oddity is recorded
as a question to verify, not silently repaired.

The pre-change retained-input verification also passed. Manifest updates for this
work are limited to the explicitly edited documentation/task entries and the new
AI artifacts; unrelated working-tree changes were preserved.

## Subsequent compiler work

See [compiler-progress.md](compiler-progress.md) for the native predicate compiler,
scalar translation checks and parent-goto probe. This later work does not change
the full-battle acceptance status above.

Recovery movement and controlled cross-actor callback order: [recovery-order.md](recovery-order.md). The r09/r10 fixtures disprove a fixed whole-fighter callback order; full match parity remains pending.

- [Player source controller, binary64 trace probe and r13 failure](player-controller-and-binary-trace.md): source-derived integration and focused tests; complete parity remains pending.

- [Effect random calls and repeated source hit queries](effect-random-and-repeat-contact.md): r13 advances through the recorded boundary sequence; root observations and termination remain mismatched.

- [Effect registration order and root observer](effect-registry-and-root-observer.md): r13 discrete segment matches; independent r14 remains a failing projectile-name case.

- [Deferred projectile names](projectile-deferred-rename.md): r13 and r14 discrete segments now both match; complete match/geometry/presentation parity is still pending.

- [完整比赛倒计时与超时审计](match-timeout.md)：5 个剪辑、18 份源脚本及逐帧结构；原生实现和完整比赛对照待完成。

- [r15 原版整场 KO 与原生首差异](match-flow-r15.md)：两局 KO、换局、返回选人；原生 735/726 顺序不一致，尚未覆盖超时。

- [共用受击规则修复](receiver-rule-fixes.md)：35 个主角色函数分组、四项源修复、7 项原生测试与 r15 首局 KO 恢复差异。

- [KO instance scheduling and round continuity](ko-instance-scheduling.md): shared root/child lifecycle, round-reset retention and full r15 fighter-field comparison; countdown and full parity remain open.
