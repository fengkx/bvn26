_root.aiHeld = {};
_root.aiKeyDown = function(code)
{
   var held = _root.aiHeld[code] == true;
   _root.aiEvent("key_read", String(this) + "," + code + "," + held);
   return held;
};
p1selt = "佐助须佐";
p2selt = "一护";
p1sf = "我爱罗";
p2sf = "魂";
curStage = "现世";
modo = 3;
p1cpu = false;
p2cpu = false;
AI = 5;
maxhp = 1000;
maxtime = 60;
fighterDir = "file:///Users/fengkx/me/agent-code/bvn2_6-sasukexz/evidence/characters/sasukexz/probe-visibility-r02/game/fighter/";
fzDir = "file:///Users/fengkx/me/agent-code/bvn2_6-sasukexz/evidence/characters/sasukexz/probe-visibility-r02/game/fighter/fz/";
musicDir = "file:///Users/fengkx/me/agent-code/bvn2_6-sasukexz/evidence/characters/sasukexz/probe-visibility-r02/game/music/";
_root.aiEvent("boot", "vs_com,minren,yihu,AI=5");
_root.aiEvent("input_bindings", "w=" + w + "," + "a=" + a + "," + "l=" + l + "," + "上箭=" + 上箭 + "," + "下箭=" + 下箭 + "," + "左箭=" + 左箭 + "," + "右箭=" + 右箭 + "," + "N1=" + N1 + "," + "N2=" + N2 + "," + "N3=" + N3 + "," + "N4=" + N4 + "," + "N5=" + N5 + "," + "N6=" + N6 + "," + "right=" + d + ",attack=" + j + ",down=" + s + ",ranged=" + u + ",jump=" + k + ",special=" + i + ",summon=" + o);
gotoAndStop("游戏场景");
_root.aiYulongDisplayComplete = false;
onEnterFrame = function()
{
   if(_root.aiYulongDisplayComplete)
   {
      aiEvent("capture_window_closed", "before-next-root-increment");
      _root.onEnterFrame = function() {};
      _root.aiEvent = function() {};
      return;
   }
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
   if(aiFight == 0)
   {
      clearInterval(_root.airanset);
      _root.game.p1.mc.gotoAndPlay("站立");
      _root.game.p1._x = 300.0;
      _root.game.p1.mc.ql = 300.0;
      _root.game.p2.mc.gotoAndPlay("站立");
      _root.game.p2._x = 350.0;
      _root.game.p2.mc.ql = 300.0;
   }
   aiHeld = {};
   if(aiFight >= 10 && aiFight < 13) { aiHeld[s] = true; aiHeld[u] = true; }
   if(aiFight >= 280 && aiFight < 283) { aiHeld[s] = true; aiHeld[u] = true; }
   if(aiFight >= 460 && aiFight < 463) { aiHeld[s] = true; aiHeld[u] = true; }
   if(aiFight >= 170 && aiFight < 235) { aiHeld[左箭] = true; }
   if(aiFight >= 236 && aiFight < 239) { aiHeld[N2] = true; aiHeld[左箭] = true; }
   if(aiFight >= 240 && aiFight < 260) { aiHeld[左箭] = true; }
   if(aiFight >= 380 && aiFight < 435) { aiHeld[右箭] = true; }
   // These inputs become visible to the next display callback, as logged.
   aiEvent("input_next_display", "w=" + aiHeld[w] + "," + "a=" + aiHeld[a] + "," + "l=" + aiHeld[l] + "," + "上箭=" + aiHeld[上箭] + "," + "下箭=" + aiHeld[下箭] + "," + "左箭=" + aiHeld[左箭] + "," + "右箭=" + aiHeld[右箭] + "," + "N1=" + aiHeld[N1] + "," + "N2=" + aiHeld[N2] + "," + "N3=" + aiHeld[N3] + "," + "N4=" + aiHeld[N4] + "," + "N5=" + aiHeld[N5] + "," + "N6=" + aiHeld[N6] + "," + "right=" + aiHeld[d] + ",attack=" + aiHeld[j] + ",down=" + aiHeld[s] + ",ranged=" + aiHeld[u] + ",jump=" + aiHeld[k] + ",special=" + aiHeld[i] + ",summon=" + aiHeld[o]);
   if(p2loaded == true)
   {
      if(!_root.aiGeometryLogged && _root.game.p2.useAI == true && _root.game.p2.mc.AImain._currentframe == 2)
      {
         _root.aiGeometryLogged = true;
         aiGeometry();
      }
      aiState("p1");
      aiHelperState("p1");
      aiState("p2");
      aiHelperState("p2");
   }
   _root.aiDisplaySample();
   if(aiFight >= 600)
   {
      aiEvent("done", "");
      _root.aiYulongDisplayComplete = true;
      fscommand("quit");
   }
   if(aiDisplay > 600 + 900)
   {
      aiEvent("timeout", "ready=" + _menuEnabled + ",loaded=" + p2loaded);
      fscommand("quit");
   }
};

_root.aiGeoStamp(this, "game/main.swf#frame_10/DoAction.as");
