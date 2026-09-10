   if(aiFight == 0) {
      clearInterval(_root.airanset);
      clearInterval(_root.timeset);
      _root.game.p2.mc.goran = 500;
      _root.game.p2.mc.attran = 500;
      _root.game.p2.mc.defran = 500;
      _root.game.p2.mc.jumpran = 500;
      _root.game.p2.mc.bisharan = NaN;
      _root.game.p1.mc.hp = 800;
      _root.game.p2.mc.hp = __HP__;
      _root.maxtime = 30;
      _root.gametime = 1;
      _root.cfgFindTimer = function(mc, depth) {
         if(depth > 5) return;
         for(var key in mc) {
            if(typeof mc[key] == "movieclip" && mc[key]._parent == mc) {
               if(typeof mc[key].time == "function") return mc[key];
               var found = _root.cfgFindTimer(mc[key],depth + 1);
               if(found != undefined) return found;
            }
         }
      };
      _root.cfgTimer = _root.cfgFindTimer(_root,0);
      aiEvent("timeout_timer", String(_root.cfgTimer));
      _root.cfgTimer.time();
   }
   if(aiFight >= 0) aiEvent("timeout_state", _root.timeover._currentframe + "," + _root.gametime + "," + _root.to + "," + _root.p1ws + "," + _root.p2ws + "," + _root.game.p1.mc.sw + "," + _root.game.p2.mc.sw + "," + _root.zhanting + "," + _root.rounds);

   if(aiFight >= 0) {
      aiEvent("timeout_badge_aliases", _root.timeover._currentframe + "," + typeof _root.p1win + "," + typeof _root.p2win + "," + typeof _root.p1win.bzxg + "," + typeof _root.p2win.bzxg);
      var findWin = function(mc, depth) {
         if(depth > 6) return;
         for(var key in mc) {
            if(typeof mc[key] == "movieclip" && mc[key]._parent == mc) {
               if(key == "win") aiEvent("timeout_badge_frame", String(mc[key]) + "," + mc[key]._currentframe);
               else findWin(mc[key], depth + 1);
            }
         }
      };
      findWin(_root.game, 0);
      findWin(_root.xuetiao, 0);
   }
