// Analysis only: observe one authored bdmn slot without initializing it.
_root.s256Object = function(role, mc)
{
   _root.aiEvent("s256_object", role + "," + escape(String(mc)) + "," + typeof(mc) + "," + escape(String(mc._parent)) + "," + mc.getDepth() + "," + mc._currentframe + "," + mc._totalframes + "," + typeof(mc.getHitObj) + "," + typeof(mc.getStgHitObj) + "," + mc.__aiGeoId + "," + escape(String(mc.__aiGeoSource)) + "," + mc.__aiGeoBirth + "," + typeof(mc._fsArray) + "," + typeof(mc._fzfsArray) + "," + typeof(mc.stgks));
};
_root.s256Observe = function()
{
   if(_root.aiFight < 10 || _root.aiFight > 12) return;
   var parent = _root.game.p1.mc;
   var named = parent.bdmn;
   var occupant = parent.getInstanceAtDepth(-16355);
   if(_root.aiFight == 10) _root.s256Saved = named;
   _root.aiEvent("s256_identity", parent._currentframe + "," + (named == occupant) + "," + (_root.s256Saved == occupant));
   _root.s256Object("named", named);
   _root.s256Object("depth", occupant);
   _root.s256Object("saved_tick10", _root.s256Saved);
};
