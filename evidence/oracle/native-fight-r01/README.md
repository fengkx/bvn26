# M0-02 native fight oracle — live facility blocker r01

Base/dependency: unmerged PR #244, `00504cee9935bd41b0e0e4ebf17aa826721cd530`.
Local branch: `feat/m0-02-native-fight-oracle`. Initial worktree was clean.
This is a live oracle/facility attempt, not another sampling priority rank.
No push, PR creation, external post, ready transition, merge or deployment.

**No reproducible fight oracle was obtained.** M0-02 remains pending, with this
attempt blocked at native UI binding. `production_admitted=false` and
`native_parity_proven=false`. No fixed input tape, post-menu state, random tape,
normalized trace, repeated fight or oracle acceptance is claimed.

## Exact blocker

Computer Use returned `Sky Computer Use native pipe startup failed` for the
global app/browser inventory and exact mounted player selection. Resetting only
the CUA JavaScript kernel did not recover it. Selection was attempted again after
the live launch request, with the same failure. No screenshot, accessibility
state, visible content or input-target binding was returned; zero UI inputs were
sent. [Verbatim tool results](cua-attempts.json) retain all operations/durations.
The overlap with the live process is not independently timestamp-bound.

This is a CUA transport startup failure, distinct from s361's application timeout.
It is not proof that the player failed to draw, did not dispatch, or displayed no
prompt. No trust/permission prompt text was returned; unseen prompt absence is
unknown. No trust was accepted, UI automation fallback installed, security setting
changed, process injection performed or permissions widened. Per-command sandbox
approval was used for the authorized native launch/process inspection only.

The user's last reported weekly remaining budget was 55%, with a requested stop
floor near 20%. A fresh legitimate UI reading was unavailable because the native
pipe could not start. No credential/session files or unofficial usage endpoints
were inspected, no model/settings change was made. Work was bounded to this
live attempt, regression checks and local handoff.

## Actual native attempt

[Attempt 01](attempt-01/session.json) verifies disk custody/configuration and
acquires the shared lock, then fails before launch with the sandbox error:
`[Errno 1] Operation not permitted: 'ps'`.

[Attempt 02](attempt-02/session.json) ran with approved command escalation:

- Player `/Volumes/Flash Player/Flash Player.app`, full executable SHA-256
  `8d4c1f5934adae809b5f4ce4f6ca7c64d4260df46bb3eb9c41fe32be2ee905be`.
- macOS 26.7 / build 25G229; host `arm64`; `arch -x86_64 uname -m` returned
  `x86_64` with exit 0, establishing host translated-execution availability.
  The pinned player's x86_64 identity is retained from reference-environment;
  the player's loaded image/translation state was not independently inspected.
- Existing `~/mm.cfg` exactly equals `tools/probes/mm.cfg`:
  `ErrorReportingEnable=1` and `TraceOutputFileEnable=1`. No configuration writes.
- All 75 locked `game/` files copied to a new temporary directory outside formal
  source, preserving relative paths and filenames. Source and copied bytes match
  every manifest hash before launch and after cleanup. Main SHA-256 remains
  `707fac0ec6bb2af1a3d18dc308dd403cb556a0988144b0f6f10555382287f92d`.
  Instrumentation diff is empty; no frame forcing, menu bypass or injected input.
- `/tmp/bvn-native-flash-capture.lock` held over preparation, launch, sampling and
  cleanup. It was neither deleted nor replaced. A busy lock fails before launch.
- LaunchServices command uses `open -g -n -W -a` with the mounted player and the
  unique temporary `game/main.swf`. Activation is explicitly allowed, not assumed
  prevented by `-g`. Launcher PID 69683; exact executable/movie-command PID 69685
  observed over the bounded 15-second window. This is process metadata, not proof
  of visible game content or loaded movie execution.
- Account-wide flashlog remained 156 bytes with the same hash. The retained
  [append interval](attempt-02/flashlog.delta.log) is **zero bytes**. It is not an
  attributed native fight trace. Silence is not execution/completion evidence.
- Only PID 69685, freshly matched to the unique movie, was terminated. No matching
  process remained. Launcher exit -15 is our cleanup, not a native outcome.
  Other players and their files were not modified. Temporary build remains
  available at the exact receipt path; it is not committed.

## Acceptance and next live step

M0-02 acceptance requires fixed initial state/input reproducibility, capture
provenance, instrumentation diff and resource hashes. The hashes and empty diff
are available; actual post-menu fight state, input/frame association, random
consumption, trace and a second same-input run are absent. No acceptance criterion
is discharged by the empty flashlog or metadata.

The intended next case is ordinary Vs Human, Naruto base versus Ichigo base on
现世, AI off, natural intro and natural initial stance. These are **proposed
choices**, not observed settings. Helpers, HP/energy/positions/facing, mode ID,
clock phase, rendering scale and random state must be observed and pinned before
capturing the fight. Do not write guessed coordinates or an invented seed.
Use real original-menu inputs; never AS function calls as user input.

Restore the native CUA pipe in the host application, then obtain screenshot/AX
state for the receipt-matching launched instance and bind actual input to it.
Relay any trust or approval prompt verbatim to the coordinator. Qualify the
observation/recording route, pin physical inputs to observed native consumption
and record random draws (or demonstrate their irrelevance) before two independent
runs. Preserve raw logs and session receipts, derive a contract-correct replay
and trace only from actual observations, then independently check acceptance.
No CUA/service restart or permission bypass is attempted here.

The existing replay, trace and match-input contracts were read unchanged. The
facility session JSON deliberately does not masquerade as `replay`, `trace`, or
`match-input`: their required initial state/random/phase/input fields are missing.
No schema or validator change is necessary to report this blocked attempt.

## Reproduction and checks

Portable safety regressions (fixture input, no native launch):

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3.11 -m unittest discover -s evidence/oracle/native-fight-r01 -p 'test_*.py'
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3.11 -m unittest tools.tests.test_capture_serialization tools.tests.test_capture_runtime_fighter
python3 tools/verify.py
python3 tools/check_handoff.py
```

The bounded collector is specific to this known unqualified boot attempt. It
always returns exit 1 and cannot certify an oracle. To reproduce the boot check
on this Mac, choose a fresh output path, obtain any required sandbox approval and
explicitly allow activation:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 evidence/oracle/native-fight-r01/capture_boot.py --output /tmp/oracle-boot-fresh-receipt --allow-window-activation
```

Do not overwrite historical receipts. No native fixture is launched by tests.
[Checks](checks.json) record actual commands, exits and durations. The locked
shared capture tooling stays unchanged. [Read basis](read-basis-sha256.json)
records hashes as read before tracking updates, relative to the base commit;
it is not a claim that subsequently edited docs retain their old hashes.
[Scope/hash index](artifact-sha256.json) covers this local package; the scope
receipt verifies all historical s254–s366, priority tables, original assets,
scripts, contracts, shared tools and Godot runtime have zero diff.

Source-first: no mechanism implementation; no new per-frame, placement/lifetime
or label-exit semantics claimed; tests cover hash custody/log append/lock refusal,
not guessed gameplay; original same-input fight comparison is absent. M0-03,
implementation acceptance, HIT_RECEIVE SOP E, AT matrix and M4 remain downstream.

Validation environment: default `python3` is 3.9.6. The first retained test run
failed at the unchanged `Exception.add_note` cleanup path (requires Python 3.11+).
[Initial failure](initial-python39/retained-capture-tests.txt) and all initial
check receipts are retained. Rechecked with existing Python 3.11.15; no shared
code, assertions or thresholds changed. The native boot itself ran under 3.9.6.
