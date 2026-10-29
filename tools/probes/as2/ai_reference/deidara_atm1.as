// Read-only discriminator. Do not repair missing geometry identity/source fields.
_root.aiAtm1Observe = function(phase, mc, site)
{
   if(_root.aiFight < 56 || _root.aiFight > 60) return;
   var helper = _root.game.p1fz;
   _root.aiEvent("atm1_provenance", phase + "," + escape(site) + "," + escape(String(mc)) + "," + (mc != undefined) + "," + mc._currentframe + "," + helper._currentframe + "," + mc.getDepth() + "," + escape(String(mc.__aiGeoId)) + "," + escape(String(mc.__aiGeoSource)) + "," + escape(String(mc.__aiGeoBirth)));
};
_root.aiAtm1StampObserve = function(phase, mc, site)
{
   if(String(mc) == "_level0.game.p1fz" || String(mc) == "_level0.game.p1fz.atm1")
   {
      _root.aiAtm1Observe(phase,mc,site);
   }
};
