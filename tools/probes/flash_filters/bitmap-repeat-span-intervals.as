stop();var seq=0;
function emit(k,v){trace("AIREF|filter-bitmap-repeat-span-intervals-r31|"+(seq++)+"|0|0|0|"+k+"|"+v);}
var scales=[5,3];var origins=[0,-15];var lengths=[1,3,4,5,6,7,8,9,10,11,12,13,14,15,16];
for(var pattern=0;pattern<6;pattern++) {
 var source=new flash.display.BitmapData(2,2,true,0);
 for(var sy=0;sy<2;sy++)for(var sx=0;sx<2;sx++) {
  var value=pattern<4?(sy*2+sx==pattern?255:0):(pattern==4?sx*255:sy*255);
  source.setPixel32(sx,sy,0xff000000|(value<<16)|(113<<8)|113);
 }
 var wrap=_root.createEmptyMovieClip("wrap",1);var item=wrap.createEmptyMovieClip("item",1);
 item.beginBitmapFill(source,new flash.geom.Matrix(),true,true);
 item.moveTo(-4096,-4096);item.lineTo(32768,-4096);item.lineTo(32768,32768);item.lineTo(-4096,32768);item.endFill();
 for(var ci=0;ci<2;ci++)for(var start=2;start<=8;start++)for(var li=0;li<lengths.length;li++) {
  var length=lengths[li];var target=new flash.display.BitmapData(32,8,false,0);
  target.draw(wrap,new flash.geom.Matrix(scales[ci],0,0,8,-origins[ci],0),null,null,new flash.geom.Rectangle(start,4,length,1));
  var values=[];for(var offset=0;offset<length;offset++)values.push(target.getPixel(start+offset,4));
  emit("interval",pattern+","+ci+","+start+","+length+","+values.join(","));target.dispose();
 }
 wrap.removeMovieClip();source.dispose();
}
emit("done","ok");fscommand("quit");
