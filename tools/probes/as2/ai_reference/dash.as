   if(aiFight == 0)
   {
      clearInterval(_root.airanset);
      var edgeA = _root.createEmptyMovieClip("aiEdgeA", 9000);
      var edgeB = _root.createEmptyMovieClip("aiEdgeB", 9001);
      for(var edge in {a:edgeA,b:edgeB})
      {
         var box = edge == "a" ? edgeA : edgeB;
         box.beginFill(0);
         box.moveTo(0,0);
         box.lineTo(10,0);
         box.lineTo(10,10);
         box.lineTo(0,10);
         box.lineTo(0,0);
         box.endFill();
      }
      var edgeCases = [[10,0],[10,10],[10.05,0],[0,10.05],[9.95,0],[-10,0],[-10,-10]];
      for(var ei = 0; ei < edgeCases.length; ei++)
      {
         edgeB._x = edgeCases[ei][0];
         edgeB._y = edgeCases[ei][1];
         _root.aiEvent("dash_edge", edgeB._x + "," + edgeB._y + "," + edgeA.hitTest(edgeB));
      }
      edgeA.removeMovieClip();
      edgeB.removeMovieClip();
      _root.aiDashStart = -1;
      _root.game.p1.mc.gotoAndPlay("站立");
      _root.game.p2.mc.gotoAndPlay("站立");
      _root.game.p1._x = 300;
      _root.game.p1._xscale = -100;
      _root.game.p1.scale_X = -1;
      _root.game.p2._x = 600;
      _root.game.p2._xscale = -100;
      _root.game.p2.scale_X = -1;
      _root.game.p1.mc.ql = 300;
      _root.game.p2.mc.ql = 300;
      _root.game.p2.mc.goran = 400;
      _root.game.p2.mc.attran = 400;
      _root.game.p2.mc.defran = 400;
      _root.game.p2.mc.jumpran = 400;
      _root.game.p2.mc.bisharan = NaN;
      aiEvent("fixture", "dash:__CASE__;x300/600;energy300/300;neutral CPU;attack10-14");
   }
   if(aiFight >= 0)
   {
      var a = _root.game.p1.mc;
      var b = _root.game.p2.mc;
      var h = _root.game.p1fz;
      if(_root.aiDashStart < 0 && __TRIGGER__)
      {
         _root.aiDashStart = aiFight;
         aiEvent("dash_trigger", "__CASE__");
      }
      var elapsed = aiFight - _root.aiDashStart;
      if(_root.aiDashStart >= 0)
      {
         __DASH_CONTROL__
      }
      var bounds = h.atm1.getBounds(_root.game);
      aiEvent("dash_state", a._currentframe + "," + b._currentframe + "," + b.hp + "," + b.hits + "," + b.canhit + "," + b.dashing + "," + b.dashF + "," + b.ql + "," + _root.game.p2._x + "," + _root.zhanting + "," + h._currentframe + "," + h.atm1._currentframe + "," + bounds.xMin + "," + bounds.xMax + "," + a.fensheng._currentframe + "," + a.sbsatm._currentframe + "," + a.sbs2atm._currentframe + "," + b.bdmn._currentframe);
   }
