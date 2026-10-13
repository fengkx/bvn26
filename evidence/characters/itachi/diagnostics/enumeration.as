var hitks = ["tk","tz","k1","k2","k3","k4","k5","kj1","kj2","zh1","zh2","zh3","bs","sbs","cbs","kbs"];
var stgks = ["stgk1","stgk2","stgk3","stgk4","stgk5","stgk6","stgk7","stgk8","stgk9","stgk10"];
var _fsArray = [];
var i = 0;
while(i < hitks.length)
{
   var kv = hitks[i];
   _fsArray.push(kv);
   var k = 1;
   while(k <= 5)
   {
      _fsArray.push(kv + k);
      k++;
   }
   i++;
}
var _fzfsArray = ["atm1","atm2","atm3","atm4","atm5"];

var order=[]; for(var key in _fsArray) {order.push(_fsArray[key]);}
trace("AIREF|itachi-enumeration|1|0|0|0|order|"+order.join(","));
trace("AIREF|itachi-enumeration|2|0|0|0|done|true");
fscommand("quit");