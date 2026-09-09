stop();
var labels = ["third","guard_energy","tenth","negative","high","small","negative_zero"];
var values = [1/3,80/15,0.1,-1/3,9007199254740991,Math.pow(2,-100),-0];
for(var i=0; i<values.length; i++) trace("NUMBER|" + labels[i] + "|" + values[i] + "|" + _root.aiNumber(values[i]));
trace("NUMBER|done");
fscommand("quit");
