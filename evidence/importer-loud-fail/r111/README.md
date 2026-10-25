# r111 — sampled cache workload narrows the static caller

A dedicated native harness performs60000 cache invalidation/draw iterations. An otherwise identical uncached control keeps cacheAsBitmap false; final property readbacks verify both modes. The profiler waits for the run-specific start marker and samples only the player process owned by that exact movie path, using the existing serialized capture/cleanup tool. Both captures complete. No debugger writes, process injection or production changes occur.

The aligned cache profile contains return PCs0x1000f5005,0x10015d5a5,0x10015c4e3 and0x10015d149, with inclusive sample-tree occurrences519/482/73/361. The uncached profile does not report these PCs. The pinned static five-byte call instructions connect the first two to0x10015d560 and **0x10015c080**, respectively; the latter two return from0x100157cb0 and0x10020ee10. This gives a concrete cache-workload caller to inspect instead of guessing a generic inverse/recompose pair.

These counts are **not invocation counts or statistical performance conclusions**. Unsampled does not mean unexecuted. Neither profile directly observes the generic affine branch inspected in r110; no specific normalization arithmetic/branch is verified. The macOS sample report labels the translated task ARM64 and leaves many Rosetta frames unknown; the installed x86_64 executable hash and reported module-relative return offsets are retained, and the four matching call instructions are checked independently.

An initial sample started before the probe marker; it is retained under `initial-startup-window/` but superseded for the comparison by the aligned cached/uncached reports. Profiling outputs are not pixel references. Old native image gates remain unchanged.

## Reproduce

```sh
python3 tools/probes/build_flash_filter_probe.py --case bitmap-cache-profile --output /tmp/cache-profile --ffdec /path/to/ffdec-cli.jar
python3 -m tools.probes.profile_native_cache --build /tmp/cache-profile --output /tmp/cache-profile-report --player-app '/path/to/Flash Player.app' --allow-window-activation
# Repeat with bitmap-no-cache-profile and a separate output folder.
python3 -m tools.probes.analyze_native_cache_profile --evidence evidence/importer-loud-fail/r111 --output /tmp/cache-profile-analysis.json --binary '/path/to/Flash Player Debugger'
python3 -m unittest tools.tests.test_native_cache_profile
```

[Analysis](analysis.json), [static call edges](static-edges.json), compressed complete sample reports and original trace events under `cached/` and `uncached/`, [provenance](provenance.json), [acceptance](acceptance.json).

Next discriminator: trace the bounds/matrix setup reaching0x10015c080, especially the stored affine fields used before buffer allocation and drawing. Pin the relevant instruction spans and conversion constants independently of RGB. A call graph narrows the search but cannot establish branch values; any derived common construction must still clear r101–r109 and all prior exact sampler controls before GPU binding. Do not infer a route from sampling absence or select constants from pixel agreement.

`specific_normalization_branch_verified=false`, `candidate_admitted=false`, `production_admitted=false`. Components historical9/54; source cache normalization, general affine/coverage and full AS/clip-action ownership remain open. Draft only; no merge/deploy/Worker.
