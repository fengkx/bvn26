stop();var seq=0;
function emit(k,v){trace("AIREF|filter-bitmap-short-spans-r25|"+(seq++)+"|0|0|0|"+k+"|"+v);}
var scales=[2.5,5,8];var starts=[0,1,3,4,5,17,253];
for(var mode=0;mode<2;mode++) {
 var size=mode==0?1024:2;
 var source=new flash.display.BitmapData(size,size,true,0);
 var alpha=255;
 source.setPixel32(0,0,(alpha<<24)|0xff0000);
 source.setPixel32(1,0,(alpha<<24)|0x00ff00);
 source.setPixel32(0,1,(alpha<<24)|0x0000ff);
 source.setPixel32(1,1,(alpha<<24)|0xffffff);
 for(var span=2;span<size;span*=2)source.copyPixels(source,new flash.geom.Rectangle(0,0,span,2),new flash.geom.Point(span,0));
 for(var span=2;span<size;span*=2)source.copyPixels(source,new flash.geom.Rectangle(0,0,size,span),new flash.geom.Point(0,span));

 var wrap=_root.createEmptyMovieClip("wrap",1);
 var item=wrap.createEmptyMovieClip("item",1);
 item.beginBitmapFill(source,new flash.geom.Matrix(),mode==1,true);
 item.moveTo(0,0);item.lineTo(1024,0);item.lineTo(1024,1024);item.lineTo(0,1024);item.endFill();
 for(var suite=0;suite<2;suite++)for(var si=0;si<scales.length;si++) {
  var scale=scales[si];
  var translations=suite==0?17:2;
  var ycount=suite==0?2:1;
  var xcount=suite==0?6:starts.length;
  var lengths=suite==0?1:8;
  for(var ti=0;ti<translations;ti++)for(var yi=0;yi<ycount;yi++)for(var xi=0;xi<xcount;xi++)for(var length=1;length<=lengths;length++) {
   var tx=suite==0?(ti-8)/8:(ti==0?-0.5:0.75);
   var ty=yi==0?0.25:-0.25;
   var start=suite==0?xi+3:starts[xi];
   var target=new flash.display.BitmapData(272,8,false,0);
   target.draw(wrap,new flash.geom.Matrix(scale,0,0,scale,tx,ty),null,null,new flash.geom.Rectangle(start,4,length,1));
   var row="";
   for(var x=start;x<start+length;x++)row+=","+target.getPixel(x,4);
   emit("short",suite+","+mode+","+scale+","+tx+","+ty+","+start+","+length+row);
   target.dispose();
  }
 }
 wrap.removeMovieClip();source.dispose();
}
emit("done","ok");fscommand("quit");
