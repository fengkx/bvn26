# Online lobby menu — local implementation evidence

Base: `b905eb5f9441c94bf3c75d87e6c8d8fa73ed0563` (`origin/master`).
Branch: `feat/online-lobby-menu`. User review: 2026-11-13, t310u.

The approved sidecar design supplies the warm black, bone white, vermilion and
blue identity direction. Its character/helper mockups are explicitly excluded:
both players navigate to the existing `CharacterSelection` view, independently
confirm a fighter and helper, then return to the room. Offline selection remains
unchanged. The roster is taken from the current game catalog, not the older
13-fighter design snapshot.

## Implemented path

- Create with nickname; new rooms default to host-authoritative with no choices
  and an unconfirmed map. Join by code or `?invite=` link; remember nickname.
- Invite code remains selectable; copy shares a link in Web and code on native.
  Host can select before a guest arrives. Guest departure retains host choices,
  clears readiness, and renews the service's consumed invitation automatically.
- Host alone confirms map and rules. Guest waits for confirmation. Ready locks
  the local lineup; cancel unlocks it. Map/rules changes clear both readies.
- Both ready enables an explicit host Start; there is no automatic prepare.
- Room settings contain time/life and mode. Mode locks while occupied; rollback
  alone exposes delay/prediction and a recommended-default reset.
- Player menus omit endpoint, LAN opt-in, internal connection status and invite
  rotation controls. Existing development APIs and legacy room handshake remain.
- Host leave confirms room closure; guest sees room-ended and returns to entry.
  Existing loading cancellation/abort keeps committed setup for retry.
- Worker accepts the catalog roster/map for host authority; guest display resource
  registration covers fighters/helpers instead of four fixed directories.

This changes online orchestration and presentation, not Flash gameplay mechanics.
The source-first five-question gate remains applicable to future combat changes;
no fighter runtime, attack compiler, source inputs, tapes or parity threshold was
changed. No Flash parity or milestone completion is claimed.

## Validation

- Godot 4.7.2 native `online_menu_flow_smoke.gd`: passed independent host/guest
  selection, empty-host commit, map commit/gate, ready lock, explicit start,
  guest permissions, invite-link parsing and expanded projection resources.
- Existing `tools/test_online_lobby_ui.py`: all ten scripts passed, including
  legacy peer selection/map barriers, exact retries and room-client validation.
- `authority_projection_smoke.gd -- --selected-roster`: passed 330 simulation
  frames with Sasuke/Itachi-helper vs Hitsugaya/Kon on Rukongai; 220 display
  packets intentionally dropped; maximum encoded packet 16,093 bytes; guest
  simulation ticks stayed zero. This is a bounded projection test, not a network
  or full-roster capacity claim.
- `authority_pair_smoke.gd`: passed both authority slots, 660 frames, startup
  recovery, bounded state credit, pause/resume and terminal receipt; guest ticks
  stayed zero.
- Local Worker TypeScript and test suite: 32/32 passed, including non-fixed
  authority setup, map readiness gate, owner-only map, occupied mode lock,
  lineup lock, explicit prepare, authority agreement and result receipts.
- Local Wrangler configuration WebSocket test passed with its registry redirected
  to `/private/tmp`; no cloud deployment was invoked.
- Input integrity and handoff checks passed. Contract validation passed (6 schemas/6 examples); fingerprints are regenerated
  from the final tree before PR creation. All 25,223 recorded input hashes were
  independently checked against disk with zero mismatches. The existing generator
  remains unchanged, including its treatment of Godot import sidecars.

First native import produced only a sandbox editor-preferences write warning;
initial premature selection testing was rerun after asset import. Native smoke
logs can include denied writes to the default user log directory; final direct
checks use `/private/tmp` logs. Early test failures and layout capture fixes were
resolved rather than changing gameplay thresholds or saved baseline output.

Measured implementation/validation time at the packaging checkpoint: 1,522 seconds.
No person-day estimate or milestone completion is inferred.

## Native visual review

[Room](room.png), [settings](settings.png), and [host map picker](map.png) were
rendered by Godot on the native 600x400 canvas at 900x600 and visually inspected.
Character artwork is cropped to its alpha bounds; original selection artwork
and behavior remain unchanged.

## Remaining boundaries

G0, weak-machine performance, actual two-machine play, TURN, Internet and default
ICE remain unverified; admission/proof flags are unchanged. No production Worker
or Vercel changes, deployment or merge. New clients and Worker must be shipped
with matching generated fingerprints in a future separately authorized release.
The new menu path is selected by the server's `mapConfirmed` field; older room
states retain the legacy handshake until expiration. Native layout review does
not establish full Web clipboard, cross-browser or end-to-end human acceptance.

The display packet cap stays unchanged. Additional roster combinations and heavy
special-move scenes may exceed it and must fail closed rather than silently
relaxing limits. Existing host selection still chooses the simulation authority
at startup; room ownership remains slot 0 and never migrates mid-match.
