# r248 — Owned native abort; no final-image admission

The same source-bound60-second workload and one-hit hardware callsite logic were retained. The diagnostic added only timestamps around the existing detach and an optional post-detach observer: exact ownership/run-marker checks, process state, and one bounded one-second sample. The observer requires a successful current detach receipt; errors cannot skip the owned capture lifecycle. Focused tests **23/23** pass, including AST equivalence of the hardware script after removing the two timing assignments.

**The native experiment fails.** Owned PID70251 exited with SIGABRT before a verified callsite hit. The breakpoint was removed, detach failed because the connection was gone, and the observer correctly skipped. No process-state query or sample was executed. Capture retained43 events with no final image/done marker; command exit1 and no owned process remains.

The independently PID-matched crash report confirms EXC_CRASH/SIGABRT on the main thread, but provides no explanatory termination string and warns that RIP does not match the crashing frame. Render-traversal frames do not establish the cause. Do not attribute the abort to ScriptLimits, Rosetta hardware-breakpoint handling, or rendering arithmetic without further evidence. No retry, software breakpoint, target expression, signing or security change was used.

Available source readbacks **3680/3680** and source matrices remain exact; final240000-pixel sanity is **unavailable**, not passed. Instrumented traces are not replacement references. Full diagnostic count remains **46/54**, and all candidate/GPU/production flags remain false.

## Evidence and reproduction

`debugger/feasibility.json` retains the skipped observer and host monotonic timing. `debugger/debugger-result.json` retains the failed detach and embedded-LLDB timestamps. These clocks have different observed origins: compare durations within each domain only. The host debugger invocation lasted about35.1544seconds; the complete capture lifecycle about90.0967seconds. See `monitor-conclusion.md`, `owned-crash.ips.gz`, `partial-baseline.json`, and the strict baseline rejection log.

```sh
python3 -m tools.probes.build_jinye_debugger_profile --output /tmp/r248/native --ffdec /path/to/ffdec-cli.jar --duration-ms 60000
python3 -m tools.probes.probe_owned_source_monitor --build /tmp/r248/native --output /tmp/r248/debugger --player-app '/path/to/Flash Player.app' --disassembly /path/to/pinned-player.asm --allow-window-activation
python3 -m tools.probes.check_jinye_debugger_baseline --native /tmp/r248/native --output /tmp/r248/baseline.json
python3 -m unittest tools.tests.test_owned_source_call tools.tests.test_owned_hardware_entry tools.tests.test_owned_debugger_probe tools.tests.test_owned_guest_memory tools.tests.test_owned_native_monitor
```

Commands describe the retained experiment, not approval to keep repeating an unstable instrumented run. Use fresh builds/output/run IDs for any separately justified future experiment; archived SWF bytes are omitted and cannot be silently skipped by baseline verification.

## Next discriminator

Do not add more native traps while completion is unexplained. Test one independently instruction-derived float32 hierarchy-composition construction against retained source controls instead: pin the generic composition float branch, preserve its integer-translation rounding at each boundary, and compare globally with the current exact-combine-then-quantize hypothesis. Keep the MXCSR rounding assumption and bitmap-fill routing explicitly unproved. Reject against all retained r233 controls and the r242 local counterexample; do not select an arithmetic path from RGB or fitted phases. This can advance source arithmetic without treating incomplete debugger observations as production proof.

Separate merge gates remain Jinye4, Yijiao4, production54 or explicit gameplay non-admission, and full AS/clip-action ownership. `production_admitted=false` is an evidence flag, not a gameplay kill-switch. No runtime changes this round. Fresh cache/fingerprint/protected/integrity/handoff/contracts checks are separate from the **failed native experiment**; full roster/Web/Python and production54 were not rerun. Keep Draft; no merge/deploy/Worker.
