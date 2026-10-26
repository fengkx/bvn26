# Existing binary evidence cannot yet identify Jinye bitmap-fill setup

Read-only inspection used the installed executable with pinned SHA256 `8d4c1f5934adae809b5f4ce4f6ca7c64d4260df46bb3eb9c41fe32be2ee905be` and the pre-existing `/tmp/bvn-r110/player.asm`. Every listed direct-call instruction was checked against bytes in the corresponding Mach-O segment; the disassembly alone was not trusted. `static-callers.json` records167 verified direct call edges:128 to generic compose `0x10029dad0`,39 to generic inverse `0x10029de20`.

Intersecting their return PCs with already-pinned r111 profiles finds six observed call sites:

| Call site | Target | Cached observations | Uncached observations |
|---|---|---:|---:|
|0x1000f28db|compose|0|2|
|0x1000f4e11|compose|0|1|
|0x1000fad3f|compose|1|0|
|0x100158203|compose|2|2|
|0x10015e7a2|inverse|2|0|
|0x10015f86b|compose|1|0|

Counts are inclusive profile-tree occurrences, not invocation counts. Unsampled edges may execute. The previously reported absence of PCs *inside* the generic affine routines is consistent with these sampled *caller return PCs*; they are different observations.

The inverse at0x10015e7a2 lies in the already-pinned cache inverse-translation store, and compose at0x10015f86b reads the same cache object field0x3d8. Other sampled compose sites obtain one operand from an object+0x48 matrix and write a stack temporary; inspected instructions do not identify a raw bitmap-fill matrix operand. Their argument values and branch flags were not captured. None of these observations establishes a compound bitmap-fill setup caller, its input units, or its footprint arithmetic.

The only available sampler-related workload profile is `tools/probes/flash_filters/bitmap-cache-profile.as:5`: identity `beginBitmapFill`, scale7 child, repeated cache invalidation. It is not a Jinye nonidentity raw-fill workload. Existing native factorization/image observations do not retroactively establish binary call routing.

Conclusion: **actual bitmap-fill matrix setup routing remains unestablished from current evidence**. No independently justified new coordinate operation follows from these generic calls. Reusing the generic cache inverse/compose sequence as a Jinye fix would require an unproved route assumption; no renderer change or fitted arithmetic was made.

Reproduce this bounded audit with the adjacent scratch script `audit_static_callers.py`, against the pinned executable/disassembly and repository r111 profiles. No native capture, process attachment, modification, or deployment was performed. `production_admitted=false`.
