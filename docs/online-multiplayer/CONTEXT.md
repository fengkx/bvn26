# Online BVN matches

Vocabulary for friends playing BVN on separate devices. Terms shared with the
existing [input glossary](../input-decoupling/GLOSSARY.md) retain their meaning.

## Language

**Friend room**:
A place where invited friends gather to arrange and enter a match.
_Avoid_: Matchmaking queue, match.

**Match**:
A contest between the two player sides, with an agreed starting setup and an
eventual result or termination.
_Avoid_: Room, connection, single round.

**Player slot**:
One of the two controlled sides, P1 or P2, independent of device or character.
_Avoid_: Network peer ID, keyboard number.

**Match setup**:
The initial choices and rules of a match, including fighters, helpers, stage
and applicable game settings.
_Avoid_: Current battle state, snapshot.

**Match-control operation**:
An ordered operation affecting the match beyond a fighter's held buttons,
such as intro skip, pause, resume or exit.
_Avoid_: Held button, pause Boolean.

**Input recording**:
A record of supplied controls and their ordering from a fresh match setup.
_Avoid_: Full-state snapshot, guaranteed battle replay.

**Room owner**:
The participant who created the room and holds its agreed setup permissions.
_Avoid_: Authoritative battle server, always-winning host.

**Confirmed match frame**:
A battle frame for which both players' actual inputs and required match-control
operations are known. State agreement is a separate validation of the simulation.
_Avoid_: Merely displayed frame, server-approved hit.

**Predicted match frame**:
A battle frame advanced while at least one required remote input is still
assumed rather than received; its consequences can change after correction.
_Avoid_: Final result, confirmed match frame.

**Battle correction**:
Replacement of a predicted battle history by restoring prior match state and
recomputing it with the received inputs.
_Avoid_: Hitbox rewind, damage veto, visual smoothing.
