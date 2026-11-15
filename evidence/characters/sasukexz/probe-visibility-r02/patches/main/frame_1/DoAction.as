Stage.displayState = "normal";
Stage.scaleMode = "showAll";
// Native MovieClip observations; authored non-MovieClip leaves are joined offline.
_root.aiDlSerial = 0;
_root.aiDlMatrix = function(m)
{
   return _root.aiNumber(m.a)+","+_root.aiNumber(m.b)+","+_root.aiNumber(m.c)+","+_root.aiNumber(m.d)+","+_root.aiNumber(m.tx)+","+_root.aiNumber(m.ty);
};
_root.aiDlWalk = function(mc, parent)
{
   var path = String(mc);
   if(_root.aiDlSeen[path] == true) return;
   _root.aiDlSeen[path] = true;
   if(mc.__aiDlId == undefined) mc.__aiDlId = ++_root.aiDlSerial;
   var rect = mc.scrollRect;
   var clip = rect == null ? "none" : _root.aiNumber(rect.x)+":"+_root.aiNumber(rect.y)+":"+_root.aiNumber(rect.width)+":"+_root.aiNumber(rect.height);
   var filters = mc.filters;
   _root.aiEvent("display_node", escape(path)+","+escape(parent)+","+mc.__aiDlId+","+escape(String(mc.__aiGeoSource))+","+mc.getDepth()+","+mc._currentframe+","+_root.aiDlMatrix(mc.transform.matrix)+","+_root.aiDlMatrix(mc.transform.concatenatedMatrix)+","+mc._visible+","+_root.aiNumber(mc._alpha)+","+mc.blendMode+","+mc.cacheAsBitmap+","+clip+","+filters.length);
   for(var i=0; i<filters.length; i++)
   {
      var f=filters[i];
      var fields=["blurX","blurY","quality","alpha","color","strength","inner","knockout","hideObject","distance","angle","matrix","colors","alphas","ratios","type","width","height","divisor","bias","preserveAlpha","clamp"];
      var value="";
      for(var j=0;j<fields.length;j++) if(f[fields[j]] != undefined) value += fields[j]+"="+escape(String(f[fields[j]]))+";";
      _root.aiEvent("display_filter",escape(path)+","+i+","+value);
   }
   var children=[];
   var names={};
   for(var key in mc)
   {
      var child=mc[key];
      if(typeof(child)=="movieclip" && child._parent==mc && names[String(child)]!=true)
      {
         names[String(child)]=true;
         children.push(child);
      }
   }
   _root.aiEvent("display_children",escape(path)+","+children.length);
   _root.aiDlCount++;
   for(var k=0;k<children.length;k++) _root.aiDlWalk(children[k],path);
};
_root.aiDisplaySample = function()
{
   if(_root.aiFight<0) return;
   _root.aiDlSeen={};
   _root.aiDlCount=0;
   _root.aiEvent("display_begin","");
   _root.aiEvent("display_camera",Stage.width+","+Stage.height+","+Stage.scaleMode+","+Stage.align+","+_root.aiDlMatrix(_root.transform.matrix)+","+_root.aiDlMatrix(_root.transform.concatenatedMatrix));
   _root.aiDlWalk(_root.game, String(_root));
   _root.aiEvent("display_end",_root.aiDlCount);
};
// Analysis only: enumerate the source collision receivers and their candidate lists.
_root.aiGeoSerial = 0;
_root.aiGeoStamp = function(mc, source)
{
   if(mc.__aiGeoId == undefined)
   {
      mc.__aiGeoId = ++_root.aiGeoSerial;
      mc.__aiGeoSource = source;
      mc.__aiGeoBirth = _root.aiDisplay;
   }
};
_root.aiGeoBox = function(mc, role)
{
   if(mc == undefined) return;
   var path = String(mc);
   if(_root.aiGeoSeen[path] == true) return;
   _root.aiGeoSeen[path] = true;
   if(mc.__aiGeoId == undefined || mc.__aiGeoSource == undefined)
   {
      _root.aiEvent("geometry_error", "unbound:" + path);
      return;
   }
   var m = mc.transform.concatenatedMatrix;
   var b = mc.getBounds(mc);
   _root.aiEvent("geometry_box", role + "," + path + "," + mc.__aiGeoId + "," + mc.__aiGeoSource + "," + mc.__aiGeoBirth + "," + mc.getDepth() + "," + mc._currentframe + "," + _root.aiNumber(m.a) + "," + _root.aiNumber(m.b) + "," + _root.aiNumber(m.c) + "," + _root.aiNumber(m.d) + "," + _root.aiNumber(m.tx) + "," + _root.aiNumber(m.ty) + "," + _root.aiNumber(b.xMin) + "," + _root.aiNumber(b.yMin) + "," + _root.aiNumber(b.xMax) + "," + _root.aiNumber(b.yMax));
   _root.aiGeoCount++;
};
_root.aiGeoWalk = function(mc)
{
   var path = String(mc);
   if(_root.aiGeoWalked[path] == true) return;
   _root.aiGeoWalked[path] = true;
   if(typeof(mc.getHitObj) == "function" && typeof(mc.getStgHitObj) == "function")
   {
      _root.aiGeoReceivers++;
      var boxName = mc._name;
      var boxRole = boxName.substr(boxName.length - 3) == "atm" ? "attack" : "hurt";
      _root.aiGeoBox(mc,boxRole);
      var target = _root.game["p" + mc._parent.pn];
      if(target == undefined || mc._fsArray == undefined || mc._fzfsArray == undefined || mc.stgks == undefined)
         _root.aiEvent("geometry_error", "missing-source-list:" + path);
      for(var i in mc._fsArray) _root.aiGeoBox(target.mc[mc._fsArray[i] + "atm"],"attack");
      for(var j in mc._fzfsArray) _root.aiGeoBox(_root.game["p" + mc._parent.pn + "fz"][mc._fzfsArray[j]],"helper_attack");
      for(var k in mc.stgks)
      {
         var stage = _root.game.layer_effect[mc.stgks[k] + "_P" + mc._parent.pn];
         if(stage != undefined) _root.aiGeoBox(stage.mian,"stage_attack");
      }
   }
   for(var name in mc)
   {
      var child = mc[name];
      if(typeof(child) == "movieclip" && child._parent == mc) _root.aiGeoWalk(child);
   }
};
_root.aiGeometrySample = function()
{
   if(_root.aiFight < 0) return;
   _root.aiGeoSeen = {};
   _root.aiGeoWalked = {};
   _root.aiGeoCount = 0;
   _root.aiGeoReceivers = 0;
   _root.aiEvent("geometry_begin", "");
   _root.aiGeoWalk(_root.game);
   _root.aiEvent("geometry_end", _root.aiGeoCount + "," + _root.aiGeoReceivers);
};
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
_root.aiRun = "sasukexz-visibility-r02";
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

_root.aiGeoStamp(this, "game/main.swf#frame_1/DoAction.as");
