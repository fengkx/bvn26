// Analysis-only bootstrap: the original battle loader and AI remain active.
_root.aiRun = "__RUN_ID__";
_root.aiSeq = 0;
_root.aiDisplay = 0;
_root.aiFight = -1;
_root.aiDraw = 0;
_root.aiClockDraw = 0;
_root.aiNativeRandom = Math.random;
_root.aiEvent = function(kind, value)
{
   trace("AIREF|" + aiRun + "|" + (++aiSeq) + "|" + getTimer() + "|" + aiDisplay + "|" + aiFight + "|" + kind + "|" + value);
};
_root.aiTimer = function(site)
{
   var value = getTimer();
   _root.aiEvent("clock", (++_root.aiClockDraw) + "," + site + "," + value);
   return value;
};
_root.aiRandom = function(site)
{
   var value = _root.aiNativeRandom();
   _root.aiEvent("random", (++_root.aiDraw) + "," + site + "," + _root.aiNumber(value));
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
   _root.aiEvent("state", player + "," + m._currentframe + "," + _root.aiNumber(f._x) + "," + _root.aiNumber(f._y) + "," + _root.aiNumber(f._xscale) + "," + m.动作 + "," + _root.aiNumber(m.hp) + "," + _root.aiNumber(m.ql) + "," + m.sw + "," + m.touch + "," + m.touchFloor + "," + m.hits + "," + _root.zhanting + "," + m.hstm + "," + m.hurtSkling);
};
_root.aiGeometry = function()
{
   var f = _root.game.p2;
   var m = f.mc;
   var target = _root.game.p1.mc.bdmn;
   var names = ["kanmian","tkanmian","zh1mian","zh2mian","zh3mian","kj1mian","kj2mian","bsmian","sbsmian","cbsmian","tzmian","absmian"];
   _root.aiEvent("geometry_frame", m._currentframe + "," + f._x + "," + f._y + "," + f._xscale);
   var chain = [f,m,m.AImain];
   for(var c = 0; c < chain.length; c++)
   {
      var cm = chain[c].transform.matrix;
      var gm = chain[c].transform.concatenatedMatrix;
      _root.aiEvent("geometry_matrix", c + "," + cm.a + "," + cm.b + "," + cm.c + "," + cm.d + "," + cm.tx + "," + cm.ty + "," + gm.a + "," + gm.b + "," + gm.c + "," + gm.d + "," + gm.tx + "," + gm.ty);
   }
   for(var n = 0; n < names.length; n++)
   {
      var obj = m.AImain[names[n]];
      var bounds = obj.getBounds(f);
      _root.aiEvent("sensor_bounds", names[n] + "," + bounds.xMin + "," + bounds.yMin + "," + bounds.xMax + "," + bounds.yMax + "," + obj.hitTest(target));
      var own = obj.getBounds(obj);
      var sm = obj.transform.matrix;
      _root.aiEvent("sensor_local", names[n] + "," + own.xMin + "," + own.yMin + "," + own.xMax + "," + own.yMax + "," + sm.a + "," + sm.b + "," + sm.c + "," + sm.d + "," + sm.tx + "," + sm.ty);
   }
};
_root.aiHeld = {};
_root.aiKeyDown = function(code)
{
   var held = _root.aiHeld[code] == true;
   _root.aiEvent("key_read", String(this) + "," + code + "," + held);
   return held;
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
fighterDir = "__GAME_URI__/fighter/";
fzDir = "__GAME_URI__/fighter/fz/";
musicDir = "__GAME_URI__/music/";
_root.aiEvent("boot", "vs_com,minren,yihu,AI=5");
_root.aiEvent("input_bindings", "right=" + d + ",attack=" + j + ",down=" + s + ",ranged=" + u + ",jump=" + k + ",special=" + i + ",summon=" + o);
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
   aiEvent("input_next_display", "right=" + aiHeld[d] + ",attack=" + aiHeld[j] + ",down=" + aiHeld[s] + ",ranged=" + aiHeld[u] + ",jump=" + aiHeld[k] + ",special=" + aiHeld[i] + ",summon=" + aiHeld[o]);
   if(p2loaded == true)
   {
      if(!_root.aiGeometryLogged && _root.game.p2.useAI == true && _root.game.p2.mc.AImain._currentframe == 2)
      {
         _root.aiGeometryLogged = true;
         aiGeometry();
      }
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
