# r246 — Independent task-memory attempt fails closed

The fresh owned Jinye probe attached successfully, but the host-side libSystem `task_for_pid` returned5 before any Mach memory read or breakpoint creation. The exact error is retained; it does not identify the underlying permission cause and does not contradict LLDB's demonstrated access. No privilege, signing or security change, software breakpoint fallback, or retry was used. Detach succeeded and no owned process remains.

The new bounded reader requests exactly16 bytes at the pinned guest virtual entry address and releases any acquired task right in `finally`. PID conversion rejects values outside signed32-bit range and booleans. Guest virtual bytes are explicitly distinct from physical memory or Rosetta translated instructions. The hardware probe stops before operands when the independent-read prerequisite fails. Tests **15/15** pass.

Original source readbacks **3680/3680**, final raw RGBA **240000/240000** and premultiplied RGBA **240000/240000** remain exact against r242. These instrumented outputs are sanity checks, never new references. Complete diagnostics remain **46/54**; this round changes no rendering arithmetic or runtime. All candidate/GPU/production admission flags remain false.

## Reproduction

```sh
python3 -m tools.probes.build_jinye_debugger_profile --output /tmp/r246/native --ffdec /path/to/ffdec-cli.jar --duration-ms 60000
python3 -m tools.probes.probe_owned_hardware_entry --build /tmp/r246/native --output /tmp/r246/debugger --player-app '/path/to/Flash Player.app' --disassembly /path/to/pinned-player.asm --allow-window-activation
python3 -m tools.probes.check_jinye_debugger_baseline --native /tmp/r246/native --output /tmp/r246/baseline.json
python3 -m unittest tools.tests.test_owned_hardware_entry tools.tests.test_owned_debugger_probe tools.tests.test_owned_guest_memory
```

Use fresh run IDs and output directories. The evidence archive omits SWFs; baseline replay requires the original build bytes or a freshly rebuilt and captured run. The outer harness breakpoint-mode flag describes the requested mode; the inner receipt has no hardware command and an empty cleanup list because this run stopped before creating one. See `raw-memory-conclusion.md`, `debugger/debugger-result.json`, `review.md`, and `provenance.json`.

## Next discriminator

Independent raw guest-byte proof remains unavailable through this host interface. It is separate from a bounded hardware-only diagnostic of source-call operands; do not claim it passed. Narrow the next capture to the independently source-profile-observed, byte-pinned CALL at0x1000f28db. Its argument setup is statically RDI=RBX+0x48, RSI=R14, RDX=RBP-0x230. Verify the exact callsite/hardware stop and retain the raw-byte caveat; a pre-CALL RSP is not the callee return slot. Record unclassified operands and identify provenance through source-matrix/structural controls, never by selecting hits or formulas from RGB agreement. No software fallback or target expression.

This explicitly revises r245's sequencing: testing the independent interface produced a recorded denial, not raw-byte admission. It need not prevent separately scoped, instrumented operand observations with that limitation retained. Source-fill ownership, the one-pixel local counterexample, complete Jinye/Yijiao images, production54/runtime admission and full AS ownership remain open.

## Acceptance scope

Fresh focused tests and mandatory cache/fingerprint/protected/integrity/handoff/contracts checks are recorded in `acceptance.json` and `checks/`. Full roster/Web/production54 and full Python were not rerun for these diagnostic-only changes; earlier results remain historical. Keep Draft; no merge, deployment or Worker action.
