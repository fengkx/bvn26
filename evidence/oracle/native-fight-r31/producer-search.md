# r31 independent producer search: a historical UI contract, not wire qualification

Research date: 2026-11-12. Scope: the producer-side prerequisites left by r30,
not a reclassification of r25 observations. No player, debugger connection,
Java/C++ execution, SWF compile, instrumentation or live run occurred.

## Specific producer artifacts named by the pinned client

The retained Apache Flex source itself identifies a narrower provenance target:
`DProtocol.java` says the player-side message definitions and handlers are in
`core/debugtags.h` and `core/playerdebugger.cpp`. `DMessage.java` identifies
`playerdebugger.h` / `DebugAtomType` as the origin of atom-type constants,
with an older `shared_tcserver/tcparser.h` reference. These are **source-file
provenance comments**, not copies of those implementations, version attestations,
or evidence that the exact Flash32 binary uses the same emission rules.
[Commit-pinned DProtocol lines32–45](https://github.com/apache/flex-sdk/blob/ba414443032b49c45ff11b61db452c8a8f428bd8/modules/debugger/src/java/flash/tools/debugger/concrete/DProtocol.java#L32-L45),
[commit-pinned DMessage](https://github.com/apache/flex-sdk/blob/ba414443032b49c45ff11b61db452c8a8f428bd8/modules/debugger/src/java/flash/tools/debugger/concrete/DMessage.java#L169-L172).

This supplies a concrete artifact request: authorized producer definitions and
handler code, with build provenance for Debugger 32.0.0.465, or a producer
specification covering those handlers. The names alone cannot bind an address,
ID allocation/reuse rule, per-instance removal edge or activation lifetime.
No producer implementation was obtained in this search.

## A distinct first-party historical AS2 debugger contract

Adobe's February 2013 Flash Professional CS6 Help describes the ActionScript
2.0 debugger display list updating as playback proceeds. Its note says removing
a clip also removes its displayed variables from that list, while a watched
variable may remain visible. The same AS2 debugger section describes ending
the debug session as deactivating the debugger while playback continues.
These are historical **UI behavior contracts**, not observed behavior on this
machine. [Adobe CS6 Help, PDF page597 / printed590 and PDF page601 / printed594](https://help.adobe.com/archive/en/flash/cs6/flash_reference.pdf#page=597).

This source distinguishes two observations that must not be conflated:
disappearance from a debugger display list versus continued watch visibility.
It does not specify `InRemoveObject`, IDs, native object destruction, reuse,
removal-vs-call interruption, or current client cache behavior. Session end
continuing playback does not specify resetting `break_on_fault`, setters,
timeouts, squelch, or any other protocol option. Its 2013 scope cannot certify
32.0.0.465. No UI action described by that manual was performed.

The current Adobe debugger-download URL opens an EOL information page in this
check, rather than a versioned producer protocol specification. That retrieval
result is an availability bound, not a claim that all historical documentation
is unavailable. [Adobe debugger-download URL](https://www.adobe.com/support/flashplayer/debug_downloads.html).

## Bounded search ledger

The following public queries were performed on 2026-11-12, with primary sources
selected for inspection. Search ranking or no matching result is never treated
as proof that an implementation does not exist.

| Query / inspection | Outcome and qualification decision |
|---|---|
| `site:adobe.com Flash Player 32.0.0.465 debugger release notes` | Version/download and community material did not supply a lifecycle wire or reset contract for the pinned debugger binary. No community or download result was promoted into producer proof. |
| `"InPlaceObject" "InRemoveObject" Flash debugger` | Apache client API documentation/constants; the inspected material remains consumer-side. |
| `"disable_script_stuck" "swf_load_messages" debugger` | No qualifying producer default/reset specification obtained; source-level client sends remain distinct from effective state. |
| `"playerdebugger.h" "DebugAtomType"` and `"core/playerdebugger.cpp" "debugtags.h"` | Apache source documentation and mirrors of client comments; no exact producer implementation obtained. |
| `"InRemoveObject" "32"`, `"32.0.0.465" "debug protocol"`, `"Flash" "InRemoveObject" reuse` | No qualifying build-bound lifecycle-ID/reuse evidence obtained. Unrelated third-party listings and copies of constants excluded. |
| `site:adobe.com "debugger" "object" "32.0.0.465"`; `site:adobe.com "debugger" "disconnect" "settings" "Flash"` | No exact-version effective-option reset contract obtained. Adobe AS2 manual inspected separately as the limited UI contract above. |
| Apache Flex recursive Git tree API at pinned commit | HTTP403 rate-limit response. No tree returned, so no repository-wide producer-file absence claim is made. This was a public HTTP retrieval failure, not an approval denial or a player operation. |

The exact tree request was
`https://api.github.com/repos/apache/flex-sdk/git/trees/ba414443032b49c45ff11b61db452c8a8f428bd8?recursive=1`.
No credential/session material was read and no alternate authenticated query
was attempted to turn that failure into an absence claim.

## Qualification outcome

Newly established: named producer-source provenance targets in the fixed client,
and an independent, older Adobe AS2 debugger UI contract that separates
removal display from watch visibility and describes continuation after ending
a session. Neither qualifies exact producer/version emission, the wire-to-value
ID namespace, allocation reuse/generation, or effective initialization/reset.
No AVM2 layout was substituted for AVM1. All five flags remain false; M0-02
pending. Native return and behavior-preserving connection remain unproved.

The next evidence request is specific: exact-build-authorized `debugtags.h` /
`playerdebugger.cpp` semantics (or equivalent producer documentation), covering
lifecycle event emission and its namespace/reuse plus option defaults,
acknowledgements, and disconnect/reset. Without such a source or independently
qualified retained producer transcript, repeating the same client search or
launching a connection by default is not justified. This report does not
implement or authorize a connection experiment.
