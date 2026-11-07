# s349 — AFTER-s344 rank #5: P2 body-push erasure

Base: `17c9dd13de67f0ebc329576143451ceee568cbd0` (s348 #226 squash).
Branch: `feat/s349-body-push-erasure`.
Authority: [unchanged AFTER-s344 rank #5](../next-fix-priority-after-s344.md).
Only rank #5 executes; ranks 1–4 deliveries stay closed, ranks 6+ planning only.
Historical table wording is unchanged; no re-ranking.
`production_admitted=false`; `native_parity_proven=false`; M0-02 pending.

## Result and independent attempt

**Original/candidate invocation, loaded body, defining scope, uninterrupted
this/root/parent generations and activation/coercion erasure remain unproved.**
Zero independent native observations; zero mechanism/product obligations closed.
This is a failed independent entry-route attempt, not qualified body-push proof.

The [debugger-entry probe](probe_debug_route.py) tries a different prerequisite
from s340's blocked ledger: whether the unmodified compile-receipt artifacts
provide existing debugger metadata from which a source-breakpoint entry could
be pursued independently of `s283Value`. It never calls the old instrument/build
adapters, installs a helper, or launches the unqualified candidate.

[Recorded result](debug-route.json):

- Original `game/fighter/yihu.swf` matches the s283 compile receipt SHA-256
  `9f089bd3ee428382d8b99543a7534fb0f271ede09ed264b74847ca7cffcf1ac8`.
  The unchanged SWF parser validates all 49 timelines and finds zero tags of
  types 58, 63 and 64 (EnableDebugger, DebugID and EnableDebugger2).
- Reading exactly `/private/tmp/bvn-s283-qualification-r02/candidate.swf`, the
  recorded candidate path, returns FileNotFoundError. Its expected receipt hash
  remains `02089de774d202446491ce8e0afc58a3e0fcd7ad508dcf463668175d91163eb7`;
  observed candidate hash and debug metadata are null. The receipt and archived
  pcode do not substitute for a loaded candidate body.
- No breakpoint, source-to-loaded-body association, invocation pair or lifetime
  channel was established. No SWF debug flags were patched and no reconstruction
  was attempted. The candidate remains compile-only and unqualified.

These are new **disk/facility observations only**, not header inventory promoted
to invocation proof or erasure progress. Missing tags do not establish that
native debugging is impossible; the missing candidate is local to that exact
path at probe time, not proof that no copy exists elsewhere. Even a usable
source breakpoint would still need independent loaded-body/scope association,
activation identity and uninterrupted generations; stopping once would not
prove lifetime coverage or observer neutrality. This route stops before those
requirements and makes no native debugger capability claim.

Tag semantics are bounded by Adobe's [SWF format specification](https://www.flashrealtime.com/content/dam/Adobe/en/devnet/swf/pdf/swf_file_format_spec_v10.pdf)
(EnableDebugger/EnableDebugger2) and the upstream [tag code definitions](https://github.com/ruffle-rs/ruffle/blob/master/swf/src/tag_code.rs)
(numeric DebugID mapping only). No emulator is used or added to production.
The hypothesis that metadata could provide an entry is an inference, not a
claim that these tags would supply the required generation/activation channel.

## Missing measurements and ordering

[Binding attempt](binding-attempt.json) leaves original/candidate runs, same
input, loaded bodies, invocations, activations, defining scopes and all
scope/this/root/parent generations null. Initialization, scope/member access,
intervening call, first overwrite, return-before-overwrite, structural body end,
dashing read and coercion/branch each retain null event/slot/erasure fields.
Actual dashing value/type, suppression/preload visibility, coercion effects and
external-callsite execution remain unknown. Null does not mean false or zero.

First establish an independent same-input original/candidate invocation pair
with loaded-body, defining-scope and uninterrupted generations. Then observe
initialization-to-overwrite/actual-return values and mutation, exception,
reentrancy, lifetime and scheduling effects, including the actual dashing operand
and coercion. s322's two-Not versus direct-If cut remains old static evidence;
it does not imply Boolean values or harmless coercion. Structural body end is
not a native dispatcher return. Only afterwards qualify helper effects and
natural executed/skipped off/on controls. Neither control was executed here.
No early initialization, receiver exemption, extra hitTest or tick41.

## Reproduction and gates

[Diagnosis](diagnosis.json) replays the **complete locked s340 diagnosis**, which
recursively validates retained body-push tooling and 5,437 historical events.
Replay is retained validation only; no old proof is relabelled as progress.
[Input pins](input-sha256.json) cover every s340 file, its direct inputs, the
authority and route dependencies. [Route pins](route-sha256.json) lock the new
probe/result; diagnosis rechecks original metadata from the original bytes.
Historical candidate absence is not required to persist for portable diagnosis.

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 evidence/sampling-upgrade/s349/diagnose.py --output /tmp/s349.json
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s349 -p 'test_*.py'
PYTHONDONTWRITEBYTECODE=1 python3 evidence/sampling-upgrade/s349/probe_debug_route.py --output /tmp/s349-debug-route.json
python3 tools/verify.py
python3 tools/check_handoff.py
```

Base diagnose exits 0 for package consistency only. Each proof requirement and
the combined invocation exit 1: `--require-invocation-generations`,
`--require-activation-erasure`, `--require-coercion-erasure`,
`--require-helper-effects`, `--require-off-on`, `--require-external-callsite`.
Codes are `S349_<UPPERCASE_FLAG_WITH_UNDERSCORES>_UNPROVED`; invalid evidence fails
separately with `S349_EVIDENCE_INVALID`. No proof override or trace import.
Tests reject invented invocation/generation/erasure, metadata-as-live-identity,
Boolean/harmless assumptions, omitted boundaries and premature controls. They
are evidence custody tests, not synthetic gameplay observations.

[Gates](gates.json) and [project checks](project-checks.json) retain actual
commands, exits, durations and logs, including unchanged s340/s331/s322/s312/
s300/s291/s283 and retained shared suites. No runtime/contract change requires
Godot or contract checks. Green package checks do not establish erasure.

## Source-first, custody and delivery

1. Complete callbacks stay in locked s283 with s273 caller/frame mapping;
   source: `scripts/fighter/yihu.json` → `DefineSprite_638/frame_1/DoAction.as`.
2. Retained Sprite638 depth1 placement is new, not MOVE; no new live lifetime.
3. Explicit returns and structural body end stay distinct from dispatcher return.
4. Tests protect custody and unknowns, not guessed gameplay invariants.
5. No new original/Godot same-input comparison; native parity stays unproved.

Only s349 and minimal STATUS/SAMPLING_UPGRADE/tasks/manifest tracking change.
Prior s254–s348 trees, authority tables, game/, scripts/, runtime, contracts and
shared sampler/threshold/validator remain byte-identical. Zero builds, launches,
attaches, memory reads, helper installations or captures. No other rank executes.
[Scope audit](scope-audit.json), [manifest audit](manifest-audit.json) and
[artifact index](artifact-sha256.json) retain custody. The index excludes itself
and caches. [Timing](session-timing.json) records actual packaging/check wall time,
excluding initial reading/route discovery and subsequent commit/push/PR;
person-days remain unknown. Delivery is Draft PR only: no ready marking or merge.

Validation: **135 tests pass**. Base exit 0; six individual proof flags and
combined invocation exit 1. Route recheck matches the recorded result. Integrity,
handoff and whitespace checks exit 0. Protected diffs are zero.
