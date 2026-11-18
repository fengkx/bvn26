# Uryu Ishida assist

The catalog uses 石田 for both the fighter and assist. The assist is compiled
from game/fighter/fz/yulong.swf. The existing selection footer supplies the
original display name 石田·雨龙.

The 49-frame root parks and stops on frame 1. Frame 2 starts entry presentation.
Frame 3 samples the opponent's position once, copying X and subtracting 100
from Y. Frame 6 opens the helper super and sets action. Frame 25 releases it.
Frame 27 requests the default shine followed by color 7329791. The current
presentation importer retains the final explicit color. Frame 28 places sprite
35 as atm1, retains that instance on frame 29 and then removes it. Its packet
requests 150 damage. Frame 33 clears action and frame 49 emits the exit effect
before the root wraps. The generated timeline retains placement lifetimes.

The diagnostic fixtures exercise P1 summoning and two mirrored P2 casts.
Original-player events, build metadata, Godot states, helper projections and
the exact comparison results accompany the fixtures. The comparison covers
14 fighter fields and six helper fields. Visual and audio parity, rollback
and browser gameplay remain open.

Both cases matched 804 fighter rows and 804 helper rows in total. P1's
summon reduced the opponent to 850 HP at tick 43. P2's two casts reduced
the opponent to 850 and then 700 HP at ticks 43 and 164.
