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
