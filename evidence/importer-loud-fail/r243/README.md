# r243 — Actual Jinye source-bound caller sampling

Four workloads retain the unchanged r242 raw JPEG55 and shape56 source tags, first-placement matrices, authored fill/mask and camera. They repeatedly draw into an existing target for at least eight seconds; only the final image is traced. No native reference bytes are uploaded as source textures.

| Workload | Operation | Final raw and premultiplied pixels exact against r242 |
|---|---|---:|
| `direct_uncached` | Original minified parent draw, cache false | 240000/240000 |
| `direct_cached_reuse` | Same draw, cache true throughout | 240000/240000 |
| `direct_cached_regenerate` | Requests cache false→true before each draw | 240000/240000 |
| `local_uncached` | Explicit pre-outer child raster, source-derived origin/extent | 15980/15980 |

Source readbacks are 14720/14720 exact across four workloads. Final raw RGBA and premultiplied RGBA are independently 735980/735980 exact. Matrix/bounds/property readbacks, event order, source provenance, pinned executable hash and owned-process identity all pass. Each three-second process sample completed successfully. The toggle workload name does **not** prove cache regeneration or allocation. Explicit local materialization does not establish native cache equivalence.

The static audit verifies 167 direct call instructions against the pinned executable. Five generic composition call sites occur in the actual-source profiles; no generic inverse return was observed. This identifies sampled callers only, not authored fill operands, arithmetic branches, initialization rules, or nonexecution of unsampled functions. See `actual-source-routing.md` and `actual-source-callers.json.gz`. Counts are inclusive sample-tree occurrences, not invocation counts.

The first unsampled attempt failed strict ownership matching because `/tmp` and canonical `/private/tmp` differed. Its completed capture and reason are retained under `unsampled-attempt/`; no caller claim uses it. `profile()` now canonicalizes its public arguments before the unchanged exact ownership check, covered by a regression test. A fresh run ID was used for the accepted capture.

## Reproduction

Run from the repository root, using the same pinned FFDEC and native Flash Player Debugger 32 described in the reference environment. Native captures may activate a player window and must be serialized.

```sh
python3 -m tools.probes.build_jinye_profile --output /tmp/r243/native/direct_uncached --ffdec /path/to/ffdec-cli.jar --workload direct_uncached
python3 -m tools.probes.profile_native_cache --build /tmp/r243/native/direct_uncached --output /tmp/r243/profiles/direct_uncached --player-app '/path/to/Flash Player.app' --allow-window-activation
```

Repeat the build/profile pair for the other three table workload names. Then:

```sh
python3 -m tools.probes.analyze_jinye_profile --root /tmp/r243 --output /tmp/r243/profile-baselines.json
python3 -m unittest tools.tests.test_jinye_profile tools.tests.test_affine_static_callers
```

Tests: **7/7**. Independent re-decoding reproduced every baseline count; see `review.json` and `review-profile-reproduced.json`. Archived logs can be independently decoded against the retained original SWFs using:

```sh
python3 -m tools.probes.analyze_jinye_profile --root evidence/importer-loud-fail/r243 --built-native-root /tmp/bvn-r243/native --output /tmp/r243-archive-reproduced.json
```

This option requires every retained build receipt to equal the archived receipt and every SWF byte hash to match; it never skips the movie check. The archive intentionally omits SWFs and cannot alone prove their bytes. A fresh build receives a fresh run ID, so future reproduction must build and capture all four workloads anew using the commands above, rather than substitute fresh SWFs for an archived capture.

The caller-audit command is in `actual-source-routing.md`; archived sample and JSON files are gzip-compressed with timestamp zero. Built SWFs and downloaded tools are not archived.

## Acceptance and next discriminator

No renderer arithmetic changed. All admission flags remain false. The r242 one-pixel local mismatch, minified Jinye image failures, historical component count, full AS ownership gate and other prior blockers remain unchanged. No full runtime acceptance was rerun because this round modifies diagnostic tooling only.

The next bounded discriminator is **owned-process operand-capture feasibility** at one profile-observed generic composition site, not another formula sweep. First establish that the debugger can attach to the exact newly owned, run-ID-pinned probe and expose Rosetta x86 argument registers; detach reliably and retain any denial. Only if that works may a separately bounded, verified hardware execution breakpoint capture the minimal matrix operands and caller context. Identify source-fill setup through independently recorded source matrices and operand bytes, never observed RGB. No security-setting changes, re-signing, software-breakpoint substitution, or attachment to unrelated players. See `operand-capture-plan.md`. This round performed no debugger attachment, and static LLDB target loading is not proof that attachment is permitted.
