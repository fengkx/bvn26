stop();var seq=0;
function emit(k,v){trace("AIREF|filter-bitmap-transparent-rgba-r32|"+(seq++)+"|0|0|0|"+k+"|"+v);}
var colors=[0xff0000,0x00ff00,0x0000ff,0xffffff];var alphas=[0,64,128,255];
var scales=[3,5,8,1.7];var lengths=[1,4,8,260];
for(var varying=0;varying<2;varying++)for(var repeat=0;repeat<2;repeat++) {
 var source=new flash.display.BitmapData(2,2,true,0);
 for(var c=0;c<4;c++)source.setPixel32(c%2,Math.floor(c/2),((varying?alphas[c]:128)<<24)|colors[c]);
 var wrap=_root.createEmptyMovieClip("wrap",1);var item=wrap.createEmptyMovieClip("item",1);
 item.beginBitmapFill(source,new flash.geom.Matrix(),repeat==1,true);
 item.moveTo(-4096,-4096);item.lineTo(32768,-4096);item.lineTo(32768,32768);item.lineTo(-4096,32768);item.endFill();
 for(var si=0;si<scales.length;si++)for(var start=3;start<=4;start++)for(var li=0;li<lengths.length;li++) {
  var length=lengths[li];var target=new flash.display.BitmapData(300,8,true,0);
  target.draw(wrap,new flash.geom.Matrix(scales[si],0,0,scales[si],-.5,.25),null,null,new flash.geom.Rectangle(start,4,length,1));
  var values=[];for(var offset=0;offset<length;offset++)values.push(target.getPixel32(start+offset,4));
  emit("rgba",varying+","+repeat+","+scales[si]+","+start+","+length+","+values.join(","));target.dispose();
 }
 wrap.removeMovieClip();source.dispose();
}
emit("done","ok");fscommand("quit");
