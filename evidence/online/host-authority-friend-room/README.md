# Default host-authoritative friend rooms

The requested scope is friend rooms: create/share/join, independent fighter and
helper selection, host map/rule confirmation, readiness, explicit start, result
settlement and another match in the same room. Automatic stranger matching is
out of scope. The branch incorporates master df36e43f5 and retains the existing
receiver-credit fix d0774b41c.

New rooms already default to host-authoritative on the integrated master. This
continuation removes experimental product labels and the legacy fixed-map and
readiness shortcuts. Unconfirmed maps remain unconfirmed in the room summary.

## Runtime corrections

- Register shipped `generated/forms` resources. Before the fix, the real Golden
  Naruto replacement was rejected as an unregistered display resource.
- Project `wrapper_clips` independently of BODY clips. The retained Kenshin
  replacement test exposed a wrapper texture mismatch after resource registration;
  these are compiled siblings outside `mc`, with their own retained clocks.
- Bind and validate both clip trees before replacing the guest display. Missing
  wrapper playheads are rejected without replacing the last valid display.
- Retain the highest serial in a receive drain, including when a lower serial
  arrives after the newest packet on the unordered channel.
- Display schema is v2, bound into the initial-state hash. Packet, decompression,
  clip, resource and plain-value limits are unchanged. No geometry is transmitted.

## Source-first scope

1. Gameplay frame scripts remain on the existing host Battle/source controller.
   Replacement edges are the retained `minrenx`, `ichigo`, `kenshin`, and `weqal`
   form lifecycle cases (1294; 886; 1148/1503; 1148 respectively).
2. PlaceObject identities come from the compiled `timeline.json` BODY and
   `wrapper_siblings` placements. The guest binds depth/symbol/placed-frame to
   local definitions; it does not inherit or synthesize instance variables.
3. No goto/stop/fallthrough behavior changes. The guest applies host playheads
   and never executes frame scripts or independently advances the fight.
4. Invariants are identical host/guest render trees, wrapper clocks, bounded
   validation and guest simulation tick zero. Tests do not invent fighter rules.
5. This is native host/guest comparison, not a new Flash behavior certification.
   Existing character source captures remain unchanged; full original parity and
   all existing proof/admission flags are unchanged.

## Validation and raw evidence

`validation.json` records the executed checks, build identity and limitations.
`roster.json` retains the 34 fighter fixture selections; the rotating matrix also
covers all five selectable helpers and all ten maps, at 330 ticks each with two
out of three snapshots skipped. This is a fixed-input projection matrix, not an
exhaustive move or performance benchmark.

Five actual production form replacements compare host/guest render structures.
The two-peer test selects each authority slot in turn, uses a non-default
Sasuke/Hitsugaya matchup on Konoha, and covers lost initial state, receiver credit,
unordered arrival, same-connection safety recovery, source KO and result receipt.
The real local Worker tests additionally prepare/start a second epoch in the same
room with a newly selected host, then abort back to the room with lineups retained.

The dedicated WebRTC export runs the real room UI callbacks against a local
Worker in two isolated Chromium instances. It selects Sasuke/Itachi assist versus
Hitsugaya/Kon on Konoha, prepares and starts explicitly. CDP keyboard input is
observed at the host and returns as guest position movement. The successful run
retains three open channels, selected ICE pairs, zero guest simulation, and no
browser console errors. This uses the documented local ICE permission override;
it is not an Internet/TURN or two-physical-machine acceptance.

The first browser run is retained as failed: input and WebRTC worked, but 148
received states at the old 240-tick stop did not satisfy the existing 180-state
coverage gate. The fixture was extended to 480 ticks; thresholds were unchanged.
The successful run has 479 host ticks and 277 received guest states.

Initial test failures are retained: a GDScript type-name collision, missing forms,
missing wrapper playheads, and canvas transform notifications not yet settled at
comparison time. The renderer comparison now flushes the same CanvasItem
transform notifications that precede drawing; no numeric tolerance was added.
Three exit-time audio retirement diagnostics have separate clean reruns after
using the repository audio shutdown drain. Sandbox-denied local TCP tests were
rerun with local network permission. Raw logs are compressed without normalization.

## Production artifact and remaining external check

`dist/web/` uses the production `render_surface.tscn` entry. A frozen APFS clone
was used to fit the local disk budget, followed by the repository import checker,
manifest generator/checker, metadata prepare/finalize and Web exporter. This is
not represented as an invocation of the entire `build_web.sh` wrapper. Embedded
metadata retains the dirty snapshot provenance. The dedicated WebRTC fixture
export is separate and is never deployed as the production entry.

Automatic approval review rejected creating a diagnostic room and requesting
TURN credentials from `https://bvn26-pvp.fengkx.top` without explicit approval for
that production service. No production room or credential request was made.
Deployment, production TURN, real cross-network and weak-machine performance
remain unverified; the local loopback test does not certify those conditions.

## Reproduction

Run `tools/test_online_lobby_ui.py`, the three `authority_*` foundation/probe/pair
runners, `authority_form_projection_smoke.gd`, and
`python3 tools/test_authority_roster.py --godot /path/to/Godot --output /tmp/authority-roster`.
Run `npm test` in `services/matchmaking`, and the browser runner documented in
`docs/HOST_AUTHORITY_EXPERIMENT.md` using isolated local test browsers.
