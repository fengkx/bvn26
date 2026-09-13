# Rukia base source/native action coverage r05–r11

Six additional fixed-input cases were captured from the original Flash player and strictly compared against the Godot harness. Each has 602 source rows, 602 native rows, and exact agreement across the 14 state fields. The captures cover the second jump, down-jump/fall, guard continuation, walk, ordinary hit reaction, and one complete knockdown/recovery chain.

The knockdown case uses P2 Ichigo’s source `必杀` input at ticks 10–13. The Rukia trace visits `击飞` at frames 931–938, `击落地` at 943–945, then a downed `冲` input at ticks 65–68 enters `起身` at frames 978–988. This is one confirmed chain for this exact opponent attack and timing. The ordinary hit case visits `被打` only.

The evidence keeps each original event stream, native rows, fixture, build/source hashes, input tapes, instrumentation diff, and strict comparison under the case directories listed in `results.json`. `SHA256SUMS.json` covers those captured case trees and this packet’s README/results.

This packet proves only the recorded inputs. It does not establish every hit timing, audible output, Web behavior, or Rukia-specific round/opening presentation. `万解` remains out of scope and base-form `上必杀` is absent from the base timeline.
