// Analysis-only pass-through: return the same once-evaluated value.
_root.s275Value = function(site, value)
{
   if(_root.aiFight >= 15 && _root.aiFight <= 22)
   {
      _root.aiEvent("s275_value", site + "," + typeof(value) + "," + escape(String(value)) + "," + escape(String(value._parent)) + "," + value._currentframe + "," + value.__aiGeoId + "," + escape(String(value.__aiGeoSource)));
   }
   return value;
};
_root.s275Boundary = function(phase, mc)
{
   if(_root.aiFight < 15 || _root.aiFight > 22) return;
   _root.aiEvent("s275_boundary", phase + "," + escape(String(mc)) + "," + mc._currentframe + "," + mc.__aiGeoId + "," + escape(String(mc._parent)) + "," + escape(String(mc.mian)) + "," + escape(String(mc.getInstanceAtDepth(-16382))) + "," + escape(String(_root.game.p1.mc.getInstanceAtDepth(-16356))) + "," + escape(String(_root.game.p1.mc.k1atm)) + "," + escape(String(_root.game.p1.mc.abcd)));
};
