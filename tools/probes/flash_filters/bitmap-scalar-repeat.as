stop();var seq=0;
function emit(k,v){trace("AIREF|filter-bitmap-scalar-repeat-r24|"+(seq++)+"|0|0|0|"+k+"|"+v);}
var scales=[1.01,1.7,2.5,3,5,7.99,8,13.3];
var phases=[-224,-128,-32,0,32,128,224];
var positions=[4,7,15,31,63,127,255,383,511];
for(var a=0;a<2;a++) {
 var source=new flash.display.BitmapData(2,2,true,0);
 var alpha=a==0?255:128;
 source.setPixel32(0,0,(alpha<<24)|0xff0000);
 source.setPixel32(1,0,(alpha<<24)|0x00ff00);
 source.setPixel32(0,1,(alpha<<24)|0x0000ff);
 source.setPixel32(1,1,(alpha<<24)|0xffffff);
 for(var si=0;si<scales.length;si++)for(var pi=0;pi<phases.length;pi++) {
  var scale=scales[si];var phase=phases[pi];
  var wrap=_root.createEmptyMovieClip("wrap",1);
  var item=wrap.createEmptyMovieClip("item",1);
  item.beginBitmapFill(source,new flash.geom.Matrix(),true,true);
  item.moveTo(0,0);item.lineTo(1024,0);item.lineTo(1024,1024);item.lineTo(0,1024);item.endFill();
  var target=new flash.display.BitmapData(520,520,false,0);
  var row="";
  for(var i=0;i<positions.length;i++) {
   var px=positions[i];var py=Math.floor(px*0.6)+2;
   target.draw(wrap,new flash.geom.Matrix(scale,0,0,scale,phase/256,-phase/512),null,null,new flash.geom.Rectangle(px,py,1,1));
   row+=","+target.getPixel(px,py);
  }
  emit("inverse",alpha+","+scale+","+phase+row);
  target.dispose();wrap.removeMovieClip();
 }
 source.dispose();
}
emit("done","ok");fscommand("quit");
