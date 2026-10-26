stop();var seq=0;
function emit(k,v){trace("AIREF|filter-bitmap-phase-extended-r22|"+(seq++)+"|0|0|0|"+k+"|"+v);}
for(var a=0;a<2;a++) {
 var source=new flash.display.BitmapData(2,2,true,0);
 var alpha=a==0?255:128;
 source.setPixel32(0,0,(alpha<<24)|0xff0000);
 source.setPixel32(1,0,(alpha<<24)|0x00ff00);
 source.setPixel32(0,1,(alpha<<24)|0x0000ff);
 source.setPixel32(1,1,(alpha<<24)|0xffffff);
 for(var scaleIndex=0;scaleIndex<4;scaleIndex++) {
  var scale=[2.5,3,5,8][scaleIndex];var row="";
  for(var phase=-256;phase<256;phase++) {
   var wrap=_root.createEmptyMovieClip("wrap",1);
   var item=wrap.createEmptyMovieClip("item",1);
   item.beginBitmapFill(source,new flash.geom.Matrix(),false,true);
   item.moveTo(0,0);item.lineTo(2,0);item.lineTo(2,2);item.lineTo(0,2);item.endFill();
   var target=new flash.display.BitmapData(32,32,false,0);
   target.draw(wrap,new flash.geom.Matrix(scale,0,0,scale,phase/256,-phase/512));
   row+=","+target.getPixel(Math.floor(scale),Math.floor(scale));
   target.dispose();wrap.removeMovieClip();
  }
  emit("phase",alpha+","+scale+row);
 }
 source.dispose();
}
emit("done","ok");fscommand("quit");
