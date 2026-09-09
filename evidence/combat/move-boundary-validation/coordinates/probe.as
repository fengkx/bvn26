// Analysis-only binary significand encoding avoids FP32's short decimal strings.
_root.aiNumber = function(value)
{
   if(typeof value != "number" || !isFinite(value)) return String(value);
   if(value == 0) return "f:" + (1 / value < 0 ? -1 : 1) + ":0:0:0";
   var sign = value < 0 ? -1 : 1;
   var fraction = Math.abs(value);
   var exponent = 0;
   while(fraction >= 2) { fraction /= 2; exponent++; }
   while(fraction < 1) { fraction *= 2; exponent--; }
   var mantissa = fraction * 4503599627370496;
   var high = Math.floor(mantissa / 67108864);
   var low = mantissa - high * 67108864;
   return "f:" + sign + ":" + exponent + ":" + high + ":" + low;
};

Stage.displayState = "normal";
Stage.scaleMode = "showAll";
stop();
var seq = 0;
var obj = _root.createEmptyMovieClip("measured", 1);
function emit(kind, value) {
   trace("AIREF|coordinate-r1|" + (++seq) + "|" + getTimer() + "|0|0|" + kind + "|" + value);
}
var values = [0,0.024,0.025,0.049,0.05,0.051,-0.024,-0.025,-0.049,-0.05,-0.051,14.4,-14.4,314.4,-314.4];
for(var i = 0; i < values.length; i++) {
   obj._x = values[i]; obj._y = values[i];
   emit("set", aiNumber(values[i]) + "," + aiNumber(obj._x) + "," + aiNumber(obj._y));
}
for(var sign = -1; sign <= 1; sign += 2) {
   obj._x = 300 * sign; obj._y = -25;
   for(var step = 0; step < 20; step++) {
      obj._x += 14.4 * sign; obj._y -= 19.2;
      emit("step", sign + "," + step + "," + aiNumber(obj._x) + "," + aiNumber(obj._y));
   }
}
emit("done", "");
fscommand("quit");
