# upI source callback order probe r04

This isolated Flash probe adds sequence markers to the You `atm1` callback, the
Renji `bdmn` receiver callback (`beida()`), and the Renji outer fighter BODY
wrapper (`on_enterframe()`). The full ordered chain is in `sequence-chain.json`.

At display tick 544 / fight tick 62 the observer emits P2 root state frame 626,
then You callback sees P2 `mc._currentframe=969` (target bdmn local frame and
bounds unavailable), then Renji BODY wrapper runs at frame 969. At display tick
545 / fight tick 63 the observer emits root frame 969, then You callback sees
`mc._currentframe=970`, then BODY runs at 970. The same pattern continues for
ticks 64 and 65. The receiver `bdmn` clip callback first appears at sequence
3843, display tick 548 / fight tick 66, after You had already observed the
successful hit at sequence 3820 on display tick 547 / fight tick 65.

This establishes the measured sequence and the distinction between You child,
Renji outer BODY, and Renji receiver `bdmn`; it does not establish a global
registration order beyond these observed calls.
