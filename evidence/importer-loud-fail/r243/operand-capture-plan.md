# Conditional plan: owned-probe operand capture

This plan is not authorization to attach now. Complete the actual-source profile comparison first and select a call site from observed return-PC evidence, not from a formula matching pixels. Static LLDB availability does not prove runtime permission or Rosetta register support.

## Ownership and reproducibility prerequisites

1. Use a separately built, run-ID-pinned Jinye profiling SWF, the pinned Flash binary, and a new instrumented output directory. Preserve an uninstrumented completed baseline of the same source/tag hashes, graph, actual matrices and workload checksum.
2. Reuse the serialized native-capture lock and exact movie/binary matching in `tools/probes/capture_native_player.py`. The capture owner must supply its unique live PID after the run-specific start marker. Immediately before attach, recheck that same PID matches the exact movie path and pinned binary. Ambiguous, absent, stale or changed ownership fails closed; never attach to a user-opened player or another agent's capture.
3. Record the profile-selected static call address, executable SHA, module load address and verified instruction bytes. ASLR-adjust only from the owned process's module mapping. Do not guess addresses from another process.

## Bounded feasibility sequence

- First attempt only attaching to the owned probe and inspect architecture, program counter and availability of x86_64 argument registers. Use a short timeout (for example15seconds), then detach in a guaranteed cleanup path. If access is denied or Rosetta cannot expose the required state, stop and record the exact failure. Do not re-sign, alter entitlements, change Developer Tools/SIP/security settings, or attach elsewhere.
- Reading registers at an arbitrary interrupt is only a permission/architecture check; it does not establish the selected function's inputs.
- For actual function-entry operands, prefer a hardware execution breakpoint at one verified observed call target, with one bounded hit. Hardware support must be checked rather than assumed. If unavailable, report blocked; do not silently substitute software breakpoints, which modify executable bytes and would require an explicitly revised instrumentation scope.
- At the verified entry PC, read only the required argument registers and bounded memory regions for the matrix operands (no expression evaluation or function calls). Validate pointer mappings/readability and retain raw bytes plus exact integer/float interpretations separately. Do not infer a fill-matrix identity from a pointer's numerical value alone. Correlate with source properties and caller context before classifying an operand.
- Limit hit count and captured memory size in advance. Capture one call site and the minimum operand range needed by its pinned static instructions; do not dump unrelated process memory.

## Exit and evidence rules

Always remove the hardware breakpoint and detach; hand remaining lifecycle back to the existing native capture owner. On timeout/error, existing capture cleanup may terminate only its still-exactly-matched owned probe process. Retain debugger transcript, ownership checks, timestamps, module mapping and all failures.

Mark all instrumented outputs `pixel_reference=false`; timing interruption changes the workload. Never replace pinned native images with this run. Compare final source/matrix/checksum observations to the uninstrumented baseline only as an instrumentation sanity check. Even a matching checksum does not prove unobserved branches or universal rendering semantics. `production_admitted=false` throughout.
