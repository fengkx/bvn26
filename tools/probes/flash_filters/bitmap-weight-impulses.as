stop();var seq=0;
function emit(k,v){trace("AIREF|filter-bitmap-weight-impulses-r26|"+(seq++)+"|0|0|0|"+k+"|"+v);}
var scales=[2.5,5,8];var starts=[3,4,5];var lengths=[1,4,5];
var edgeX=[17,223,61,149];var edgeY=[29,197,83,241];
for(var mode=0;mode<2;mode++)for(var corner=0;corner<4;corner++) {
 var size=mode==0?1024:(mode==1?2:4);
 var period=mode<2?2:4;
 var source=new flash.display.BitmapData(size,size,true,0);
 for(var sy=0;sy<period;sy++)for(var sx=0;sx<period;sx++) {
  var red=(sy*2+sx)==corner?255:0;
  var green=mode<2?sy*255:edgeY[sy];
  source.setPixel32(sx,sy,0xff000000|(red<<16)|(green<<8)|113);
 }
 for(var span=period;span<size;span*=2)source.copyPixels(source,new flash.geom.Rectangle(0,0,span,period),new flash.geom.Point(span,0));
 for(var span=period;span<size;span*=2)source.copyPixels(source,new flash.geom.Rectangle(0,0,size,span),new flash.geom.Point(0,span));
 var wrap=_root.createEmptyMovieClip("wrap",1);var item=wrap.createEmptyMovieClip("item",1);
 item.beginBitmapFill(source,new flash.geom.Matrix(),mode==1||mode==3,true);
 item.moveTo(-32,-32);item.lineTo(1024,-32);item.lineTo(1024,1024);item.lineTo(-32,1024);item.endFill();
 for(var si=0;si<scales.length;si++)for(var ti=0;ti<2;ti++)for(var yi=0;yi<2;yi++)for(var xi=0;xi<starts.length;xi++)for(var li=0;li<lengths.length;li++) {
  var scale=scales[si];var tx=ti==0?-0.5:0.75;var ty=yi==0?0.25:-0.25;
  var start=starts[xi];var length=lengths[li];
  var target=new flash.display.BitmapData(272,8,false,0);
  target.draw(wrap,new flash.geom.Matrix(scale,0,0,scale,tx,ty),null,null,new flash.geom.Rectangle(start,4,length,1));
  var row="";for(var x=start;x<start+length;x++)row+=","+target.getPixel(x,4);
  emit("weight",corner+","+mode+","+scale+","+tx+","+ty+","+start+","+length+row);
  target.dispose();
 }
 wrap.removeMovieClip();source.dispose();
}
emit("done","ok");fscommand("quit");
