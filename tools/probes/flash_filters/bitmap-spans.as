stop();var seq=0;
function emit(k,v){trace("AIREF|filter-bitmap-spans-r24|"+(seq++)+"|0|0|0|"+k+"|"+v);}
var scales=[2.5,8];var widths=[260,520,524,768];var starts=[0,5,17];
var phases=[-224,224];

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
 for(var si=0;si<scales.length;si++)for(var pi=0;pi<phases.length;pi++)for(var wi=0;wi<widths.length;wi++)for(var ci=0;ci<starts.length;ci++) {
  var width=widths[wi];var clipx=starts[ci];
  var scale=scales[si];var phase=phases[pi];
  var wrap=_root.createEmptyMovieClip("wrap",1);
  var item=wrap.createEmptyMovieClip("item",1);
  item.beginBitmapFill(source,new flash.geom.Matrix(),mode==1,true);
  item.moveTo(0,0);item.lineTo(1024,0);item.lineTo(1024,1024);item.lineTo(0,1024);item.endFill();
  var target=new flash.display.BitmapData(width,160,false,0);
  target.draw(wrap,new flash.geom.Matrix(scale,0,0,scale,phase/256,-phase/512),null,null,new flash.geom.Rectangle(clipx,0,width-clipx,160));
  var row="";
  for(var x=16;x<width;x++)row+=","+target.getPixel(x,155);
  emit("span",mode+","+width+","+clipx+","+scale+","+phase+row);
  target.dispose();wrap.removeMovieClip();
 }
 source.dispose();
}
emit("done","ok");fscommand("quit");
