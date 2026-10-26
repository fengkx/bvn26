# Actual Jinye workload: observed affine callers

The four source-bound profiles passed the producer's baseline gate before this comparison:735980 final pixels match pinned rawRGBA and premultipliedRGBA independently; source3680 pixels and the executable hash also verify. See `profile-baselines.json`. `direct_cached_regenerate` is only a name for requesting cache false→true each draw; actual regeneration is not established.

`actual-source-callers.json.gz` intersects the profiles with167 independently byte-verified direct calls to the pinned generic compose/inverse functions. Counts below are inclusive sample-tree occurrences, not function invocation counts.

| Compose call site | Direct uncached | Cached reuse | Cache invalidation request | Local uncached |
|---|---:|---:|---:|---:|
|0x1000f28db|2|0|1|1|
|0x1000f4e11|1|0|0|0|
|0x1000fad3f|2|1|0|0|
|0x100158203|0|1|0|2|
|0x10015f86b|0|1|0|0|

All five target generic compose `0x10029dad0`. No direct return from generic inverse `0x10029de20` was sampled in these four captures. This does **not** prove that inversion did not execute. The retained old r111 cache profile still observes the already-known inverse-origin store call at0x10015e7a2.

This establishes observed callers in the actual source workload, but no matrix argument values or branch flags. In particular, it does not identify any operand as the authored bitmap fill matrix, prove the specific fixed/float arithmetic branch, or establish the footprint initializer. The generic calls' object+0x48 and cache-field operands remain semantically unclassified. `bitmap_fill_setup_routing_established=false` is unchanged.

Reproduce with the repository probe:

```sh
python3 -m tools.probes.audit_affine_static_callers \
  --binary '/path/to/Flash Player Debugger' \
  --disassembly /path/to/pinned-player-disassembly.asm \
  --profile prior_cached=evidence/importer-loud-fail/r111/cached/sample.txt.gz \
  --profile prior_uncached=evidence/importer-loud-fail/r111/uncached/sample.txt.gz \
  --profile direct_uncached=/path/to/profiles/direct_uncached/sample.txt \
  --profile direct_cached_reuse=/path/to/profiles/direct_cached_reuse/sample.txt \
  --profile direct_cached_regenerate=/path/to/profiles/direct_cached_regenerate/sample.txt \
  --profile local_uncached=/path/to/profiles/local_uncached/sample.txt \
  --output /path/to/actual-source-callers.json
```

The tool validates every reported call instruction against the pinned executable and hashes all input profiles. No native RGB chooses a call site or arithmetic route. No debugger attachment, process injection, renderer change or production advancement was performed by this audit. The separate conditional operand-capture plan is still unexecuted.
