stop();var seq=0;
function emit(k,v){trace("AIREF|filter-bitmap-repeat-pixel-step-r29|"+(seq++)+"|0|0|0|"+k+"|"+v);}
var scales=[1.01,1.7,2.5,3,5,7.99,8,13.3,1.3,6.25];var origins=[0,1,3,7,15,31,63,127,255,511,1023,2047];var edge=[17,223,61,149];
for(var axis=0;axis<2;axis++)for(var corner=0;corner<4;corner++) {
 var source=new flash.display.BitmapData(4,4,true,0);
 for(var sy=0;sy<4;sy++)for(var sx=0;sx<4;sx++)source.setPixel32(sx,sy,0xff000000|(((sy%2*2+sx%2)==corner?255:0)<<16)|(edge[axis==0?sx:sy]<<8)|113);
 var wrap=_root.createEmptyMovieClip("wrap",1);var item=wrap.createEmptyMovieClip("item",1);
 item.beginBitmapFill(source,new flash.geom.Matrix(),true,true);
 item.moveTo(-4096,-4096);item.lineTo(32768,-4096);item.lineTo(32768,32768);item.lineTo(-4096,32768);item.endFill();
 for(var si=0;si<scales.length;si++)for(var oi=0;oi<origins.length;oi++) {
  var scale=scales[si];var origin=origins[oi];var target=new flash.display.BitmapData(axis==0?2060:8,axis==0?8:2060,false,0);var px=axis==0?4+origin:4;var py=axis==0?4:4+origin;
  target.draw(wrap,new flash.geom.Matrix(axis==0?scale:8,0,0,axis==0?8:scale,0,0),null,null,new flash.geom.Rectangle(px,py,1,1));
  emit("step",axis+","+corner+","+scale+","+origin+","+target.getPixel(px,py));target.dispose();
 }
 wrap.removeMovieClip();source.dispose();
}
emit("done","ok");fscommand("quit");
