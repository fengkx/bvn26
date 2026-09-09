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
fighterDir = "file:///private/tmp/bvn-super-guard-observation/game/fighter/";
fzDir = "file:///private/tmp/bvn-super-guard-observation/game/fighter/fz/";
musicDir = "file:///private/tmp/bvn-super-guard-observation/game/music/";
_root.aiEvent("boot", "vs_com,minren,yihu,AI=5");
_root.aiEvent("input_bindings", "right=" + d + ",attack=" + j + ",down=" + s + ",ranged=" + u + ",jump=" + k + ",special=" + i + ",summon=" + o);
gotoAndStop("游戏场景");

_root.sgNames = ["ichigo_bs","ichigo_sbs","ichigo_cbs","naruto_bs","naruto_sbs","naruto_cbs"];
_root.sgLabels = ["必杀","上必杀","超必杀","必杀","上必杀","超必杀"];
onEnterFrame = function() {
 aiDisplay++;
 if(aiFight < 0 && p2loaded == true && _menuEnabled == true && zhanting == false) aiFight=0;
 else if(aiFight >= 0) aiFight++;
 if(aiFight < 0) return;
 var ci = Math.floor(aiFight / 300);
 var t = aiFight % 300;
 if(ci >= 6) { trace("SG2_DONE"); fscommand("quit"); return; }
 var a = ci < 3 ? game.p2 : game.p1;
 var b = ci < 3 ? game.p1 : game.p2;
 aiHeld = {};
 aiHeld[ci < 3 ? s : 下箭] = true;
 if(t == 0) {
   clearInterval(airanset);
   game.p2.mc.defran=0; game.p2.mc.attran=500; game.p2.mc.goran=500; game.p2.mc.jumpran=500; game.p2.mc.bisharan=500;
   for(var v=1;v<=2;v++) {
     var f=game["p"+v]; f.mc.hp=1000; f.mc.ql=300; f.mc.sw=false;
     f.mc.hits=0; f.mc.hited=0; f.mc.beida=0; f.mc.动作=0; f.mc.canhit=true;
     f.mc.gotoAndPlay("站立");
   }
   a._x=400; b._x=450; a._xscale=100; a.scale_X=1; b._xscale=-100; b.scale_X=-1;
   b._y=a._y;
   b.mc.gotoAndPlay("防御2");
   trace("SG2_START|"+sgNames[ci]+"|"+a._y);
 }
 if(t == 10) { b.mc.gotoAndPlay("防御2"); a.mc.gotoAndPlay(sgLabels[ci]); }
 trace("SG2|"+sgNames[ci]+"|"+t+"|"+a.mc._currentframe+"|"+b.mc._currentframe+"|"+b.mc.hp+"|"+b.mc.hits+"|"+b.mc.动作+"|"+a._x+"|"+a._y+"|"+b._x+"|"+b._y+"|"+zhanting);
};
