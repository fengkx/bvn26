# Independent research: Apache Flex debugger protocol identity

Research date: 2026-11-12. Primary source: Apache Flex SDK commit
`ba414443032b49c45ff11b61db452c8a8f428bd8`, fetched from Apache's public repository.
No Flash launch, socket connection, debugger attachment or protocol command was performed.
This is new external implementation/API evidence, not a reclassification of r25 traces.

## Concrete new lead: object placement/removal messages

The debugger client enumerates player-originated messages `InPlaceObject=13`,
`InNewObject=3`, `InRemoveObject=4`, `InBreakAtExt=27`, and `InFrame=31`.
These are protocol discriminants, not addresses in the proprietary player.
[DMessage constants](https://github.com/apache/flex-sdk/blob/ba414443032b49c45ff11b61db452c8a8f428bd8/modules/debugger/src/java/flash/tools/debugger/concrete/DMessage.java#L40-L80).

`DManager` reads placement as a pointer-width object ID plus path, and removal as
an object ID. The object-bag updates are commented out: these handlers do not
publish a typed removal event or maintain an object-lifetime ledger. This is a
concrete independently inspectable **consumer-side wire shape**, not evidence
that Flash32 sends these messages for timeline helper removal. Version handling
reads a negotiated pointer width, defaulting to four bytes for older responses.
[DManager message parsing](https://github.com/apache/flex-sdk/blob/ba414443032b49c45ff11b61db452c8a8f428bd8/modules/debugger/src/java/flash/tools/debugger/concrete/DManager.java#L1093-L1105),
[placement/removal handlers](https://github.com/apache/flex-sdk/blob/ba414443032b49c45ff11b61db452c8a8f428bd8/modules/debugger/src/java/flash/tools/debugger/concrete/DManager.java#L1214-L1238).

The named `SwfUnloadedEvent` is explicitly about an entire SWF and carries SWF ID,
index and path. It must not be substituted for a MovieClip/helper removal event.
[SwfUnloadedEvent](https://github.com/apache/flex-sdk/blob/ba414443032b49c45ff11b61db452c8a8f428bd8/modules/debugger/src/java/flash/tools/debugger/events/SwfUnloadedEvent.java#L24-L45).

## Object identity has a documented API meaning, but not a native generation schema

`Value.getId()` promises equal IDs for variables referring to the same underlying
Object/MovieClip. `_global` and `_root` pseudo-identifiers are explicitly marked
AS2-only, so the API is not wholly AVM2-specific. `Session.getValue()` documents ID
stability during a Value's lifetime and null for values that become inaccessible
or cannot be found. Neither contract says that null proves native destruction,
that IDs cannot be reused after death, or that a wire removal ID has been bound to
an r25 helper. The ID contract is useful independent semantics for a **prospective
protocol-level alias test**, not a verified native pointer/owner/generation layout.
[Value identity and AS2 pseudo-values](https://github.com/apache/flex-sdk/blob/ba414443032b49c45ff11b61db452c8a8f428bd8/modules/debugger/src/java/flash/tools/debugger/Value.java#L35-L76),
[Value.getId](https://github.com/apache/flex-sdk/blob/ba414443032b49c45ff11b61db452c8a8f428bd8/modules/debugger/src/java/flash/tools/debugger/Value.java#L146-L155),
[Session.getValue](https://github.com/apache/flex-sdk/blob/ba414443032b49c45ff11b61db452c8a8f428bd8/modules/debugger/src/java/flash/tools/debugger/Session.java#L394-L415).

## Stack snapshots do not independently certify activation continuity

`Frame` is an ActionScript call-stack snapshot valid only while suspended; its
`this` may be unavailable. The API's frame location/signature is not a native
dispatch-entry/exit token.
[Frame contract](https://github.com/apache/flex-sdk/blob/ba414443032b49c45ff11b61db452c8a8f428bd8/modules/debugger/src/java/flash/tools/debugger/Frame.java#L20-L42).

`DStackContext` discards the constructor's supplied `thisId` as unreliable and
lazily requests frame variables. Its internal “activation object” is a variable
container, not a documented native callback-activation generation.
[DStackContext constructor](https://github.com/apache/flex-sdk/blob/ba414443032b49c45ff11b61db452c8a8f428bd8/modules/debugger/src/java/flash/tools/debugger/concrete/DStackContext.java#L51-L65),
[activation-object and population code](https://github.com/apache/flex-sdk/blob/ba414443032b49c45ff11b61db452c8a8f428bd8/modules/debugger/src/java/flash/tools/debugger/concrete/DStackContext.java#L134-L168).

Across suspensions, `DManager.mapOldFramesToNew()` correlates frames using call
signatures from the bottom of the stack; this is explicitly a heuristic for
local-value-change display. It cannot qualify uninterrupted activation identity.
[DManager frame mapping](https://github.com/apache/flex-sdk/blob/ba414443032b49c45ff11b61db452c8a8f428bd8/modules/debugger/src/java/flash/tools/debugger/concrete/DManager.java#L946-L988).

## Applicability and preservation boundary

The client contains legacy AS2 paths, but no inspected source proves that the
specific pinned Flash32/macOS binary emits the placement/removal messages for
AVM1 timeline replacement, identifies their dispatch timing, or exposes the native
field offsets r28 requires. A producer-side binding or separately reviewed
protocol qualification remains necessary. Do not transfer AVM2-looking activation
object terminology into an AVM1/native activation schema.

Connecting this client is not passive preservation proof: initialization sends
squelch/options, and `sendStopWarning()` changes script-stuck behavior with an
AS2/AS3 distinction. `requestFrame()` requires suspension and supported get
operations. These source facts require a reviewed initialization/command whitelist
and explicit preservation assessment before any future protocol experiment; no
such experiment is authorized or implemented here.
[PlayerSession initialization](https://github.com/apache/flex-sdk/blob/ba414443032b49c45ff11b61db452c8a8f428bd8/modules/debugger/src/java/flash/tools/debugger/concrete/PlayerSession.java#L350-L380),
[frame requests](https://github.com/apache/flex-sdk/blob/ba414443032b49c45ff11b61db452c8a8f428bd8/modules/debugger/src/java/flash/tools/debugger/concrete/PlayerSession.java#L1074-L1098),
[script-stuck options](https://github.com/apache/flex-sdk/blob/ba414443032b49c45ff11b61db452c8a8f428bd8/modules/debugger/src/java/flash/tools/debugger/concrete/PlayerSession.java#L1878-L1892).

**Research result:** a specific externally defined protocol message family and
object-alias API contract were found. They narrow what to investigate independently
next; they do not supply a native removal boundary, native owner/generation/activation
schema, r25 target→call join, native return or after-silence cause. All five admission
flags remain false and M0-02 pending. No live facility was added.
