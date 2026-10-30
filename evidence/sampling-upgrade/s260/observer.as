// Analysis only: never invoke receiver methods or write receiver state.
_root.s260Observe = function(phase, mc)
{
   if(_root.aiFight < 10 || _root.aiFight > 12) return;
   if(String(mc) != "_level0.game.p1.mc.bdmn") return;
   _root.aiEvent("s260_order", phase + "," + escape(String(mc)) + "," + mc._parent._currentframe + "," + typeof(mc.getHitObj) + "," + typeof(mc.getStgHitObj) + "," + typeof(mc._fsArray) + "," + typeof(mc._fzfsArray) + "," + typeof(mc.stgks) + "," + mc._fsArray.length + "," + mc._fzfsArray.length + "," + mc.stgks.length + "," + mc.__aiGeoId + "," + mc.__aiGeoBirth);
};
