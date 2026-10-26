# r245 — Verified hardware entry, still unclassified operands

One fresh 60-second actual Jinye source workload exercised a hardware-only breakpoint at the pinned generic composition entry. The exact new stop ID, breakpoint/location pair and entry PC were verified. The debugger read only 28 bytes from each input pointer, the stack return address and argument register addresses. The created breakpoint was removed, debugger detached and native capture completed with no owned process remaining.

The observed direct caller `0x1005e8dd6` was **not** one of the r243 source-profile sampled edges. This is a generic-function feasibility result, not identification of the authored bitmap-fill setup. The captured structs remain unclassified. ABI field extent and direct call bytes were independently checked against the pinned executable; see `hardware-conclusion.md`, `debugger/static-callers.json.gz`, the r243 static-caller audit and `tools/probes/extract_cache_affine_binary.py`.

LLDB's entry readback matched the pinned prefix, but `SBProcess.ReadMemory` can mask software-breakpoint trap bytes. It therefore does **not** independently establish the physical target entry bytes. `physical_entry_bytes_independently_verified=false` remains explicit. No software fallback, target memory write, expression evaluation, signing or security change was requested.

The instrumented capture retains original JPEG55/shape56 tags, fill/mask and r242 matrices. Strict fixture/harness/SWF/raw-tag checks pass. Source pixels **3680/3680**, final raw RGBA **240000/240000**, and final premultiplied RGBA **240000/240000** match r242. These are instrumentation sanity checks, never replacement references. Tests: **11/11**.

## Reproduction

Use the pinned native debugger and FFDEC, with serialized captures. Build fresh run IDs and fresh output directories; do not reuse archived run IDs.

```sh
python3 -m tools.probes.build_jinye_debugger_profile --output /tmp/r245/native --ffdec /path/to/ffdec-cli.jar --duration-ms 60000
python3 -m tools.probes.probe_owned_hardware_entry --build /tmp/r245/native --output /tmp/r245/debugger --player-app '/path/to/Flash Player.app' --disassembly /path/to/pinned-player.asm --allow-window-activation
python3 -m tools.probes.check_jinye_debugger_baseline --native /tmp/r245/native --output /tmp/r245/baseline.json
python3 -m unittest tools.tests.test_owned_hardware_entry tools.tests.test_owned_debugger_probe
```

The baseline checker requires retained original build bytes and verifies their receipt/hash; the archive omits SWFs and cannot alone establish omitted bytes. Full native logs and the caller audit are compressed with timestamp zero. Source fixtures, build/environment receipts, generated debugger script, transcripts and independent review are retained.

## Next discriminator and acceptance

First test a permitted read-only task-memory interface to verify raw entry bytes independently of LLDB's masked view. Only then narrow a bounded hardware stop to a byte-verified, independently profile-observed caller; retain exact caller/entry evidence and the already established minimal operand read bounds. Source-fill ownership must follow from independent matrix provenance, not whichever operand reproduces output pixels.

No arithmetic or runtime change, no reference rewrite, no production admission. The Jinye sampling mismatch and separate full AS ownership gate remain open. Candidate/GPU/production flags remain false.
