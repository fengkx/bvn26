// Keep the observer root outside the receiver that the authored goto can remove.
_global.bvnChadRoot = _root;
_global.bvnChadArmed = false;
_global.bvnChadObserve = function(phase, receiver)
{
   var root = _global.bvnChadRoot;
   if(phase == "caller_before" && root.aiFight == 10 && receiver._parent == root.game.p1.mc)
   {
      _global.bvnChadArmed = true;
      _global.bvnChadReceiver = receiver;
      _global.bvnChadParent = receiver._parent;
      _global.bvnChadDepth = receiver.getDepth();
      _global.bvnChadPath = String(receiver);
   }
   if(!_global.bvnChadArmed || root.aiFight < 10 || root.aiFight > 11)
   {
      return;
   }
   var parent = _global.bvnChadParent;
   var saved = _global.bvnChadReceiver;
   var occupant = parent.getInstanceAtDepth(_global.bvnChadDepth);
   root.aiEvent("chad_lifecycle", phase + "," + escape(_global.bvnChadPath) + "," + escape(String(receiver)) + "," + escape(String(saved)) + "," + escape(String(saved._parent)) + "," + saved._currentframe + "," + _global.bvnChadDepth + "," + parent._currentframe + "," + escape(String(occupant)) + "," + (occupant == saved));
};
