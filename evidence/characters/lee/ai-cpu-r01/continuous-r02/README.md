# Lee continuous AI replay r02

This is a bounded source-clock replay from a documented partial standing
checkpoint. The acceptance harness calls `intro.begin(fighters, true)` after
loading the source checkpoint; it does not claim boot or complete intro parity.

The replay uses the original Lee CPU capture with P1 Ichigo, P2 Lee, helpers
Gaara/Soul, and the source random and clock tapes. The harness wires source
input to both the P1 player controller and the P2 CPU/player-controller path.
`input_next_display` is consumed for the following display observation, so the
source key reader uses the preceding input row while producing the current
state. This phase was the cause of the earlier r01 first difference at display
tick 570; r01 remains preserved as a superseded failed diagnostic.

`acceptance.json` is `validated` for the source horizon of 300 fight ticks:
602 actor states, 602 geometry rows, 301 input rows, and the recorded
random/clock consumers pass the strict gates. The source window contains 602
helper rows, and the current validator compares each helper row
field-by-field for frame, x, y, facing, action, attacking and hits (source
undefined hits are explicitly normalized to the runtime default zero). This bounded result does not establish full AI input coverage or
full boot/intro parity.
