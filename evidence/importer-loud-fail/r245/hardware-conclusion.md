# Bounded hardware-entry feasibility

One fresh, source-pinned Jinye workload was launched through the approved capture lifecycle. The executable hash and movie/run identity were checked before attaching to its unique owned PID59702. LLDB attached to the x86_64 process and successfully created a hardware-only execution breakpoint at file address0x10029dad0, loaded at0x102606ad0. The new stop ID2 reported the exact breakpoint/location pair and exact entry PC. The breakpoint was removed and the debugger detached; capture completed447events and no owned process remained.

The independently pinned generic compose entry reads fields through offset0x18 from RDI/RSI (`0x10029dadd: movl 0x18(%rdi),%eax`; `0x10029dae8: testb $1,0x18(%rsi)`). Only28bytes from each input pointer and the8-byte stack return address were read; RDX was retained as an address without reading its output buffer. These are unclassified generic operands, not identified source-fill matrices. The observed return mapped to pinned direct call0x1005e8dd6→0x10029dad0. This caller was not among the source-profile sampled edges, so the first generic-entry hit does not establish the bitmap-fill route.

Before/at-stop entry bytes returned by LLDB matched the pinned16-byte prefix. SBProcess.ReadMemory documents masking of software breakpoint traps, therefore this does NOT independently prove the physical entry bytes unchanged. The receipt explicitly retains `physical_entry_bytes_independently_verified=false`; only our breakpoint's hardware requirement/report and verified stop are established. No software fallback, target-memory write, target expression, signing or security change was requested. Instrumented output is not a native pixel reference.

Next discriminator: independently verify raw entry bytes if a permitted read-only task-memory interface is available, without treating LLDB's masked read as proof. Then narrow a bounded hardware stop to one independently sampled caller (e.g. the pinned direct call at0x1000f28db), verifying its exact call instruction and collecting only the established generic ABI operands. Map source ownership through independent operand/provenance evidence before proposing arithmetic. No operand-derived renderer, coordinate fitting, or production admission follows from this feasibility pass.

Reproduction:

```
python3 -m tools.probes.probe_owned_hardware_entry --build FRESH_BUILD --output FRESH_OUTPUT --player-app '/Users/fengkx/me/code/flash-player/Flash Player.app' --disassembly PINNED_DISASSEMBLY --allow-window-activation
python3 -m unittest tools.tests.test_owned_hardware_entry tools.tests.test_owned_debugger_probe -v
```

Focused tests11/11 pass. All admission flags remain false.
