stop();
xure.gotoAndPlay("地图");
_root.mapProbeTick = 0;
_root.mapProbeInterval = setInterval(function() {
 var m = _root.xure.xrmc;
 if (!m.isMap) { return; }
 _root.mapProbeTick++;
 if (_root.mapProbeTick == 20) { m.left(1); }
 if (_root.mapProbeTick == 30) { m.up(1); }
 if (_root.mapProbeTick == 40) { m.right(1); }
 if (_root.mapProbeTick == 50) { m.down(1); }
 if (_root.mapProbeTick <= 55) {
 trace("MAP_ORACLE tick=" + _root.mapProbeTick + " frame=" + _root.xure._currentframe + " x=" + m.curx1 + " y=" + m.cury1 + " stage=" + _root.curStage + " alpha=" + m._p1selt._alpha + " p2=" + m.p2enable);
 }
},33);

setTimeout(function() {
 var m = _root.xure.xrmc;
 m.updateXY(1,1,0);
 m.czint1 = undefined;
 var originalEnterFrame = m.onEnterFrame;
 _root.mapHeld = {};
 _root.mapKeyIsDown = function(code) { return _root.mapHeld[code] == true; };
 var tick = 0;
 m.onEnterFrame = function() {
  tick++;
  _root.mapHeld = {};
  if (tick <= 6) { _root.mapHeld[_root.s] = true; }
  if (tick == 12) { _root.mapHeld[_root.j] = true; _root.mapConfirmTime = getTimer(); }
  originalEnterFrame();
  if (tick <= 40) trace("MAP_INPUT tick="+tick+" stage="+_root.curStage+" repeat="+m.czint1+" enabled="+m.p1enable);
 };
},2200);
