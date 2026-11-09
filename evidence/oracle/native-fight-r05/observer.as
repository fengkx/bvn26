// Separate local clocks; neither is a certified ExecutionProfile tick.
_root.__m002ClockOrdinal = 0;
_root.__m002FightKey = function(owner, code, site)
{
   var result = owner.kis(code);
   _root.__m002Emit("fight-key-return", site + "," + code + "," + result + "," + escape(owner._target) + "," + owner._parent.useAI + "," + _root.zhanting + "," + _root.gamePaused + "," + owner._currentframe + "," + _root.__m002Value(owner.动作) + "," + _root.__m002Value(_root.gametime));
   return result;
};
_root.__m002Clock = function(boundary)
{
   _root.__m002Emit("clock-" + boundary, _root.__m002ClockOrdinal + "," + _root.__m002Value(_root.gametime) + "," + _root.zhanting + "," + _root.gamePaused);
   _root.__m002State("p1");
   _root.__m002State("p2");
};
