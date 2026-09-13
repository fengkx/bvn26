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
