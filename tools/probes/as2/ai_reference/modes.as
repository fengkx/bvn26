   if(aiFight == 0)
   {
      clearInterval(_root.airanset);
      _root.game.p1.mc.gotoAndPlay("站立");
      _root.game.p2.mc.gotoAndPlay("站立");
      _root.game.p1._x = 300;
      _root.game.p2._x = 550;
      _root.game.p1.mc.ql = 300;
      _root.game.p2.mc.ql = 300;
   }
   aiHeld = {};
   if(aiFight >= 5 && aiFight < 17) { aiHeld[d] = true; aiHeld[左箭] = true; }
   if(aiFight >= 22 && aiFight < 26) { aiHeld[j] = true; aiHeld[N1] = true; }
   if((aiFight >= 60 && aiFight < 63) || (aiFight >= 80 && aiFight < 83))
   { aiHeld[w] = true; aiHeld[l] = true; aiHeld[下箭] = true; aiHeld[N3] = true; }
   if(aiFight >= 110 && aiFight < 115) { aiHeld[w] = true; aiHeld[i] = true; aiHeld[N3] = true; }
   if(aiFight >= 180 && aiFight < 185) { aiHeld[o] = true; aiHeld[N6] = true; }
