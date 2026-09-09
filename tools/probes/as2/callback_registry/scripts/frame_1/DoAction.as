stop();
_root.registryTick = 0;
_root.record = function(kind, obj)
{
   trace("REGISTRY|" + registryTick + "|" + kind + "|" + obj + "|" + obj.token + "|" + obj.getDepth() + "|" + obj._parent.getDepth() + "|" + obj._currentframe);
};
onEnterFrame = function()
{
   registryTick++;
   trace("REGISTRY|" + registryTick + "|root");
   if(registryTick == 2) { trace("REGISTRY|2|op|retain-a2-b2"); a.gotoAndStop(2); b.gotoAndStop(2); }
   if(registryTick == 4) { trace("REGISTRY|4|op|remove-a3"); a.gotoAndStop(3); }
   if(registryTick == 6) { trace("REGISTRY|6|op|recreate-a1"); a.gotoAndStop(1); }
   if(registryTick == 8) { trace("REGISTRY|8|op|swap-depths"); a.swapDepths(b); }
   if(registryTick == 10) { trace("REGISTRY|10|op|retain-b1"); b.gotoAndStop(1); }
   if(registryTick == 12) { trace("REGISTRY|12|op|remove-b3"); b.gotoAndStop(3); }
   if(registryTick == 14) { trace("REGISTRY|14|op|recreate-b1"); b.gotoAndStop(1); }
   if(registryTick == 17) { trace("REGISTRY|17|done"); fscommand("quit"); }
};
