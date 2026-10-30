_root.s262InitSerial = 0;
_root.s262Init = function(mc, symbol)
{
   _root.s262InitSerial++;
   mc.s262InitSerial = _root.s262InitSerial;
   mc.s262InitDisplay = _root.aiDisplay;
   _root.aiEvent("s262_init", String(mc) + "," + symbol + "," + mc.getDepth() + "," + mc.s262InitSerial + "," + mc.s262InitDisplay);
};
_root.s262Node = function(mc, role, level)
{
   if(typeof(mc) != "movieclip") { return; }
   _root.aiEvent("s262_visual", role + "," + String(mc) + "," + mc.getDepth() + "," + mc._currentframe + "," + mc._totalframes + "," + mc.s262InitSerial + "," + mc.s262InitDisplay + "," + mc._x + "," + mc._y + "," + mc._xscale + "," + mc._yscale + "," + mc._rotation + "," + mc._alpha + "," + mc._visible);
   if(level > 0)
   {
      for(var key in mc)
      {
         if(typeof(mc[key]) == "movieclip" && mc[key]._parent == mc)
         {
            _root.s262Node(mc[key], role + "/" + key, level - 1);
         }
      }
   }
};
_root.s262Snapshot = function()
{
   _root.aiEvent("s262_begin", _root.s258Count);
   _root.s262Node(_root.s258Timer, "timer", 1);
   _root.s262Node(_root.xuetiao, "hud", 5);
   _root.s262Node(_root, "root", 0);
   _root.s262Node(_root.game, "camera", 0);
   _root.aiEvent("s262_end", _root.s258Count);
};
