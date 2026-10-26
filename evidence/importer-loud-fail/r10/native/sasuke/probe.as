_root.zhanting=true;
function initCtrl(ai)
{
   useAI = ai;
   mc.initCtrl();
}
function updateGJL()
{
   trace("updateGJL");
   _curGJL = _this["gjl" + _this._currentframe];
   var _loc2_ = _this._name != "p1" ? _root.game.p1 : _root.game.p2;
   var _loc3_ = _this._name != "p1" ? _root.game.p1fz : _root.game.p2fz;
   mc.pw = _loc2_["gjl" + _loc2_._currentframe];
   mc.fzpw = _loc3_.gjl;
}
function setColor(cls)
{
   mc.colors = cls;
}
function showdow(rgb)
{
   if(++_si > 1)
   {
      _si = 0;
      return undefined;
   }
   var _loc3_;
   if(rgb != null)
   {
      _loc3_ = new flash.geom.ColorTransform();
      if(!isNaN(rgb.R))
      {
         _loc3_.redOffset = rgb.R;
      }
      if(!isNaN(rgb.G))
      {
         _loc3_.greenOffset = rgb.G;
      }
      if(!isNaN(rgb.B))
      {
         _loc3_.blueOffset = rgb.B;
      }
   }
   _root.shadowEffect(_this,{alphaStart:100,alphaLose:10,colorTransform:_loc3_});
}
function moveX(spd)
{
   _X = _X + spd * scale_X;
}
function moveY(spd)
{
   _Y = _Y + spd;
}
var 中转 = new Array();
var 万解 = false;
var useAI;
var _this = this;
var _curGJL;
var scale_X = 1;
var hitWall = false;
var isNaruto;
var heavy = 2;
var hitTarget = false;
var vecx = 0;
if(_root.zhanting == undefined)
{
   this.unloadMovie();
}
var _si = 0;
stop();
var gjl1 = [];
gjl1.tkpw = 40;
gjl1.tkzl = 2;
gjl1.tkup = -3;
gjl1.tkx = 3;
gjl1.tktm = 500;
gjl1.tkdz = "被打";
gjl1.tzpw = 50;
gjl1.tzzl = 1;
gjl1.tzup = -10;
gjl1.tzx = 1;
gjl1.tztm = 600;
gjl1.tzdz = "被打";
gjl1.k1pw = 20;
gjl1.k1zl = 2;
gjl1.k1up = 0;
gjl1.k1x = 4;
gjl1.k1tm = 300;
gjl1.k1dz = "被打";
gjl1.k2pw = 30;
gjl1.k2zl = 2;
gjl1.k2up = 0;
gjl1.k2x = 4;
gjl1.k2tm = 500;
gjl1.k2dz = "被打";
gjl1.k3pw = 80;
gjl1.k3zl = 6;
gjl1.k3up = 0;
gjl1.k3x = 8;
gjl1.k3tm = 500;
gjl1.k3dz = "被打";
gjl1.kj1pw = 110;
gjl1.kj1zl = 9;
gjl1.kj1up = 0;
gjl1.kj1x = 6;
gjl1.kj1tm = 0;
gjl1.kj1dz = "击飞";
gjl1.kj21pw = 30;
gjl1.kj21zl = 1;
gjl1.kj21up = 0;
gjl1.kj21x = 1;
gjl1.kj21tm = 400;
gjl1.kj21dz = "被打";
gjl1.kj2pw = 80;
gjl1.kj2zl = 9;
gjl1.kj2up = 0;
gjl1.kj2x = 10;
gjl1.kj2tm = 0;
gjl1.kj2dz = "击飞";
gjl1.zh1pw = 40;
gjl1.zh1zl = 2;
gjl1.zh1up = 3;
gjl1.zh1x = 3;
gjl1.zh1tm = 400;
gjl1.zh1dz = "被打";
gjl1.zh12pw = 70;
gjl1.zh12zl = 3;
gjl1.zh12up = 5;
gjl1.zh12x = 5;
gjl1.zh12tm = 0;
gjl1.zh12dz = "击飞";
gjl1.zh2pw = 70;
gjl1.zh2zl = 19;
gjl1.zh2up = 7;
gjl1.zh2x = 7;
gjl1.zh2tm = 500;
gjl1.zh2dz = "被打";
gjl1.zh3pw = 50;
gjl1.zh3zl = 3;
gjl1.zh3up = 7;
gjl1.zh3x = 7;
gjl1.zh3tm = 700;
gjl1.zh3dz = "被打";
gjl1.zh31pw = 60;
gjl1.zh31zl = 3;
gjl1.zh31up = 5;
gjl1.zh31x = 10;
gjl1.zh31tm = 0;
gjl1.zh31dz = "击飞";
gjl1.bspw = 300;
gjl1.bszl = 9;
gjl1.bsup = 0;
gjl1.bsx = 30;
gjl1.bstm = 0;
gjl1.bsdz = "击飞";
gjl1.sbspw = 250;
gjl1.sbszl = 9;
gjl1.sbsup = 10;
gjl1.sbsx = 10;
gjl1.sbstm = 0;
gjl1.sbsdz = "击飞";
gjl1.sbs2pw = 250;
gjl1.sbs2zl = 19;
gjl1.sbs2up = 10;
gjl1.sbs2x = 10;
gjl1.sbs2tm = 0;
gjl1.sbs2dz = "击飞";
gjl1.cbs1pw = 100;
gjl1.cbs1zl = 19;
gjl1.cbs1up = 7;
gjl1.cbs1x = 10;
gjl1.cbs1tm = 800;
gjl1.cbs1dz = "被打";
gjl1.cbs2pw = 50;
gjl1.cbs2zl = 1;
gjl1.cbs2up = 0;
gjl1.cbs2x = 1;
gjl1.cbs2tm = 1000;
gjl1.cbs2dz = "被打";
gjl1.cbs3pw = 55;
gjl1.cbs3zl = 6;
gjl1.cbs3up = -5;
gjl1.cbs3x = 5;
gjl1.cbs3tm = 1000;
gjl1.cbs3dz = "被打";
gjl1.cbspw = 280;
gjl1.cbszl = 7;
gjl1.cbsup = -20;
gjl1.cbsx = 30;
gjl1.cbstm = 0;
gjl1.cbsdz = "击飞";
var gjl2 = [];
gjl2.tkpw = 30;
gjl2.tkzl = 1;
gjl2.tkup = 0;
gjl2.tkx = 1;
gjl2.tktm = 600;
gjl2.tkdz = "被打";
gjl2.tzpw = 120;
gjl2.tzzl = 7;
gjl2.tzup = -5;
gjl2.tzx = 10;
gjl2.tztm = 0;
gjl2.tzdz = "击飞";
gjl2.k1pw = 30;
gjl2.k1zl = 2;
gjl2.k1up = 0;
gjl2.k1x = 4;
gjl2.k1tm = 400;
gjl2.k1dz = "被打";
gjl2.k2pw = 50;
gjl2.k2zl = 3;
gjl2.k2up = 8;
gjl2.k2x = -2;
gjl2.k2tm = 600;
gjl2.k2dz = "被打";
gjl2.kj1pw = 90;
gjl2.kj1zl = 9;
gjl2.kj1up = 2;
gjl2.kj1x = 10;
gjl2.kj1tm = 600;
gjl2.kj1dz = "被打";
gjl2.kj2pw = 30;
gjl2.kj2zl = 5;
gjl2.kj2up = 0;
gjl2.kj2x = -3;
gjl2.kj2tm = 600;
gjl2.kj2dz = "被打";
gjl2.zh1pw = 10;
gjl2.zh1zl = 1;
gjl2.zh1up = 0;
gjl2.zh1x = 20;
gjl2.zh1tm = 400;
gjl2.zh1dz = "被打";
gjl2.zh2pw = 40;
gjl2.zh2zl = 19;
gjl2.zh2up = 2;
gjl2.zh2x = -2;
gjl2.zh2tm = 400;
gjl2.zh2dz = "被打";
gjl2.zh3pw = 100;
gjl2.zh3zl = 6;
gjl2.zh3up = 0;
gjl2.zh3x = -5;
gjl2.zh3tm = 0;
gjl2.zh3dz = "击飞";
gjl2.bspw = 350;
gjl2.bszl = 9;
gjl2.bsup = 0;
gjl2.bsx = 30;
gjl2.bstm = 0;
gjl2.bsdz = "击飞";
gjl2.sbspw = 280;
gjl2.sbszl = 7;
gjl2.sbsup = 8;
gjl2.sbsx = 10;
gjl2.sbstm = 0;
gjl2.sbsdz = "击飞";
gjl2.cbspw = 550;
gjl2.cbszl = 9;
gjl2.cbsup = 8;
gjl2.cbsx = 20;
gjl2.cbstm = 500;
gjl2.cbsdz = "击飞";

var __seq=0;var __tick=0;var __fn;var __old;var __interval;var __deliveries=0;
maxhp=1000;
function __emit(k,v){trace("AIREF|parent-goto-sasuke-a6366947|"+(__seq++)+"|0|"+__tick+"|0|"+k+"|"+v);}
function __deliver(tag,health,paused,invulnerable){
 mc.hp=health;mc.wudi=invulnerable;zhanting=paused;
 __fn();zhanting=true;__emit(tag,mc.hp);
}
onEnterFrame=function(){
 __tick++;
 if(__tick==1){
  __old=mc;__fn=mc.feixue;
  __interval=setInterval(function(){
   zhanting=false;__fn();zhanting=true;
   __emit("interval",mc.hp);
   if(++__deliveries==2){clearInterval(__interval);delete onEnterFrame;__emit("done","ok");fscommand("quit");}
  },1000);
  __deliver("before",500,false,false);
  __deliver("paused",500,true,false);
  __deliver("threshold",200,false,false);
  __deliver("above_threshold",201,false,false);
  __deliver("invulnerable",500,false,true);
 }else if(__tick==2){mc.gotoAndPlay(1232);
 }else if(__tick==3){
  __emit("replaced",mc===__old);
  __deliver("after",600,false,false);
  __deliver("after_paused",600,true,false);
  __deliver("after_threshold",200,false,false);
  __deliver("after_invulnerable",600,false,true);
  var __newLoseHp=mc.loseHp;
  mc.loseHp=function(v){_root.mc.hp-=v*2;};
  __deliver("rebound_method",600,false,false);
  mc.loseHp=__newLoseHp;
  mc.hp=600;mc.wudi=false;
 }
};
