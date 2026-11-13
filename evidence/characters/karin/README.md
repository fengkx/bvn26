# Karin / 香磷 base-form port

Base: `b905eb5f9441c94bf3c75d87e6c8d8fa73ed0563`, branch `feat/karin`.
Targeted native parity and production rollback pass; final repository gates and
saved-roster replay are tracked in `checks.json`.
Coverage remains partial. No merge or deployment.

## Source-first answers

1. Locked `game/fighter/karin.swf` (SHA-256
   `995ea7a1b6aceef2572f0854020d9ddf9462e902a10257344d338c0b6fc0b5c8`)
   and `scripts/fighter/karin.json` define Sprite 427, 1,412 frames.
   `source-first.json` indexes every root frame, including empty frames,
   scripts and display-list changes. Frames 654 and 908 each have two
   DoAction tags: flash first, then `followMc`. The second tag must not be
   discarded merely because the first script exists.
2. New PlaceObject instances own their `played`, `movspeed` and `atm_name`;
   MOVE retains them. Sprite 173 is placed independently at 448/451/454.
   Its callbacks start after placement and test the authored hitmc against
   body and projectile targets. Frame 454 changes `atm_name` on contact.
   Frame 654 follows the opponent in X/Y; frame 908 follows X only, with
   the authored front-only constraint. Neither is a guaranteed hit.
3. Normal exits are 225/253/289/317; low attack warps and reverses display
   facing at 348, then enters 砍2 at 362. Upper attack falls through into
   砍技21 and returns at 427. Super start/end pairs are 607/650, 697/745,
   848/906. Upper-super continuation loops at 780 back to 上必杀2 (756),
   with a `doAllAction()` callback placed at 771 providing input exits.
   Healing at each of 763–768 is `if(hp < 1000) { hp += 5; }`; it does
   not clamp the result or substitute configured max HP. Ultimate returns
   at 980. Label boundaries alone do not end actions.
4. Tests lock the shared Sprite 2 receiver, source super frames, default
   helper and the six conditional healing writes. HIT_RECEIVE step A
   passes all five tests covering 35 fighters and 26 assists. Before traces
   retain missing healing and early projectile contact; after traces match.
   Frame-1 projectile declarations and frame-5 variable renames are compiled
   separately, with a token boundary preventing `atm_name` from becoming an
   accidental `_name` assignment.
5. Seventeen complete native Flash captures match 12,274 actor states on
   14 exact fields, with both slots and every tick 0–360 aligned. Captures use
   the pinned native Flash debugger only through
   `flash_lock.py run --holder bvn-karin`. Diagnostic
   injected inputs are explicitly distinct from OS-input or initialization
   admission. Health-precondition cases require separate probe builds,
   because that precondition is embedded in the current capture harness.

## Selection and scope

The source manifest has no Karin `fzurl`; default `fz` is 鼬, already
imported as `you`. No helper port is added. Local and online catalogs,
source portraits/footer and natural opening include the base form only.

The comparison contract is all 14 actor fields (frame, x, y, xscale, action,
hp, ql, sw, touch, touchFloor, hits, paused, hstm, hurtSkling), with both slots
and every tick. Passing fixtures establish only their observed scope.
Full audiovisual, browser, AI and exhaustive boundary acceptance remains
pending. G0, weak-machine, two-machine, TURN and Internet acceptance is not
claimed. All six admission/initialization flags remain false.

PR #37 protected interrupted-super recovery must remain unchanged; no new
intentional gameplay difference is authorized.

## Toolchain

- Godot: `/Users/fengkx/me/agent-code/toolchains/godot-4.7.2/Godot.app/Contents/MacOS/Godot`
- JPEXS: `/Users/fengkx/me/agent-code/toolchains/jpexs-26.2.1/ffdec-cli.jar`
- JPEXS SHA-256: `23c1e70ff2b08388e35de10afd97a2875386cbfdc2ef99c8176d40b4f8a3ada9`
- Python for modern importer scripts: `/opt/homebrew/bin/python3` (3.14).
  System `python3` is 3.9 and cannot evaluate the hurt-voice tool's union
  annotations; switching interpreter did not change project dependencies.

## Observed behavior and residual coverage

- Ordinary combo: 190 damage, maximum four hits. Normal/super guard chips
  2/23 HP with zero hits; incoming guard then low attack leaves Karin at 916 HP.
- Super: 230 damage / one hit. Ultimate: 450 damage / three hits. Dash-to-super
  input reaches its source cancel; it is not exhaustive cancel-edge coverage.
- Upper super heals 900 to 1000 and 998 to 1003, preserving the source's
  pre-addition comparison. Its continuation is still looping at tick 360.
- Mixed ranged input reaches root frames 444/499/549 at ticks 11/133/251.
  Only the ordinary ranged cast hits at these positions (150 damage / three
  hits); low/upper ranged and the separate air-ranged fixture whiff.
- Repeated ranged uses the authored low-attack warp between three casts,
  observing right/left/right facing and independent child locals. The separate
  repeat-warp fixture also preserves changed target positions and both facings.
- `interrupt` and `prepare-interrupt` are attempted counterattacks: Karin
  takes no damage and finishes the super. They are not interruption coverage.
  PR #37's actual direct/queued recovery smoke remains separately protected.

Five Godot checks cover production rollback through natural opening,
ultimate pause/replay, delayed guard inputs, round reset, healing overflow,
projectile local-state replay and three casts across both facings, plus the
shared protected recovery/input/visual controllers. Shared PvP and training
references match 602 states each. Focused Python checks: 86 passed; shared
receiver chain: five passed. Matchmaking typecheck and 32 tests pass (the
sandbox-restricted Wrangler test was rerun successfully through escalation).
Six contract schemas and six examples pass; this does not prove gameplay.

`comparisons.json` binds fixtures, decompressed source/native hashes, observed
results and complete alignment. `source-builds/` retains build configuration,
instrumentation diffs, native capture environments, raw logs, input strings,
random tapes, clock tapes and post-done tails. Diagnostic `built_not_run`
metadata is not rewritten: adjacent capture records establish execution.
`diagnostics/` retains the initial timeout, source-test failures, original
native failures, invalid visual attempt and unsuccessful coverage calibrations.
A wall-clock timeout capture is not substituted for a passing reference.

## Compiler impact

`combat-compiler-impact.json`: all 26 decoded combat models have equal numeric
values; 22 serialized outputs are unchanged. didala, itachi, juggo and yihu
serialize integral `movspeed` literals as integers instead of floats. Exact
paths and before/after hashes are retained; this is not byte identity. `compiler-impact.json`: supplementary DoAction processing
changes future context compilation for didala, gaara, juggo, lanran, renji and
yijiao. Those generated packages and their reviewed obligations are not
rewritten. This is not a claim that all compiler outputs are unchanged, or
that actor-state replay validates old audiovisual omissions.

`roster-index.json` pins 216 saved prior-role fixtures and original traces;
`replay_saved_roster.py` runs their exact comparisons without launching Flash.
Final execution and repository-gate results are recorded in `checks.json`.
No person-days are inferred from process timings.

## Reproduce

Use the pinned tool paths above. Import new PNG resources with the pinned
Godot editor before rendering selection screenshots. Run `tools/test_move_cases.py`
against `cases/` (the direct batch command may be used when the host requires
more wall-clock time; no logical ticks or acceptance fields are removed).
The source capture harness must always be wrapped by the shared Flash lock;
health preconditions need their own retained probe builds. The repeat-ranged
fixture uses the standard dynamic probe. Keep incomplete and completed but
non-comparable captures distinct from accepted comparisons.

Full audiovisual, browser, AI, all energy/boundary combinations and Internet
acceptance remain pending. The screenshot checks use native rendering, not
Flash pixel comparison. No production deployment or admission is authorized.

The online compatibility manifest must change with the roster. Its retained
base snapshot was already stale for 16 runtime entries and two font entries;
local import metadata also differs. `online-manifest-impact.json` separates
those from this port's four runtime and five existing content-file changes.
No cleanup of old `.import`/`.uid` fingerprints or prior fighter packages was
performed. The regenerated manifest records the actual local build inputs.
