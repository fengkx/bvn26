   if(aiFight == 0)
   {
      clearInterval(_root.airanset);
      _root.game.p1._x = 300;
      _root.game.p2._x = __TARGET_X__;
      _root.game.p1.mc.ql = 100;
      _root.game.p2.mc.ql = __TARGET_ENERGY__;
      _root.game.p2.mc.goran = 400;
      _root.game.p2.mc.attran = 400;
      _root.game.p2.mc.defran = 400;
      _root.game.p2.mc.jumpran = 400;
      _root.game.p2.mc.bisharan = NaN;
      aiEvent("fixture", "helper: x300/__TARGET_X__, energy100/__TARGET_ENERGY__, CPU samples400/bisharanNaN, O10-14");
   }
   if(aiFight >= 0)
   {
      var helper = _root.game.p1fz;
      var target = _root.game.p2.mc;
      aiEvent("helper_state", helper._currentframe + "," + helper.attacking + "," + helper.atm1._currentframe + "," + target._currentframe + "," + target.hp + "," + target.hits + "," + _root.zhanting + "," + target.ql);
   }
