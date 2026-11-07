# s330 — AFTER-s326 rank #4: Loader consumed-byte binding prerequisite

Base: `24f0c16b` (s329 #207). Branch: `feat/s330-loader-attestation`.
Authority: [unchanged AFTER-s326 rank #4](../next-fix-priority-after-s326.md).
Ranks 1–3 deliveries stay closed; ranks 5+ remain planning only. No re-ranking.
`production_admitted=false`; `native_parity_proven=false`; M0-02 pending.

## Result and limits

The requested live binding remains **unproved**. This package delivers a bounded
assessment of retained observation adapters, not successful Loader attestation.
[Diagnosis](diagnosis.json) records exact source and line spans for three functions:

- `debugger_script` reads selected frame-zero CPU registers and detaches. It has
  no request resolver, call/return range capture or pre-inline-advance target join.
- `_verify_runtime_fighter` verifies disk bytes at the configured fighter path.
  Those bytes are not independently observed returned or consumed bytes.
- s321 `extract_native.main` extracts and disassembles disk bytes. Its candidate
  call is not an executed consumer. Inspection here is not a new binary audit.

These functions were read, not invoked. This finding is limited to their current
interfaces; it does not prove that a suitable native facility cannot be built.
There are zero new independent native observations. Every executed caller,
P1 consumer, immutable generation, returned/consumed range, pre-advance target,
initialization/lifetime and observer-effect field remains null. No normal load
was qualified, so the wrong-resource control was not executed.

Every s321 file is pinned and its complete diagnosis replayed, recursively
checking historical Loader evidence. This is retained validation, not new proof.
In particular, the local at rbp-0x29 is initialized to zero before the static call
at 0x100108f68; the later byte load cannot distinguish a write from preserved
initialization. The mutable stream slot cannot identify a request generation.
No receipt is resealed, and no imported symbol, static candidate or artifact hash
is promoted to execution or returned-byte provenance.

## Remaining discriminator

Before normal can qualify, independently derive an executed caller/consumer and
immutable P1 request generation; join read return status, actual returned ranges
and consumed subranges (including partial/failed-read behavior) to that same
request. Observe the target before `loadStep++` invokes the next load inline;
retain same-request initialization/use/unload/replacement and qualify observer
effects. A breakpoint hit or pointer alone is insufficient. Only after normal
qualifies may Yihu-for-Yijiao run with expected Yijiao identity unchanged and
actual error/range evidence. No such experiment was performed in this slice.

## Gates and reproduction

With `PYTHONPATH=.`, run:

```sh
python3 evidence/sampling-upgrade/s330/diagnose.py --output /tmp/s330.json
python3 -m unittest discover -s evidence/sampling-upgrade/s330 -p 'test_*.py'
python3 tools/verify.py
python3 tools/check_handoff.py
```

Base diagnose exits 0 for package consistency only. Each requirement exits 1:
`--require-consumer-request`, `--require-returned-consumed-ranges`,
`--require-pre-advance-target`, `--require-loader-attestation`, and
`--require-wrong-resource-control`. Invalid pinned evidence fails separately with
`S330_EVIDENCE_INVALID`; there is no proof/trace override.
Actual commands, exits and costs are in [gates](gates.json) and
[project checks](project-checks.json). Tests check unknowns, modified input/prior
rejection and each CLI proof flag; s321 and retained Loader/shared tests rerun.
No runtime or contract changes: Godot/contract checks are not applicable.

## Source-first and custody

1. Locked `scripts/main.json` → `DefineSprite_1900/frame_1/DoAction.as`
   remains the shared P1/P2/assist/sound Loader source; no new script behavior.
2. No new PlaceObject/MOVE or native generation/lifetime observation exists.
3. `LO.onLoadComplete(target)` ignores target and advances the next load inline;
   a later mutable slot cannot recover the earlier target association.
4. Tests enforce provenance and unknowns, not guessed successful reads.
5. No new original/Godot same-input comparison; parity remains unproved.

Zero builds, launches, attaches, live memory reads, captures or product obligations
closed. Only s330 plus minimal STATUS/SAMPLING_UPGRADE/tasks/manifest tracking
changes. All s254–s329 trees, authority table, game/scripts, runtime, contracts and
shared tools remain unchanged. Scope, manifest and artifact hashes are recorded
separately; the artifact index excludes itself and caches. Measured packaging
interval excludes initial reading/design and later commit/push/PR; person-days
are unknown. Draft only; no ready marking, merge, rollout or deployment.
