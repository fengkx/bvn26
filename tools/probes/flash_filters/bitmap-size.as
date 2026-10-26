stop();var seq=0;
function emit(k,v){trace("AIREF|filter-bitmap-size-r23|"+(seq++)+"|0|0|0|"+k+"|"+v);}
var scales=[2.5,3,5,8];var sizes=[2,4,8,16,64,1024];
var phases=[-224,-128,0,128,224];
var positions=[4,7,15,31,63,127,255,383,511];
for(var a=0;a<2;a++)for(var sizeIndex=0;sizeIndex<sizes.length;sizeIndex++) {
 var size=sizes[sizeIndex];
 var source=new flash.display.BitmapData(size,size,true,0);
 var alpha=a==0?255:128;
 source.setPixel32(0,0,(alpha<<24)|0xff0000);
 source.setPixel32(1,0,(alpha<<24)|0x00ff00);
 source.setPixel32(0,1,(alpha<<24)|0x0000ff);
 source.setPixel32(1,1,(alpha<<24)|0xffffff);
 for(var span=2;span<size;span*=2)source.copyPixels(source,new flash.geom.Rectangle(0,0,span,2),new flash.geom.Point(span,0));
 for(var span=2;span<size;span*=2)source.copyPixels(source,new flash.geom.Rectangle(0,0,size,span),new flash.geom.Point(0,span));
 for(var si=0;si<scales.length;si++)for(var pi=0;pi<phases.length;pi++) {
  var scale=scales[si];var phase=phases[pi];
  var wrap=_root.createEmptyMovieClip("wrap",1);
  var item=wrap.createEmptyMovieClip("item",1);
  item.beginBitmapFill(source,new flash.geom.Matrix(),false,true);
  item.moveTo(0,0);item.lineTo(size,0);item.lineTo(size,size);item.lineTo(0,size);item.endFill();
  var target=new flash.display.BitmapData(32,32,false,0);
  target.draw(wrap,new flash.geom.Matrix(scale,0,0,scale,phase/256,-phase/512));
  emit("size",alpha+","+size+","+scale+","+phase+","+target.getPixel(Math.floor(scale),Math.floor(scale)));
  target.dispose();wrap.removeMovieClip();
 }
 source.dispose();
}
emit("done","ok");fscommand("quit");
