stop();var seq=0;
function emit(k,v){trace("AIREF|filter-bitmap-origin-sweep-r27|"+(seq++)+"|0|0|0|"+k+"|"+v);}
var scales=[2.5,5,8];var origins=[4,5,8,17,63,127,255,511];
for(var corner=0;corner<4;corner++) {
 var source=new flash.display.BitmapData(1024,2,true,0);
 for(var sy=0;sy<2;sy++)for(var sx=0;sx<2;sx++)source.setPixel32(sx,sy,0xff000000|(((sy*2+sx)==corner?255:0)<<16)|(sy*255<<8)|113);
 for(var span=2;span<1024;span*=2)source.copyPixels(source,new flash.geom.Rectangle(0,0,span,2),new flash.geom.Point(span,0));
 var wrap=_root.createEmptyMovieClip("wrap",1);var item=wrap.createEmptyMovieClip("item",1);
 item.beginBitmapFill(source,new flash.geom.Matrix(),false,true);
 item.moveTo(-1024,-128);item.lineTo(2048,-128);item.lineTo(2048,1024);item.lineTo(-1024,1024);item.endFill();
 for(var si=0;si<scales.length;si++)for(var oi=0;oi<origins.length;oi++)for(var shift=-8;shift<=8;shift++) {
  var scale=scales[si];var origin=origins[oi];var tx=origin-4+shift/8;
  var target=new flash.display.BitmapData(520,8,false,0);
  target.draw(wrap,new flash.geom.Matrix(scale,0,0,scale,tx,0.25),null,null,new flash.geom.Rectangle(origin,4,1,1));
  emit("origin",corner+","+scale+","+origin+","+shift+","+target.getPixel(origin,4));
  target.dispose();
 }
 wrap.removeMovieClip();source.dispose();
}
emit("done","ok");fscommand("quit");
