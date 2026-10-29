// Observe the original target expression; do not substitute an ancestor's pn.
_root.aiK1Observe = function(phase, mc, target)
{
   if(_root.aiFight < 15 || _root.aiFight > 19) return;
   var parent = mc._parent;
   var grandparent = parent._parent;
   _root.aiEvent("k1atm_provenance", phase + "," + escape(String(mc)) + "," + (mc != undefined) + "," + mc._currentframe + "," + escape(String(mc.__aiGeoId)) + "," + escape(String(mc.__aiGeoSource)) + "," + escape(String(mc.__aiGeoBirth)) + "," + escape(String(parent)) + "," + parent._currentframe + "," + parent.pn + "," + escape(String(target)) + "," + (mc._fsArray != undefined) + "," + mc._fsArray.length + "," + escape(String(mc._fsArray)) + "," + (mc._fzfsArray != undefined) + "," + mc._fzfsArray.length + "," + escape(String(mc._fzfsArray)) + "," + (mc.stgks != undefined) + "," + mc.stgks.length + "," + escape(String(mc.stgks)) + "," + typeof(mc.getHitObj) + "," + typeof(mc.getStgHitObj) + "," + escape(String(grandparent)) + "," + grandparent.pn);
};
