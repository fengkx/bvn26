_root.aiHeld = {};
_root.aiKeyDown = function(code)
{
   var held = _root.aiHeld[code] == true;
   _root.aiEvent("key_read", String(this) + "," + code + "," + held);
   return held;
};
p1selt = "手鞠";
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
fighterDir = "file:///Users/fengkx/me/agent-code/bvn2_6-shouju/evidence/characters/shouju/probe-r01/game/fighter/";
fzDir = "file:///Users/fengkx/me/agent-code/bvn2_6-shouju/evidence/characters/shouju/probe-r01/game/fighter/fz/";
musicDir = "file:///Users/fengkx/me/agent-code/bvn2_6-shouju/evidence/characters/shouju/probe-r01/game/music/";
_root.aiEvent("boot", "vs_com,minren,yihu,AI=5");
_root.aiEvent("input_bindings", "w=" + w + "," + "a=" + a + "," + "l=" + l + "," + "上箭=" + 上箭 + "," + "下箭=" + 下箭 + "," + "左箭=" + 左箭 + "," + "右箭=" + 右箭 + "," + "N1=" + N1 + "," + "N2=" + N2 + "," + "N3=" + N3 + "," + "N4=" + N4 + "," + "N5=" + N5 + "," + "N6=" + N6 + "," + "right=" + d + ",attack=" + j + ",down=" + s + ",ranged=" + u + ",jump=" + k + ",special=" + i + ",summon=" + o);

stop();
_root.aiFixtureLoader = new LoadVars();
_root.aiFixtureLoader.onLoad = function(ok)
{
   if(!ok) { trace("MOVE_FIXTURE_LOAD_FAILED"); fscommand("quit"); return; }
   _root.aiFixture = this;
   _root.aiRun = this.run_id;
   _root.aiSeq = 0;
   _root.aiEvent("boot", "move_case," + this.case_id);
   _root.aiEvent("input_bindings", "w=" + w + "," + "a=" + a + "," + "l=" + l + "," + "上箭=" + 上箭 + "," + "下箭=" + 下箭 + "," + "左箭=" + 左箭 + "," + "右箭=" + 右箭 + "," + "N1=" + N1 + "," + "N2=" + N2 + "," + "N3=" + N3 + "," + "N4=" + N4 + "," + "N5=" + N5 + "," + "N6=" + N6 + "," + "right=" + d + ",attack=" + j + ",down=" + s + ",ranged=" + u + ",jump=" + k + ",special=" + i + ",summon=" + o);
   _root.gotoAndStop("游戏场景");
};
_root.aiFixtureLoader.load("file:///Users/fengkx/me/agent-code/bvn2_6-shouju/evidence/characters/shouju/probe-r01/case.txt");

onEnterFrame = function()
{
   if(_root.aiFixture == undefined) return;
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
      _root.game.p2.mc.gotoAndPlay("站立");
      _root.game.p1._x = Number(aiFixture.p1x);
      _root.game.p2._x = Number(aiFixture.p2x);
      _root.game.p1.mc.ql = Number(aiFixture.p1energy);
      _root.game.p2.mc.ql = Number(aiFixture.p2energy);
      aiWindows = aiFixture.windows.split(";");
   }
   if(aiFixture != undefined && aiFixture.resource_interventions != undefined && aiFixture.resource_interventions != "")
   {
      var aiInterventions = aiFixture.resource_interventions.split(";");
      for(var aiInterventionIndex = 0; aiInterventionIndex < aiInterventions.length; aiInterventionIndex++)
      {
         var aiIntervention = aiInterventions[aiInterventionIndex].split(":");
         if(aiFight == Number(aiIntervention[0]))
         {
            var aiTarget = aiIntervention[1] == "p1" ? _root.game.p1 : _root.game.p2;
            var aiPrevious = aiTarget.mc.ql;
            aiTarget.mc.ql = Number(aiIntervention[3]);
            _root.aiEvent("resource_intervention", aiIntervention[4] + "," + aiFight + "," + aiIntervention[1] + "," + aiIntervention[2] + "," + _root.aiNumber(aiPrevious) + "," + _root.aiNumber(aiTarget.mc.ql));
         }
      }
   }
   aiHeld = {};
   if(aiFight >= 0)
   {
      for(var aiIndex = 0; aiIndex < aiWindows.length; aiIndex++)
      {
         var aiWindow = aiWindows[aiIndex].split(":");
         if(aiFight >= Number(aiWindow[0]) && aiFight < Number(aiWindow[1]))
            aiHeld[_root[aiWindow[2]]] = true;
      }
   }

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
   if(aiFight >= 360)
   {
      aiEvent("done", "");
      fscommand("quit");
   }
   if(aiDisplay > 360 + 900)
   {
      aiEvent("timeout", "ready=" + _menuEnabled + ",loaded=" + p2loaded);
      fscommand("quit");
   }
};
