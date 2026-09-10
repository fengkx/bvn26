# Hitsugaya base-form acceptance

Bankai and form replacement are explicitly deferred. This record covers the
retained ordinary BVN 2.6 `rifagu` base Sprite 638 against Ichigo, with original
player key reads verified and Godot using the same fixture. Production remains
native Godot; the Flash player is an analysis oracle only.

**Verdict: full acceptance still pending.** The current 167-case matrix has
152 exercised matching cases, 4 matching energy-negative cases and 11 matching
source-missing-label no-ops, with no state differences. All 167 originals are
retained; no native-only result is counted. Bankai remains deferred. Full
visual/audio and additional geometry/browser boundaries below are still open.

## Observed behavior

The matrix has 167 fresh-fight fixtures: 19 neutral commands plus 148 held,
guarded, mirrored, wall, airborne-target, mutual-attack, repeated-dash and energy
threshold variants. Each completed case compares 602 actor observations over
300 fight ticks, including exact coordinates, source frames, action, HP, energy,
invulnerability, contact, hit counts, pause and hurt state. Presentation-enabled
variants additionally compare 301 root X/Y observations exactly.

[helper-registry/matrix/coverage.json](helper-registry/matrix/coverage.json) is the current fixed-input matrix.
The older `matrix/` retains the pre-repair failures.
The earlier matrix-snapshot directory remains a historical progress snapshot.
Originals and old failing native results remain alongside current comparisons.
Native-only rows do not pass.
The original has no aerial-special label; matching no-op cases are distinguished
from an exercised attack. Below-energy negative cases are also marked separately.

## Source-backed repairs

- Root position assignments preserve `=`, `+=`, `-=` and both axes of chained
  writes. The source landing effect and its root movement are compiled.
  [Source gate](root-position-source-first.md) and [red/green evidence](root-position/).
- Grouped guard-switch labels now retain strengths 5, 7, 8, 9 and 10. Ice guard
  previously omitted the shared effect, pause and shake. Its repaired replay
  matches all 602 actor and 301 root-position observations.
  [Source gate](guard-switch-source-first.md) and [red/green evidence](ice-guard/).
- Unqualified `fangyux()` is not rewritten into `_parent.fangyux()`. Native
  Flash reports the former as undefined in the controller scope. This removes
  extra guard retreat without changing impulses or collision bounds. Both
  guard routes and two additional chain/recovery routes match 2,408 actor and
  1,204 root observations. [Source and runtime proof](guard-call-source-first.md).
- The scene wall clamp now runs in its source callback phase. The shared
  receiver compiles the omitted `hitWall`/`hitNear` branch, restoring the
  authored wall-side push instead of allowing extra ice-projectile contacts.
  Long-U matches 602 actor and 301 root observations; the existing PvP,
  training and r13/r14/r15 compared fields remain matched.
  [Source gate and retained failures](wall-source-first.md).
- Authored sound sample ranges and independent static channel envelopes are
  baked into PCM. Effect sound playback belongs to its frame scheduler and
  is no longer duplicated by its visual preview.
  [Source gate](sound-source-first.md); runtime stream length and single-play
  checks pass. Waveform/device-latency identity is not established.

The full [source inventory](source-audit.json) retains scripts, placements,
callbacks, explicit exits and timeline fallthroughs. No hitbox is enlarged and
no character-specific movement or hit rule is added.

## Remaining acceptance boundary

The two former summon failures are repaired using the original global instance
order. Helper frame scripts settle after newer action clips and before older
fighter BODY callbacks. Registering the retained helper roots with the shared
registry fixes air-target pause/landing and held-summon frame timing without
reordering all callbacks. The fresh original trace, red history, 167-case
recomparison, cross-mode checks and matching Web replay hashes are retained in
[helper-registry/README.md](helper-registry/README.md). The earlier global reorder
remains rejected; no input tape or comparison threshold was changed.


The 22 source cancel windows have 88 explicit before/start/end/after obligations;
[69 calibrated root-input cases](helper-registry/cancel-input/coverage.json) now match 41,538
actor and 20,769 root-position observations exactly. These are root-input phase
results; ordinary held-input coverage does not establish all callback edges. Full visual
pixel comparison, audio waveform comparison, browser lifecycle and all geometry
boundaries remain unaccepted. Transformation is outside this request's current
scope. These limitations must remain visible even if every matrix row matches.

Python compiler/harness regressions and focused native tests pass. The existing
legacy `combat_smoke.gd:177` assertion also fails in the unchanged HEAD baseline;
its retained failure is not attributed to these repairs or counted as passing.
See [check records](checks/).
