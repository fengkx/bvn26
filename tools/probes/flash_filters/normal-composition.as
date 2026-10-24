stop();var seq=0;
function emit(k,v){trace("AIREF|normal-composition-r36|"+(seq++)+"|0|0|0|"+k+"|"+v);}
function square(p,n,d,c,a){var m=p.createEmptyMovieClip(n,d);m.beginFill(c,a*100/255);m.moveTo(0,0);m.lineTo(8,0);m.lineTo(8,8);m.lineTo(0,8);m.endFill();return m;}
function sample(m){var b=new flash.display.BitmapData(8,8,true,0);var k=new flash.display.BitmapData(8,8,false,0);b.draw(m);k.draw(b);var v=[b.getPixel32(4,4),k.getPixel32(4,4)];b.dispose();k.dispose();return v;}
var palettes=[[0x606060,0x81d3ef,0x46c4ec],[0x000000,0xff8001,0x3366cc],[0xffffff,0x017ffe,0xcc80aa],[0x3355cc,0x80ff01,0x7f0180]];
var bas=[0,1,64,128,254,255];var fas=[0,1,2,63,127,128,254,255];var ops=[0,1,25,50,99,100];
for(var layout=0;layout<3;layout++)for(var pi=0;pi<4;pi++)for(var bi=0;bi<bas.length;bi++)for(var fi=0;fi<fas.length;fi++)for(var oi=0;oi<ops.length;oi++){
 if(layout>0 && (bi%2==0 || fi%2==0 || oi%2==0))continue;
 var inners=layout==0?[100]:[25,50,100];
 for(var ii=0;ii<inners.length;ii++){
 var w=createEmptyMovieClip("w",1);var back=square(w,"back",1,palettes[pi][0],bas[bi]);
 var outer=w.createEmptyMovieClip("outer",2);outer.cacheAsBitmap=true;outer._alpha=ops[oi];
 var inner=outer.createEmptyMovieClip("inner",2);inner.cacheAsBitmap=true;inner._alpha=inners[ii];
 var middle=layout==0?square(outer,"middle",1,palettes[pi][1],0):square(layout==1?outer:inner,"middle",1,palettes[pi][1],128);
 var front=square(inner,"front",2,palettes[pi][2],fas[fi]);
 var row=[layout,pi,bas[bi],fas[fi],ops[oi],inners[ii]];
 row=row.concat(sample(back),sample(middle),sample(front),sample(w));
 emit("normal",row.join(","));w.removeMovieClip();
 }
}
emit("done","ok");fscommand("quit");
