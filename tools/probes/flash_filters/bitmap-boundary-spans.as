stop();var seq=0;
function emit(k,v){trace("AIREF|filter-bitmap-boundary-spans-r27|"+(seq++)+"|0|0|0|"+k+"|"+v);}
var sizes=[4,8,16];var scales=[5,8];var lengths=[1,5];
for(var mode=0;mode<2;mode++)for(var wi=0;wi<sizes.length;wi++)for(var corner=0;corner<4;corner++) {
 var size=sizes[wi];var source=new flash.display.BitmapData(size,2,true,0);
 for(var sy=0;sy<2;sy++)for(var sx=0;sx<size;sx++) {
  var edge=corner%2==0?size-1:0;
  var red=(sx==edge&&sy==Math.floor(corner/2))?255:0;
  var green=sx==0?17:(sx==size-1?223:61);
  source.setPixel32(sx,sy,0xff000000|(red<<16)|(green<<8)|113);
 }
 var wrap=_root.createEmptyMovieClip("wrap",1);var item=wrap.createEmptyMovieClip("item",1);
 item.beginBitmapFill(source,new flash.geom.Matrix(),mode==1,true);
 item.moveTo(-128,-128);item.lineTo(1024,-128);item.lineTo(1024,1024);item.lineTo(-128,1024);item.endFill();
 for(var si=0;si<scales.length;si++)for(var side=0;side<2;side++)for(var delta=-3;delta<=3;delta++)for(var li=0;li<lengths.length;li++) {
  var scale=scales[si];var anchor=side==0?0:size-1;
  var tx=32.5-(anchor+0.5)*scale;
  var start=32+delta;var length=lengths[li];var target=new flash.display.BitmapData(64,8,false,0);
  target.draw(wrap,new flash.geom.Matrix(scale,0,0,scale,tx,0.25),null,null,new flash.geom.Rectangle(start,4,length,1));
  var row="";for(var x=start;x<start+length;x++)row+=","+target.getPixel(x,4);
  emit("boundary",mode+","+size+","+corner+","+scale+","+side+","+delta+","+length+row);
  target.dispose();
 }
 wrap.removeMovieClip();source.dispose();
}
emit("done","ok");fscommand("quit");
