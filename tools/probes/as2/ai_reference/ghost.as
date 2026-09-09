   if(aiFight == 0)
   {
      clearInterval(_root.airanset);
      _root.game.p1.mc.gotoAndPlay("站立");
      _root.game.p2.mc.gotoAndPlay("站立");
      _root.game.p1._x = 300;
      _root.game.p2._x = 600;
      _root.game.p1.mc.ql = "__CASE__" == "low" ? 99 : 300;
      _root.game.p2.mc.goran = 400;
      _root.game.p2.mc.attran = 400;
      _root.game.p2.mc.defran = 400;
      _root.game.p2.mc.jumpran = 400;
      _root.game.p2.mc.bisharan = NaN;
   }
   if(aiFight == 10)
   {
      var m = _root.game.p1.mc;
      if("__CASE__" == "hurt")
      {
         m.htx = 0; m.yup = 0; m.time = 0; m.tdtime = 30;
         m.hited = 1; m.hstm = 0;
         m.gotoAndStop("被打");
      }
      else m.gotoAndPlay("砍1");
   }
   if(aiFight >= 0)
   {
      var m = _root.game.p1.mc;
      aiEvent("ghost_state", m._currentframe + "," + m.动作 + "," + m.ql + "," + m.dashing + "," + m.dashF + "," + _root.game.p1._x + "," + _root.game.p1._y + "," + _root.zhanting + "," + m.bs + "," + m.canhit + "," + m.bdmn._currentframe);
   }
   aiHeld = {};
   if((aiFight >= 12 && aiFight < 15) || (aiFight >= 27 && aiFight < 30))
   {
      aiHeld[l] = true;
      if("__CASE__" == "up") aiHeld[w] = true;
      else aiHeld[s] = true;
   }
