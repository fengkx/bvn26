// Analysis-only bootstrap: the original battle loader and AI remain active.
_root.aiRun = "__RUN_ID__";
_root.aiSeq = 0;
_root.aiDisplay = 0;
_root.aiFight = -1;
_root.aiDraw = 0;
_root.aiNativeRandom = Math.random;
_root.aiEvent = function(kind, value)
{
   trace("AIREF|" + aiRun + "|" + (++aiSeq) + "|" + getTimer() + "|" + aiDisplay + "|" + aiFight + "|" + kind + "|" + value);
};
_root.aiRandom = function(site)
{
   var value = _root.aiNativeRandom();
   _root.aiEvent("random", (++_root.aiDraw) + "," + site + "," + value);
   return value;
};
_root.aiPredicate = function(name, receiver, value)
{
   if(receiver._parent._parent.useAI || receiver._parent.useAI)
   {
      _root.aiEvent("predicate", name + "," + receiver + "," + value);
   }
   return value;
};
_root.aiState = function(player)
{
   var f = _root.game[player];
   var m = f.mc;
   _root.aiEvent("state", player + "," + m._currentframe + "," + f._x + "," + f._y + "," + f._xscale + "," + m.动作 + "," + m.hp + "," + m.ql + "," + m.sw + "," + m.touch + "," + m.touchFloor + "," + m.hits + "," + _root.zhanting + "," + m.hstm + "," + m.hurtSkling);
};
_root.aiHeld = {};
Key.isDown = function(code)
{
   return _root.aiHeld[code] == true;
};
p1selt = "鸣人";
p2selt = "一护";
p1sf = "我爱罗";
p2sf = "魂";
curStage = "现世";
modo = 2;
p1cpu = false;
p2cpu = true;
AI = 5;
maxhp = 1000;
maxtime = 60;
fighterDir = "fighter/";
fzDir = "fighter/fz/";
musicDir = "music/";
_root.aiEvent("boot", "vs_com,minren,yihu,AI=5");
gotoAndStop("游戏场景");
onEnterFrame = function()
{
   aiDisplay++;
   if(aiFight < 0 && p2loaded == true && _menuEnabled == true && zhanting == false)
   {
      aiFight = 0;
      aiEvent("ready", "");
   }
   else if(aiFight >= 0)
   {
      aiFight++;
   }
   aiHeld = {};
   // These inputs become visible to the next display callback, as logged.
   if(aiFight >= 90 && aiFight < 150) aiHeld[d] = true;
   if(aiFight >= 110 && aiFight < 200) aiHeld[j] = true;
   if(aiFight >= 210 && aiFight < 260) aiHeld[s] = true;
   if(aiFight >= 280 && aiFight < 320) aiHeld[u] = true;
   if(aiFight >= 340 && aiFight < 345) aiHeld[k] = true;
   if(aiFight >= 350 && aiFight < 390) aiHeld[j] = true;
   if(aiFight >= 430 && aiFight < 435) aiHeld[i] = true;
   if(aiFight >= 470 && aiFight < 475) aiHeld[o] = true;
   if(p2loaded == true)
   {
      aiState("p1");
      aiState("p2");
   }
   if(aiFight >= __FRAMES__)
   {
      aiEvent("done", "");
      fscommand("quit");
   }
   if(aiDisplay > __FRAMES__ + 900)
   {
      aiEvent("timeout", "ready=" + _menuEnabled + ",loaded=" + p2loaded);
      fscommand("quit");
   }
};
