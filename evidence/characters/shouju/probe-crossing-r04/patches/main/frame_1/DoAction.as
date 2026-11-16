Stage.displayState = "normal";
Stage.scaleMode = "showAll";
_root.aiHelperClipFrame = function(helper, instanceName)
{
   var clip = helper[instanceName];
   return clip == undefined ? undefined : clip._currentframe;
};
_root.aiHelperState = function(player)
{
   var f = _root.game[player + "fz"];
   var m = f;
   _root.aiEvent("helper_state", player + "," + m._currentframe + "," + _root.aiNumber(f._x) + "," + _root.aiNumber(f._y) + "," + _root.aiNumber(f._xscale) + "," + m.attacking + "," + m.动作 + "," + m.hits + "," + _root.aiHelperClipFrame(f,"atm1") + "," + _root.aiHelperClipFrame(f,"atm2") + "," + _root.aiHelperClipFrame(f,"atm3"));
   _root.aiEvent("helper_clip_state", player + "," + m._currentframe + "," + "atm1" + "=" + _root.aiHelperClipFrame(f,"atm1"));
   var parent = f._parent;
   _root.aiEvent("helper_lifecycle", player + "," + m._currentframe + "," + f._visible + "," + _root.zhanting + "," + (parent == undefined ? undefined : parent._currentframe) + "," + _root.aiHelperClipFrame(f,"atm1") + "," + _root.aiHelperClipFrame(f,"atm2") + "," + _root.aiHelperClipFrame(f,"atm3"));
};
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
// Analysis-only bootstrap: the original battle loader and AI remain active.
_root.aiRun = "shouju-crossing-r04";
_root.aiSeq = 0;
_root.aiDisplay = 0;
_root.aiFight = -1;
_root.aiDraw = 0;
_root.aiClockDraw = 0;
_root.aiNativeRandom = Math.random;
_root.aiEvent = function(kind, value)
{
   trace("AIREF|" + aiRun + "|" + (++aiSeq) + "|" + getTimer() + "|" + aiDisplay + "|" + aiFight + "|" + kind + "|" + value);
};
_root.aiTimer = function(site)
{
   var value = getTimer();
   _root.aiEvent("clock", (++_root.aiClockDraw) + "," + site + "," + value);
   return value;
};
_root.aiRandom = function(site)
{
   var value = _root.aiNativeRandom();
   _root.aiEvent("random", (++_root.aiDraw) + "," + site + "," + _root.aiNumber(value));
   return value;
};
_root.aiPredicate = function(name, receiver, value)
{
   if(receiver._parent._parent.useAI || receiver._parent.useAI)
   {
      _root.aiEvent("predicate", name + "," + receiver + "," + value);
   }
   return value;
};
_root.aiState = function(player)
{
   var f = _root.game[player];
   var m = f.mc;
   _root.aiEvent("state", player + "," + m._currentframe + "," + _root.aiNumber(f._x) + "," + _root.aiNumber(f._y) + "," + _root.aiNumber(f._xscale) + "," + m.动作 + "," + _root.aiNumber(m.hp) + "," + _root.aiNumber(m.ql) + "," + m.sw + "," + m.touch + "," + m.touchFloor + "," + m.hits + "," + _root.zhanting + "," + m.hstm + "," + m.hurtSkling);
};
_root.aiGeometry = function()
{
   var f = _root.game.p2;
   var m = f.mc;
   var target = _root.game.p1.mc.bdmn;
   var names = ["kanmian","tkanmian","zh1mian","zh2mian","zh3mian","kj1mian","kj2mian","bsmian","sbsmian","cbsmian","tzmian","absmian"];
   _root.aiEvent("geometry_frame", m._currentframe + "," + f._x + "," + f._y + "," + f._xscale);
   var chain = [f,m,m.AImain];
   for(var c = 0; c < chain.length; c++)
   {
      var cm = chain[c].transform.matrix;
      var gm = chain[c].transform.concatenatedMatrix;
      _root.aiEvent("geometry_matrix", c + "," + cm.a + "," + cm.b + "," + cm.c + "," + cm.d + "," + cm.tx + "," + cm.ty + "," + gm.a + "," + gm.b + "," + gm.c + "," + gm.d + "," + gm.tx + "," + gm.ty);
   }
   for(var n = 0; n < names.length; n++)
   {
      var obj = m.AImain[names[n]];
      var bounds = obj.getBounds(f);
      _root.aiEvent("sensor_bounds", names[n] + "," + bounds.xMin + "," + bounds.yMin + "," + bounds.xMax + "," + bounds.yMax + "," + obj.hitTest(target));
      var own = obj.getBounds(obj);
      var sm = obj.transform.matrix;
      _root.aiEvent("sensor_local", names[n] + "," + own.xMin + "," + own.yMin + "," + own.xMax + "," + own.yMax + "," + sm.a + "," + sm.b + "," + sm.c + "," + sm.d + "," + sm.tx + "," + sm.ty);
   }
};
function showCommt()
{
   if(allowGoLink)
   {
      goLink();
      return undefined;
   }
   if(_global.bridge)
   {
      _global.bridge.showGameList();
   }
}
function goLink(url)
{
}
_root.ver = "V 2.6";
_root.date_ver = "2016/6/23";
var adType;
var wudi = false;
var TYPE_4399 = "4399";
var allowGoLink = true;
var NO_AD = "no-ad";
var debuging = true;
adType = TYPE_4399;
var _loc0_;
if((_loc0_ = adType) === TYPE_4399)
{
   _global.bridge = AS2_4399_API.Bridge.getInstance();
   var _4399_function_ad_id = "944c23f5e64a80647f8d0f3435f5c7a8";
   allowGoLink = false;
}

gotoAndPlay(6);
