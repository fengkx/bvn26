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
