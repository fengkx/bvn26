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
