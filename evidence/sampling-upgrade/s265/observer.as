_root.s265Generation = 0;
_root.s265Life = function(mc, phase)
{
   if(phase == "load") { mc.s265Generation = ++_root.s265Generation; }
   _root.aiEvent("s265_life", phase + "," + String(mc) + "," + mc.getDepth() + "," + mc.s265Generation + "," + mc._currentframe);
};
_root.s265Entry = function(mc)
{
   _root.aiEvent("s265_entry", String(mc) + "," + mc.getDepth() + "," + mc.s265Generation + "," + mc._currentframe);
};
_root.s265State = function(phase, mc)
{
   _root.aiEvent("s265_state", phase + "," + String(mc) + "," + mc.getDepth() + "," + mc.s265Generation + "," + mc._currentframe);
};
_root.s265Sample = function()
{
   var timer = _root.s258Timer;
   _root.s265State("sample", timer.个);
   if(_root.aiFight == 0)
   {
      timer.个.duplicateMovieClip("__s265Control", 100001);
      timer.__s265Control._visible = false;
      _root.aiEvent("s265_control", "created");
   }
   if(_root.aiFight == 1)
   {
      _root.s265State("retained_before", timer.__s265Control);
      timer.__s265Control.gotoAndStop(2);
      timer.__s265Control.gotoAndStop(1);
      _root.s265State("retained_after", timer.__s265Control);
   }
   if(_root.aiFight == 2)
   {
      _root.s265State("replace_before", timer.__s265Control);
      timer.__s265Control.removeMovieClip();
      timer.个.duplicateMovieClip("__s265Control", 100001);
      timer.__s265Control._visible = false;
      _root.aiEvent("s265_control", "replaced");
   }
   if(_root.aiFight == 3)
   {
      _root.s265State("replace_after", timer.__s265Control);
      timer.__s265Control.removeMovieClip();
      _root.aiEvent("s265_control", "removed");
   }
   _root.aiEvent("s265_no_encoding", "before");
   _root.s262Snapshot();
   _root.s258Observe("snapshot_before", timer);
   _root.s258Observe("snapshot_after", timer);
   _root.aiEvent("s265_no_encoding", "after");
};
