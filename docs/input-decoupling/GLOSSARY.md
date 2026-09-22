# Input decoupling glossary

This glossary accompanies the agreed
[input decoupling decision](ADR.md).

| Term | Meaning in this design |
|---|---|
| Logical button | A gameplay meaning such as attack or left, independent of the physical key chosen in settings. |
| Held input | Which logical buttons remain down when the existing controller samples input. |
| Input source | A producer of logical input, initially the keyboard or developer playback. A future network adapter can be another producer. |
| Player slot | The controlled side, P1 or P2, independent of character choice and whether the input is local or remote. |
| Display tick | The existing numbered 30 Hz update boundary. Adding it to a recording does not change the scheduler. |
| Input boundary | The point where device-independent input enters existing game control code. |
| Match-control operation | An operation such as intro skip, pause or resume that affects a match beyond a fighter's held buttons. |
| Event phase/order | Where an event occurs relative to updates and other events. Needed to avoid changing key-release and pause timing. |
| Input recording | A record of supplied controls. It does not contain every piece of battle state. |
| Controlled playback | Reapplying recorded controls with explicitly controlled starting conditions and external timing/random inputs for a regression. |
| Full-state snapshot | All information needed to resume a match at a chosen point, including hidden controller and scheduler state. Not part of this change. |
| Rollback | Restoring an earlier full state and recomputing updates after late input arrives. Deferred. |
| Friend room | The first planned online user flow: friends join the same room to play. No room implementation is included in input decoupling. |
