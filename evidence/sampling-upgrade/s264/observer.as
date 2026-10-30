// Analysis only: read existing arguments/results, never invoke collision methods.
_root.s264Query = function(phase, mc, array, player, suffix, result)
{
   if(_root.aiFight < 10 || _root.aiFight > 12) return;
   if(String(mc) != "_level0.game.p1.mc.bdmn") return;
   _root.aiEvent("s264_query", phase + "," + escape(String(mc)) + "," + mc._parent._currentframe + "," + typeof(mc.getHitObj) + "," + typeof(mc.getStgHitObj) + "," + mc._fsArray.length + "," + mc._fzfsArray.length + "," + mc.stgks.length + "," + escape(String(player)) + "," + escape(String(suffix)) + "," + array.length + "," + typeof(result) + "," + escape(String(result)) + "," + mc.__aiGeoId + "," + mc.__aiGeoBirth);
};
