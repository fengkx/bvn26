_root.cfgClips = {};
_root.cfgHeld = {};
_root.cfgTick = -1;
_root.cfgSeq = 0;
_root.cfgKey = function(code) { return _root.cfgHeld[code] == true; };
_root.cfgEvent = function(kind, value) {
   _root.cfgSeq++;
   trace("AIREF|config-r01|" + _root.cfgSeq + "|" + getTimer() + "|" + _root.cfgTick + "|" + _root.cfgTick + "|" + kind + "|" + value);
};
_root.AI = 5;
_root.maxhp = 1000;
_root.maxtime = 60;
_root._quality = "HIGH";
_root.onEnterFrame = function() {
   if(_root.cfgClips[33] == undefined) return;
   _root.cfgTick++;
   var panel = _root.cfgClips[33]._parent;
   _root.cfgEvent("state", panel.cselect + "," + panel.cmlv.cl + "," + panel.qulity.cl + "," + panel.gtime.cl + "," + panel.plife.cl + "," + _root.AI + "," + _root._quality + "," + _root.maxtime + "," + _root.maxhp);
   _root.cfgHeld = {};
   var row = Math.floor(_root.cfgTick / 40);
   var phase = _root.cfgTick % 40;
   if(row < 4) {
      panel.cselect = [2,3,4,5][row];
      if(phase < 14 && phase % 2 == 0) _root.cfgHeld[_root.d] = true;
      if(phase >= 16 && phase < 32 && phase % 2 == 0) _root.cfgHeld[_root.a] = true;
      if(phase == 34) { _root.cfgHeld[_root.a] = true; _root.cfgHeld[_root.d] = true; }
      for(var i in _root.cfgClips) _root.cfgClips[i].cfgDown();
   }
   if(_root.cfgTick == 160) { _root.cfgEvent("done", "config"); fscommand("quit"); }
};
_root.gotoAndStop("游戏设置");
