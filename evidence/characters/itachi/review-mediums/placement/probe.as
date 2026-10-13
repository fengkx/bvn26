stop();
var calls = 1;
var ticks = 0;
createEmptyMovieClip("zh1atm", 1);
zh1atm._x = 17;
zh1atm._x = zzzz._x;
missing._x = 99;
trace("AIREF|itachi-placement-once-r01|1|0|0|0|initial|" + zh1atm._x + "," + missing);
onEnterFrame = function() {
 ticks++;
 if(ticks == 1) {
  createEmptyMovieClip("zzzz", 2); zzzz._x = 123;
  createEmptyMovieClip("missing", 3); missing._x = 23;
 }
 if(ticks == 3) {
  trace("AIREF|itachi-placement-once-r01|2|3|0|0|later|" + zh1atm._x + "," + missing._x + "," + calls);
  trace("AIREF|itachi-placement-once-r01|3|3|0|0|done|true");
  fscommand("quit");
 }
};
