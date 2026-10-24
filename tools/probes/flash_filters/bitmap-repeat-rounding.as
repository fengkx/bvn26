stop();var seq=0;
function emit(k,v){trace("AIREF|filter-bitmap-repeat-rounding-r30|"+(seq++)+"|0|0|0|"+k+"|"+v);}
var sizes=[2,4,8,16];var origins=[14,15,16];var pixels=[3,4,5];
for(var ni=0;ni<sizes.length;ni++)for(var axis=0;axis<2;axis++)for(var corner=0;corner<4;corner++) {
 var size=sizes[ni];var source=new flash.display.BitmapData(size,size,true,0);
 for(var sy=0;sy<size;sy++)for(var sx=0;sx<size;sx++)source.setPixel32(sx,sy,0xff000000|(((sy%2*2+sx%2)==corner?255:0)<<16)|(((axis==0?sx:sy)*37+17)%256<<8)|113);
 var wrap=_root.createEmptyMovieClip("wrap",1);var item=wrap.createEmptyMovieClip("item",1);
 item.beginBitmapFill(source,new flash.geom.Matrix(),true,true);
 item.moveTo(-4096,-4096);item.lineTo(32768,-4096);item.lineTo(32768,32768);item.lineTo(-4096,32768);item.endFill();
 for(var oi=0;oi<origins.length;oi++)for(var pi=0;pi<pixels.length;pi++) {
  var origin=origins[oi];var pixel=pixels[pi];var px=axis==0?pixel:4;var py=axis==0?4:pixel;var target=new flash.display.BitmapData(8,8,false,0);
  target.draw(wrap,new flash.geom.Matrix(axis==0?3:8,0,0,axis==0?8:3,axis==0?-origin:0,axis==0?0:-origin),null,null,new flash.geom.Rectangle(px,py,1,1));
  emit("rounding",size+","+axis+","+corner+","+origin+","+pixel+","+target.getPixel(px,py));target.dispose();
 }
 wrap.removeMovieClip();source.dispose();
}
emit("done","ok");fscommand("quit");
