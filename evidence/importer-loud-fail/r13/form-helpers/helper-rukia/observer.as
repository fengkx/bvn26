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
gjl1.tkzl = 4;
gjl1.tkup = -6;
gjl1.tkx = 3;
gjl1.tktm = 600;
gjl1.tkdz = "被打";
gjl1.tzpw = 40;
gjl1.tzzl = 4;
gjl1.tzup = -2;
gjl1.tzx = 2;
gjl1.tztm = 300;
gjl1.tzdz = "被打";
gjl1.k1pw = 30;
gjl1.k1zl = 2;
gjl1.k1up = 0;
gjl1.k1x = 3;
gjl1.k1tm = 300;
gjl1.k1dz = "被打";
gjl1.k2pw = 30;
gjl1.k2zl = 2;
gjl1.k2up = 0;
gjl1.k2x = 3;
gjl1.k2tm = 300;
gjl1.k2dz = "被打";
gjl1.k3pw = 80;
gjl1.k3zl = 3;
gjl1.k3up = 0;
gjl1.k3x = 8;
gjl1.k3tm = 600;
gjl1.k3dz = "被打";
gjl1.kj1pw = 110;
gjl1.kj1zl = 5;
gjl1.kj1up = 0;
gjl1.kj1x = 10;
gjl1.kj1tm = 0;
gjl1.kj1dz = "击飞";
gjl1.kj2pw = 50;
gjl1.kj2zl = 4;
gjl1.kj2up = 10;
gjl1.kj2x = 7;
gjl1.kj2tm = 400;
gjl1.kj2dz = "被打";
gjl1.zh1pw = 40;
gjl1.zh1zl = 4;
gjl1.zh1up = 0;
gjl1.zh1x = 3;
gjl1.zh1tm = 300;
gjl1.zh1dz = "被打";
gjl1.zh2pw = 60;
gjl1.zh2zl = 15;
gjl1.zh2up = 0;
gjl1.zh2x = 0;
gjl1.zh2tm = 1000;
gjl1.zh2dz = "被打";
gjl1.zh3pw = 40;
gjl1.zh3zl = 4;
gjl1.zh3up = 6;
gjl1.zh3x = 3;
gjl1.zh3tm = 300;
gjl1.zh3dz = "被打";
gjl1.bspw = 280;
gjl1.bszl = 5;
gjl1.bsup = 0;
gjl1.bsx = 20;
gjl1.bstm = 0;
gjl1.bsdz = "击飞";
gjl1.sbspw = 240;
gjl1.sbszl = 5;
gjl1.sbsup = -10;
gjl1.sbsx = 15;
gjl1.sbstm = 0;
gjl1.sbsdz = "击飞";
gjl1.cbs1pw = 20;
gjl1.cbs1zl = 4;
gjl1.cbs1up = 0;
gjl1.cbs1x = 1;
gjl1.cbs1tm = 0;
gjl1.cbs1dz = "被打";
gjl1.cbspw = 450;
gjl1.cbszl = 8;
gjl1.cbsup = 15;
gjl1.cbsx = 3;
gjl1.cbstm = 0;
gjl1.cbsdz = "击飞";
var gjl2 = [];
gjl2.tkpw = 40;
gjl2.tkzl = 1;
gjl2.tkup = -5;
gjl2.tkx = 5;
gjl2.tktm = 600;
gjl2.tkdz = "被打";
gjl2.tzpw = 80;
gjl2.tzzl = 7;
gjl2.tzup = 0;
gjl2.tzx = 8;
gjl2.tztm = 0;
gjl2.tzdz = "击飞";
gjl2.k1pw = 30;
gjl2.k1zl = 1;
gjl2.k1up = 0;
gjl2.k1x = 3;
gjl2.k1tm = 300;
gjl2.k1dz = "被打";
gjl2.k2pw = 30;
gjl2.k2zl = 1;
gjl2.k2up = 0;
gjl2.k2x = 1;
gjl2.k2tm = 300;
gjl2.k2dz = "被打";
gjl2.k3pw = 40;
gjl2.k3zl = 1;
gjl2.k3up = 0;
gjl2.k3x = 5;
gjl2.k3tm = 400;
gjl2.k3dz = "被打";
gjl2.k4pw = 60;
gjl2.k4zl = 8;
gjl2.k4up = 0;
gjl2.k4x = 5;
gjl2.k4tm = 500;
gjl2.k4dz = "被打";
gjl2.kj11pw = 15;
gjl2.kj11zl = 4;
gjl2.kj11up = 0;
gjl2.kj11x = 10;
gjl2.kj11tm = 400;
gjl2.kj11dz = "被打";
gjl2.kj1pw = 70;
gjl2.kj1zl = 8;
gjl2.kj1up = 10;
gjl2.kj1x = 0;
gjl2.kj1tm = 800;
gjl2.kj1dz = "被打";
gjl2.kj2pw = 20;
gjl2.kj2zl = 1;
gjl2.kj2up = 0;
gjl2.kj2x = 0;
gjl2.kj2tm = 500;
gjl2.kj2dz = "被打";
gjl2.kj21pw = 80;
gjl2.kj21zl = 8;
gjl2.kj21up = 7;
gjl2.kj21x = 5;
gjl2.kj21tm = 600;
gjl2.kj21dz = "被打";
gjl2.zh1pw = 90;
gjl2.zh1zl = 7;
gjl2.zh1up = 0;
gjl2.zh1x = 5;
gjl2.zh1tm = 0;
gjl2.zh1dz = "击飞";
gjl2.zh2pw = 70;
gjl2.zh2zl = 15;
gjl2.zh2up = 0;
gjl2.zh2x = 0;
gjl2.zh2tm = 1000;
gjl2.zh2dz = "被打";
gjl2.zh3pw = 40;
gjl2.zh3zl = 1;
gjl2.zh3up = 12;
gjl2.zh3x = 6;
gjl2.zh3tm = 600;
gjl2.zh3dz = "被打";
gjl2.zh31pw = 80;
gjl2.zh31zl = 8;
gjl2.zh31up = -10;
gjl2.zh31x = -10;
gjl2.zh31tm = 0;
gjl2.zh31dz = "击飞";
gjl2.bspw = 250;
gjl2.bszl = 5;
gjl2.bsup = 0;
gjl2.bsx = 15;
gjl2.bstm = 0;
gjl2.bsdz = "击飞";
gjl2.sbspw = 250;
gjl2.sbszl = 8;
gjl2.sbsup = 10;
gjl2.sbsx = 10;
gjl2.sbstm = 0;
gjl2.sbsdz = "击飞";
gjl2.cbspw = 500;
gjl2.cbszl = 8;
gjl2.cbsup = 0;
gjl2.cbsx = 20;
gjl2.cbstm = 0;
gjl2.cbsdz = "击飞";

var __seq=0;var __tick=0;
上箭=101;下箭=102;左箭=103;右箭=104;N1=105;N2=106;N3=107;N4=108;N5=109;N6=110;
function __emit(k,v){trace("AIREF|form-helper-rukia-a5ccc6ec|"+(__seq++)+"|0|"+__tick+"|0|"+k+"|"+v);}
function __observe(tag){
 __emit(tag,万解+","+中转.hp+","+中转.ql+","+_y+","+mc.hp+","+mc.ql);
}
onEnterFrame=function(){
 __tick++;
 if(__tick==1){
  mc.hp=671;mc.ql=234;mc.wudi=true;_y=17;
  mc.wankai();__observe("after_call");
 }else if(__tick==2){
  __observe("after_replace");__emit("frames",_currentframe+","+mc._currentframe);
  __emit("keys",mc.上+","+mc.下+","+mc.左+","+mc.右+","+mc.斩+","+mc.跳+","+mc.冲+","+mc.招+","+mc.必杀+","+mc.换);
  __emit("interval",typeof feiint);
  delete onEnterFrame;__emit("done","ok");fscommand("quit");
 }
};
