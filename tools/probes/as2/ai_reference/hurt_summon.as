   aiHeld = {};
   if(aiFight == 0)
   {
      clearInterval(_root.airanset);
      _root.game.p1._x = 100;
      _root.game.p2._x = 700;
      _root.game.p1.mc.gotoAndPlay("站立");
      _root.game.p2.mc.gotoAndPlay("站立");
   }
   if(aiFight >= 0)
   {
      var m = _root.game.p2.mc;
      m.attran = 0;
      m.bisharan = 400;
      m.defran = 400;
      m.jumpran = 400;
      m.goran = 400;
      if(aiFight == 10 || aiFight == 200)
      {
         m.ql = 300;
         m.gotoAndPlay("招换");
         aiEvent("hurt_summon_fixture", "normal," + aiFight);
      }
      if(aiFight == 100 || aiFight == 300)
      {
         m.ql = 300;
         m.hstm = 0;
         m.jhp = 0;
         m.bdzl = 0;
         m.yup = 0;
         m.htx = 0;
         m.tdtime = 50;
         _root.game.p2._y = _root.floorY - 100;
         m.gotoAndPlay(aiFight == 100 ? "被打" : "击飞");
         m.onBeHit0();
         m.goran = 0;
         m.beidax(aiFight == 300);
         aiEvent("hurt_summon_fixture", "hurt," + aiFight + "," + _root.game.p2.isNaruto);
      }
      aiEvent("hurt_summon_state", m._currentframe + "," + m.ql + "," + m.bs + "," + m.hurtSkling + "," + _root.game.p2._y + "," + _root.game.p2fz._currentframe + "," + _root.game.p2fz.attacking);
   }
