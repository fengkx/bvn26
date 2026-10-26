# r247 — Source-profile callsite observed; final capture incomplete

A hardware-only stop at the independently r243-profile-observed CALL0x1000f28db verified the exact new stop, location/PC, pinned logical instruction bytes, and all three argument relations: RDI=RBX+0x48, RSI=R14, RDX=RBP-0x230. It read only two28-byte input structures and retained the output pointer without dereferencing it. At this pre-CALL location, no callee return-address read from RSP is valid or attempted. The breakpoint was deleted and the debugger detached.

The first structure decodes as identity with flag1. The second has four floats `(0.03904970735311508,0,0,0.03904970735311508)` and integer fields `(1061,725,1)`. A destination quarter-coordinate interpretation is only a hypothesis; these numbers do not establish the source object's identity or authored-fill ownership. All source/operand admission flags remain false. LLDB logical readback still does not independently prove guest virtual or physical instruction bytes.

**The overall experiment fails.** Native capture ended at43 events, after the source and matrix/profile records, without a final image or done marker. The strict full-baseline checker rejects. Available source raw/premultiplied pixels **3680/3680** and matrix/bounds readbacks independently match; final240000-pixel comparison is **unavailable**, not passed. No owned process remains after capture cleanup. The CLI now explicitly rejects incomplete capture, missing hardware evidence, debugger timeout/failure, or incomplete breakpoint cleanup rather than treating successful receipt creation as experiment acceptance. Focused tests **20/20** pass.

The retained run-specific global Flash log contains no additional error text. r245/r246/r247 movies contain no ScriptLimits tag; neither fact establishes the cause. Artifact timestamps show approximately34.54 seconds between debugger script creation and receipt, then54.84 seconds before capture cleanup; these are filesystem observations, not native getTimer or exact attach durations. See `termination-inspection.json` and `script-limits.json`.

## Reproduction

```sh
python3 -m tools.probes.build_jinye_debugger_profile --output /tmp/r247/native --ffdec /path/to/ffdec-cli.jar --duration-ms 60000
python3 -m tools.probes.probe_owned_source_call --build /tmp/r247/native --output /tmp/r247/debugger --player-app '/path/to/Flash Player.app' --disassembly /path/to/pinned-player.asm --allow-window-activation
python3 -m tools.probes.check_jinye_debugger_baseline --native /tmp/r247/native --output /tmp/r247/baseline.json
python3 -m unittest tools.tests.test_owned_source_call tools.tests.test_owned_hardware_entry tools.tests.test_owned_debugger_probe tools.tests.test_owned_guest_memory
```

Use fresh builds/run IDs/output paths and serialized owned native captures. The initial executable command returned0 while printing an incomplete receipt; the new CLI acceptance check correctly rejects that retained result. Do not reinterpret the old exit code as success. SWFs are omitted from the archive; original bytes are required for strict replay or build/capture afresh.

## Next discriminator

Before collecting more calls, repeat the same one-hit diagnostic with explicit host timing and a single bounded read-only post-detach owned-process state/sample. Determine whether the process is rendering, stopped, or waiting elsewhere; do not guess a script-timeout cause or change ScriptLimits without evidence. Revalidate exact PID/movie/binary ownership before sampling, and preserve all failures/cleanup.

Once full instrumented completion is restored, collect a predeclared eight consecutive hits at this same callsite, retaining every ordinal and pointer/raw structure rather than selecting a numeric match. Then use independent child/outer/fill/draw controls to establish matrix provenance. Jinye's exact sampler and local counterexample remain unresolved; no rendering arithmetic or production path changes here.

## Acceptance scope

Mandatory cache/fingerprint/protected/integrity/handoff/contracts checks remain recorded separately from the **failed native completion gate**. Complete diagnostics remain46/54; production54 remains historical9/54. Full Python/roster/Web were not rerun for diagnostic-only edits. Candidate/GPU/production admission false, full AS ownership open. Keep Draft; no merge/deploy/Worker.
