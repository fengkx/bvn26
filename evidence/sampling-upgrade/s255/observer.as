// Store references outside the content that unloadMovie may clear.
_global.s255Root = _root;
_global.s255Armed = false;
_global.s255Describe = function(mc)
{
   var children = [];
   for(var key in mc)
   {
      var child = mc[key];
      if(typeof(child) == "movieclip" && child._parent == mc)
         children.push(escape(String(child)) + ":" + child.getDepth() + ":" + child._currentframe);
   }
   children.sort();
   return escape(String(mc)) + "," + typeof(mc) + "," + escape(String(mc._parent)) + "," + escape(String(mc._name)) + "," + mc.getDepth() + "," + mc._currentframe + "," + mc._totalframes + "," + escape(String(mc.__aiGeoSource)) + "," + mc.__s255Token + "," + mc.__aiDlId + "," + children.length + "," + children.join(";");
};
_global.s255Observe = function(phase, receiver)
{
   var root = _global.s255Root;
   if(phase == "before_unload")
   {
      if(_global.s255Armed || receiver._parent != root.game.p1.mc) return;
      _global.s255Armed = true;
      _global.s255Receiver = receiver;
      _global.s255Parent = receiver._parent;
      _global.s255Depth = receiver.getDepth();
      _global.s255Parent.__s255Token = "s255-parent-1";
      receiver.__s255Token = "s255-receiver-1";
   }
   if(!_global.s255Armed) return;
   var parent = _global.s255Parent;
   var saved = _global.s255Receiver;
   var occupant = parent.getInstanceAtDepth(_global.s255Depth);
   var named = parent.AImain;
   root.aiEvent("aimain_identity", phase + "," + (saved == occupant) + "," + (named == occupant) + "," + (saved._parent == parent) + "," + _global.s255Depth);
   root.aiEvent("aimain_object", phase + ",parent," + _global.s255Describe(parent));
   root.aiEvent("aimain_object", phase + ",saved_receiver," + _global.s255Describe(saved));
   root.aiEvent("aimain_object", phase + ",depth_occupant," + _global.s255Describe(occupant));
   root.aiEvent("aimain_object", phase + ",named_receiver," + _global.s255Describe(named));
   if(phase == "after_unload") _global.s255AwaitRoot = true;
};
