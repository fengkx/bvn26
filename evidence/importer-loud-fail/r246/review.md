# r246 independent review (complete)

## Raw task-memory boundary

The r245 logical entry readback is not independent physical proof: SBProcess.ReadMemory can remove software traps. A separate direct Mach task-memory API read can close that narrow obligation only if it receives the same exact owned PID after ownership/run-marker revalidation, acquires its own task port without entitlement/security changes, and reads the predeclared 16-byte entry span while that same process is stopped. Validate the task API return status and exact byte count, preserve raw bytes, and compare against the pinned Mach-O bytes and the already established ASLR mapping. No scan, broad dump, write API, expression evaluation, or alternate-process fallback. Permission failure remains an explicit unresolved obligation. Deallocate acquired task rights, remove every created breakpoint, detach and let existing owned capture cleanup finish even when a read fails.

ReadMemory output, LLDB's hardware flag, and an independent task read are distinct observations and must remain separately named. This establishes bytes at one instant, not universal lack of instrumentation or source-fill routing.

## Next caller selection without output-based routing

r243 independently sampled compose call0x1000f28db in direct_uncached (2 inclusive observations), local_uncached (1), and requested invalidation (1). Its call bytes e8f0b11a00 and target0x10029dad0 are byte-verified. Predeclaring this site is a narrow input/evidence-based choice. Counts are not invocation frequencies and do not imply exclusivity.

A hardware breakpoint at the observed CALL instruction avoids stopping the generic compose entry on an unrelated caller. At that CALL PC, argument registers are ready under the statically verified ABI, but the callee's return address has NOT yet been pushed. Do not reuse r245's RSP return-address check there: verify the CALL bytes/target and separately label site+5 as anticipated return. Alternatively, predeclare a bounded sequence of entry hits and accept only the exact independently selected stack return, retaining all nonmatching hits/counts without broad operand reads. Neither approach is authorized merely by this review; implementation requires a fresh bounded plan.

## What is still required for source-fill ownership

One matching matrix value or source-sized scalar is insufficient. First trace the selected caller's operand pointer construction in pinned instructions and identify whether each operand comes from a fill record, display transform, destination draw transform, or temporary/cache field. Preserve unknown fields as unclassified.

Then use independently defined source controls changing only one of F (authored fill matrix), C (child transform), or outer/draw at a time, with original raw source and shape metadata pinned and native property readbacks retained. Any mapping must hold across controls at the predeclared callsite and a source/structural identity established independently of RGB or whichever numeric tuple happens to match. Do not select a hit by matching expected matrix values; if there are multiple indistinguishable objects/hits, report that ambiguity rather than fabricate fill ownership.

Raw physical-byte verification, generic ABI capture, bitmap-fill ownership, exact arithmetic, and production admission are separate gates. All rendering/production flags remain false.

## Implementation pre-launch review

Reviewed `read_owned_guest_memory.py` and its integration into `probe_owned_hardware_entry.py`. Reads are exactly16 bytes before breakpoint creation and at verified entry stop, with independent task_for_pid / mach_vm_read_overwrite and finally mach_port_deallocate. Nonzero status or incomplete bytes blocks operand capture; no fallback/security changes. The input guard was corrected to exact Python integers with positive signed32-bit PID range, preventing ctypes PID truncation or boolean misuse. Existing exact-owned process guards remain the caller prerequisite.

Focused tests independently rerun:15/15 (owned debugger6, hardware entry5, guest memory4), including denied/partial reads, task-right release after read exception, and invalid PID values rejected before library access. One bounded parent-authorized launch is acceptable. Post-capture receipt review is recorded below; baseline validation remains with the source producer. `physical_entry_bytes_independently_verified=false` remains correct even when guest virtual bytes succeed.

## Post-capture and next-step recommendation

The sole r246 receipt records successful attach/detach, task_for_pid return5, and no independent read. Failure occurs before breakpoint creation; breakpoint cleanup is empty. Outer capture completed with no owned processes remaining. Guest-virtual proof, physical-memory proof, hardware-entry verification for this attempt, and operand semantics correctly remain false. Debugger process exit0 means a receipt was produced, not that the experiment passed.

Independent raw memory is a separate requested proof obligation, not a prerequisite for every bounded hardware-only observation. r245 already demonstrated hardware breakpoint reporting, resolved location, stop reason/PC, bounded raw register/memory observations and cleanup. A carefully labeled next diagnostic may observe the predeclared r243 caller without asserting independently unmodified guest bytes. It must retain that caveat and remain unadmitted; no pixel gate is weakened by distinguishing an instrumentation confidence limit from renderer parity.

Recommendation: proceed next with one predeclared sampled CALL site (0x1000f28db), exact pinned call instruction verification, hardware-only support checks, bounded ABI inputs, robust cleanup, and an unchanged native sanity baseline. Do not conflate callee-entry stack return with CALL-site state. This advances source ownership more directly than repeated permission probes. Do not call its logical LLDB byte read an independent memory proof.

If the separate guest-read obligation is pursued, a single task_read_for_pid feasibility attempt is narrower than task_for_pid because it requests a read task port; permission success must not be assumed. The installed SDK declares mach_vm_read_overwrite with vm_map_read_t (mach/mach_vm.h:191) and lists SYS_task_read_for_pid539 (sys/syscall.h:579), but exposes no ordinary user-header prototype found here. Confirm the exact exported API/ABI from pinned SDK/runtime evidence before any ctypes call; do not guess an undocumented syscall signature or invoke broad privilege workarounds. No such call was made in this review.

A debugserver raw packet is not automatically independent of software-trap filtering. Its actual server implementation must be pinned and inspected; it remains the same debugger infrastructure and can still normalize breakpoint memory. Do not claim independent physical bytes merely because SBProcess.ReadMemory was bypassed. Neither a guest task read nor debugserver packet proves Rosetta's translated host instructions or physical RAM. Keep those claims false instead of chasing them as unnecessary prerequisites to an explicitly bounded diagnostic.
