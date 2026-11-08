// Analysis-only forwarding observers. No input value or random result is substituted.
_root.__m002Seq = 0;
_root.__m002Ordinal = 0;
_root.__m002Phase = "before-game-callback";
_root.__m002Ended = false;
_root.__m002Emit = function(kind, data)
{
   if(_root.__m002Ended) return;
   trace("M002|__RUN_ID__|" + (++_root.__m002Seq) + "|" + getTimer() + "|" + _root.__m002Ordinal + "|" + _root.__m002Phase + "|" + kind + "|" + data);
};
_root.__m002Value = function(value)
{
   return escape(_root.__m002Number(value));
};
_root.__m002Random = function(site)
{
   var result = Math.random();
   _root.__m002Emit("random-return", site + "," + _root.__m002Value(result));
   return result;
};
_root.__m002Key = function(code, site)
{
   var result = Key.isDown(code);
   _root.__m002Emit("key-return", site + "," + code + "," + result);
   return result;
};
_root.__m002State = function(slot)
{
   var actor = _root.game[slot];
   var body = actor.mc;
   var fields = [slot, actor._x, actor._y, actor._xscale, body._currentframe, body.hp, body.ql, body.动作, body.beida, body.kcplayed];
   var result = "";
   for(var i = 0; i < fields.length; i++)
   {
      if(i > 0) result += ",";
      result += _root.__m002Value(fields[i]);
   }
   _root.__m002Emit("actor-state", result);
};
_root.__m002Checkpoint = function(phase)
{
   _root.__m002Phase = phase;
   _root.__m002Emit("game-state", _root._currentframe + "," + _root.rounds + "," + _root.zhanting + "," + _root.gamePaused + "," + _root.p2loaded + "," + _root.modo + "," + escape(_root.curStage) + "," + escape(_root.p1selt) + "," + escape(_root.p2selt) + "," + escape(_root.p1sf) + "," + escape(_root.p2sf));
   _root.__m002State("p1");
   _root.__m002State("p2");
};
_root.__m002Emit("boot", "observer-installed;no-input-substitution;ordinal-is-local");
