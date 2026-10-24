stop();var seq=0;
function emit(k,v){trace("AIREF|filter-bitmap-repeat-matrices-r28|"+(seq++)+"|0|0|0|"+k+"|"+v);}
var scales=[1.01,1.7,2.5,5,7.99,8,13.3];var periods=[-128,-1,0,1,128];var fractions=[-0.125,0,0.25,0.5,0.875,1,1.125];
for(var corner=0;corner<4;corner++) {
 var source=new flash.display.BitmapData(2,2,true,0);
 for(var sy=0;sy<2;sy++)for(var sx=0;sx<2;sx++)source.setPixel32(sx,sy,0xff000000|(((sy*2+sx)==corner?255:0)<<16)|(sy*255<<8)|113);
 for(var si=0;si<scales.length;si++)for(var route=0;route<3;route++)for(var pi=0;pi<periods.length;pi++)for(var fi=0;fi<fractions.length;fi++) {
  var scale=scales[si];var period=periods[pi];var fraction=fractions[fi];
  var tx=32.5-(fraction+0.5)*scale;var filltx=0;
  if(route==0)tx-=2*period*scale;
  if(route==1)filltx=-2*period;
  if(route==2){tx=32.5-0.5*scale;filltx=-(2*period+fraction);}
  var ty=32.5-0.85*scale;
  var wrap=_root.createEmptyMovieClip("wrap",1);var item=wrap.createEmptyMovieClip("item",1);
  item.beginBitmapFill(source,new flash.geom.Matrix(1,0,0,1,filltx,0),true,true);
  item.moveTo(-4096,-4096);item.lineTo(4096,-4096);item.lineTo(4096,4096);item.lineTo(-4096,4096);item.endFill();
  var target=new flash.display.BitmapData(64,64,false,0);
  target.draw(wrap,new flash.geom.Matrix(scale,0,0,scale,tx,ty),null,null,new flash.geom.Rectangle(32,32,1,1));
  emit("matrix",corner+","+scale+","+route+","+period+","+fraction+","+target.getPixel(32,32));
  target.dispose();wrap.removeMovieClip();
 }
 source.dispose();
}
emit("done","ok");fscommand("quit");
