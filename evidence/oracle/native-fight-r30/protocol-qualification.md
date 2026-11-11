# r30 producer, version, and ID qualification

Status: `client-contract-qualified-producer-namespace-and-preservation-unproved`.
This is an offline reading of Apache Flex SDK commit
`ba414443032b49c45ff11b61db452c8a8f428bd8`. No Java/C++ execution,
player connection, FDB attach, SWF build, or live run was performed.
These findings qualify specific client behavior. They do not qualify the
pinned Flash32 AVM1 producer or establish a native address or return.

## Version and producer identity are different obligations

`DManager.messageArrived` decodes `InVersion` into a DWORD stored as
`m_playerVersion`, followed by an optional pointer-size byte; absent that byte,
it selects four bytes. `PlayerSession.playerVersion()` returns that stored
integer. The inspected branch does not decode a build hash, executable path,
process identity, or AVM mode. This is a source-level decoder contract, not a
receipt from the pinned player. No particular version value or pointer width
was observed in this slice. [DManager 1093–1105](https://github.com/apache/flex-sdk/blob/ba414443032b49c45ff11b61db452c8a8f428bd8/modules/debugger/src/java/flash/tools/debugger/concrete/DManager.java#L1093-L1105),
[PlayerSession 202](https://github.com/apache/flex-sdk/blob/ba414443032b49c45ff11b61db452c8a8f428bd8/modules/debugger/src/java/flash/tools/debugger/concrete/PlayerSession.java#L202).

This distinction matters because successful `bind()` does not certify a
particular producer build: it starts the receive thread, sends adjustment
messages, requests squelch, probes additional capabilities and starts the reader thread, then throws
`VersionException` if that squelch request did not receive the expected response. An exception type named VersionException is not a version
attestation. [PlayerSession 336–389](https://github.com/apache/flex-sdk/blob/ba414443032b49c45ff11b61db452c8a8f428bd8/modules/debugger/src/java/flash/tools/debugger/concrete/PlayerSession.java#L336-L389).

The inspected accept path accepts a socket and constructs a PlayerSession;
its optional process listener detects a terminated launched application,
rather than checking that the accepted peer is the pinned movie process.
The receive framing starts with DWORD length and command. These inspected
paths do not bind an accepted connection to the pinned executable SHA or
particular loaded movie. This is a bounded code-path finding, not a claim
about every possible host-side binding mechanism. [PlayerSessionManager
829–877](https://github.com/apache/flex-sdk/blob/ba414443032b49c45ff11b61db452c8a8f428bd8/modules/debugger/src/java/flash/tools/debugger/concrete/PlayerSessionManager.java#L829-L877),
[DProtocol 347–358](https://github.com/apache/flex-sdk/blob/ba414443032b49c45ff11b61db452c8a8f428bd8/modules/debugger/src/java/flash/tools/debugger/concrete/DProtocol.java#L347-L358).

Pointer width is a static field on DMessage, shared by instances in that Java
class context. `getPtr()` consumes that many bytes. It is not a per-object
generation, per-session identity, or proof that a decoded integer is a usable
native address. A later qualification must preserve the received width and
its source connection, and must not mix streams with different widths through
this class-wide decoder state. No such mixing was tested or observed here.
[DMessage 205–258](https://github.com/apache/flex-sdk/blob/ba414443032b49c45ff11b61db452c8a8f428bd8/modules/debugger/src/java/flash/tools/debugger/concrete/DMessage.java#L205-L258),
[DMessage 328–335](https://github.com/apache/flex-sdk/blob/ba414443032b49c45ff11b61db452c8a8f428bd8/modules/debugger/src/java/flash/tools/debugger/concrete/DMessage.java#L328-L335).

## A narrower, verified client-side ID chain

There is a concrete client-side chain beyond merely observing that two APIs
use numbers:

1. `extractAtom`'s `kMovieClipType` branch reads `oid` with `getPtr()`, stores
   it as a Java Long, and marks the result MOVIECLIP.
2. The resulting nonprimitive value is looked up/cached by that Long in the
   target isolate's value map (insertion excludes HAS_GETTER). DValue returns its stored Long as `getId()`.
3. Thus this client's decoded MovieClip atom ID and its Value API ID are
   linked by actual implementation, scoped by isolate state. This is a
   **consumer-side** qualification; no producer message was captured here.

[DManager 2377–2388](https://github.com/apache/flex-sdk/blob/ba414443032b49c45ff11b61db452c8a8f428bd8/modules/debugger/src/java/flash/tools/debugger/concrete/DManager.java#L2377-L2388),
[DManager 2430–2455](https://github.com/apache/flex-sdk/blob/ba414443032b49c45ff11b61db452c8a8f428bd8/modules/debugger/src/java/flash/tools/debugger/concrete/DManager.java#L2430-L2455),
[DValue 216–225](https://github.com/apache/flex-sdk/blob/ba414443032b49c45ff11b61db452c8a8f428bd8/modules/debugger/src/java/flash/tools/debugger/concrete/DValue.java#L216-L225),
[DManager 176–219](https://github.com/apache/flex-sdk/blob/ba414443032b49c45ff11b61db452c8a8f428bd8/modules/debugger/src/java/flash/tools/debugger/concrete/DManager.java#L176-L219).

This does **not** complete the placement/removal join. Their handlers also
read `getPtr()`, but discard their decoded IDs rather than enter the value
cache. Equal width and Java type establish representation compatibility,
not producer namespace equivalence. No inspected producer contract maps
those lifecycle IDs to the MovieClip atom IDs, a loaded helper generation,
parent definition/depth, or a dispatch activation. The handlers contain no
generation field. [DManager 1214–1238](https://github.com/apache/flex-sdk/blob/ba414443032b49c45ff11b61db452c8a8f428bd8/modules/debugger/src/java/flash/tools/debugger/concrete/DManager.java#L1214-L1238).

Cache turnover is also not destruction: `InContinue` calls `continuing`,
which frees client caches, transfers current values to previous values,
creates a new map, and invalidates frame views. Consequently disappearance
from a current cache cannot be used as an object-removal witness; retaining
a previous map cannot prove an object survived. A run/session/isolate and
suspension-epoch envelope would prevent some accidental conflations, but
would still not constitute a producer allocation generation.
[DManager 311–330](https://github.com/apache/flex-sdk/blob/ba414443032b49c45ff11b61db452c8a8f428bd8/modules/debugger/src/java/flash/tools/debugger/concrete/DManager.java#L311-L330),
[DManager 1336–1339](https://github.com/apache/flex-sdk/blob/ba414443032b49c45ff11b61db452c8a8f428bd8/modules/debugger/src/java/flash/tools/debugger/concrete/DManager.java#L1336-L1339).

## Preservation review must include implicit traffic

In addition to the bind-time adjustments already identified in r29, this
client's receive-timeout path can actively send `OutSetSquelch(1)` as a
connection heartbeat when broken-socket detection is enabled. Therefore
"no explicit user command" would not establish a receive-only session.
This is a conditional source behavior, not proof that a heartbeat happened
on this machine. [DProtocol 326–338](https://github.com/apache/flex-sdk/blob/ba414443032b49c45ff11b61db452c8a8f428bd8/modules/debugger/src/java/flash/tools/debugger/concrete/DProtocol.java#L326-L338),
[DProtocol 356–391](https://github.com/apache/flex-sdk/blob/ba414443032b49c45ff11b61db452c8a8f428bd8/modules/debugger/src/java/flash/tools/debugger/concrete/DProtocol.java#L356-L391).

Capability getters are not purely local reads either: `getOption` emits
OutGetOption and waits for InOption. Review must distinguish local source
inspection from an active query, and must account for background SWF/SWD
requests started by bind. None of this code was executed here.
[PlayerSession 2078–2091](https://github.com/apache/flex-sdk/blob/ba414443032b49c45ff11b61db452c8a8f428bd8/modules/debugger/src/java/flash/tools/debugger/concrete/PlayerSession.java#L2078-L2091),
[PlayerSession 375–380](https://github.com/apache/flex-sdk/blob/ba414443032b49c45ff11b61db452c8a8f428bd8/modules/debugger/src/java/flash/tools/debugger/concrete/PlayerSession.java#L375-L380).

## Qualification outcome and minimum outstanding evidence

Qualified offline: the exact pinned client decoder, the MovieClip-atom →
DValue ID implementation chain, isolate/cache scoping, version-response
shape, and additional implicit outbound traffic that a preservation review
must cover. No AVM2 layout was imported into AVM1.

Still unqualified:

- The exact pinned Flash32 producer emitting InPlaceObject/InRemoveObject
  for AVM1 helper timelines, including supported settings and delivery rules.
- A producer/version-bound namespace contract relating lifecycle IDs to
  MovieClip atom IDs, allocation/reuse generations, parent/depth, and activation.
- Connection-to-owned-movie identity and full-version/build provenance;
  a version integer or successful bind alone cannot supply them.
- Whether any connection/initialization/heartbeat/background request is
  behavior-neutral for the intended observation. Omitting an option is not
  proven equivalent to the original state either.

The next prerequisite is exact-producer documentation/source or already
retained protocol evidence sufficient to resolve those points, plus a
complete command/side-effect ledger. If those cannot be obtained offline,
a separately reviewed preservation experiment would need new authorization;
this report does not authorize or implement it. No native boundary, observer,
callback, breakpoint, or capture driver is selected. All five flags remain
false and M0-02 remains pending.
