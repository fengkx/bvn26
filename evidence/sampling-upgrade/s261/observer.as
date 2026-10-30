// Store references outside the content that unloadMovie may clear.
_global.s261Root = _root;
_global.s261Armed = false;
_global.s261Describe = function(mc)
{
   var children = [];
   for(var key in mc)
   {
      var child = mc[key];
      if(typeof(child) == "movieclip" && child._parent == mc)
         children.push(escape(String(child)) + ":" + child.getDepth() + ":" + child._currentframe);
   }
   children.sort();
   return escape(String(mc)) + "," + typeof(mc) + "," + escape(String(mc._parent)) + "," + escape(String(mc._name)) + "," + mc.getDepth() + "," + mc._currentframe + "," + mc._totalframes + "," + escape(String(mc.__aiGeoSource)) + "," + mc.__s261Token + "," + mc.__aiDlId + "," + children.length + "," + children.join(";");
};
_global.s261Observe = function(phase, receiver)
{
   var root = _global.s261Root;
   if(phase == "before_unload")
   {
      if(_global.s261Armed || receiver._parent != root.game.p1.mc) return;
      _global.s261Armed = true;
      _global.s261Receiver = receiver;
      _global.s261Parent = receiver._parent;
      _global.s261Depth = receiver.getDepth();
      _global.s261Parent.__s261Token = "s261-parent-1";
      receiver.__s261Token = "s261-receiver-1";
      _global.s261Controls();
   }
   if(!_global.s261Armed) return;
   var parent = _global.s261Parent;
   var saved = _global.s261Receiver;
   var occupant = parent.getInstanceAtDepth(_global.s261Depth);
   var named = parent.AImain;
   root.aiEvent("aimain_identity", phase + "," + (saved == occupant) + "," + (named == occupant) + "," + (saved._parent == parent) + "," + _global.s261Depth);
   root.aiEvent("aimain_object", phase + ",parent," + _global.s261Describe(parent));
   root.aiEvent("aimain_object", phase + ",saved_receiver," + _global.s261Describe(saved));
   root.aiEvent("aimain_object", phase + ",depth_occupant," + _global.s261Describe(occupant));
   root.aiEvent("aimain_object", phase + ",named_receiver," + _global.s261Describe(named));
   if(phase == "root" && occupant._currentframe == 0 && occupant._totalframes == 0) _global.s261Zero = true;
   if(phase == "after_unload") _global.s261AwaitRoot = true;
};

// Independent controls live outside the game tree and are removed synchronously.
_global.s261Controls = function()
{
   var host = _root.createEmptyMovieClip("__s261Control", 100001);
   var saved = host.createEmptyMovieClip("slot", 1);
   var token = {};
   saved.identity = token;
   _root.aiEvent("s261_control", "retained," + (saved == host.slot) + "," + (host.slot.identity == token));
   saved.removeMovieClip();
   var replacement = host.createEmptyMovieClip("slot", 1);
   replacement.identity = {};
   _root.aiEvent("s261_control", "replaced," + (saved == host.slot) + "," + (host.slot.identity == token));
   var retained = replacement;
   var secondToken = replacement.identity;
   delete replacement.identity;
   _root.aiEvent("s261_control", "retained_content_deleted," + (retained == host.slot) + "," + (host.slot.identity == secondToken));
   host.removeMovieClip();
};
