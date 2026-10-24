stop();var seq=0;
function emit(k,v){trace("AIREF|filter-bitmap-repeat-negative-grid-r29|"+(seq++)+"|0|0|0|"+k+"|"+v);}
var deltas=[-16,-4,-1,0,1,4,16];var bases=[-0.5,-1,-1.5];
for(var axis=0;axis<2;axis++)for(var corner=0;corner<4;corner++) {
 var source=new flash.display.BitmapData(2,2,true,0);
 for(var sy=0;sy<2;sy++)for(var sx=0;sx<2;sx++)source.setPixel32(sx,sy,0xff000000|(((sy*2+sx)==corner?255:0)<<16)|(sy*255<<8)|113);
 var wrap=_root.createEmptyMovieClip("wrap",1);var item=wrap.createEmptyMovieClip("item",1);
 item.beginBitmapFill(source,new flash.geom.Matrix(),true,true);
 item.moveTo(-128,-128);item.lineTo(128,-128);item.lineTo(128,128);item.lineTo(-128,128);item.endFill();
 for(var bi=0;bi<bases.length;bi++)for(var di=0;di<deltas.length;di++) {
  var base=bases[bi];var delta=deltas[di];var scale=8+delta/4096;var t=4.5-(base+0.5)*8;
  var target=new flash.display.BitmapData(8,8,false,0);
  target.draw(wrap,new flash.geom.Matrix(axis==0?scale:8,0,0,axis==0?8:scale,axis==0?t:0,axis==0?0:t),null,null,new flash.geom.Rectangle(4,4,1,1));
  emit("negative",axis+","+corner+","+base+","+delta+","+target.getPixel(4,4));target.dispose();
 }
 wrap.removeMovieClip();source.dispose();
}
emit("done","ok");fscommand("quit");
