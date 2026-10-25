stop();var seq=0;
function emit(k,v){trace("AIREF|clipped-half-step-r91|"+(seq++)+"|0|0|0|"+k+"|"+v);}
var widths=[60,256];var scales=[1.23333740234375,3,5,7,1.24481201171875,2];var origins=[0,1,4,15,-4];var id=0;
for(var wi=0;wi<widths.length;wi++){
 var width=widths[wi];var source=new flash.display.BitmapData(width,8,false,0);
 for(var y=0;y<8;y++)for(var x=0;x<width;x++)source.setPixel(x,y,((x%2*255)<<16)|(((x*37+17)%256)<<8)|113);
 for(var y=0;y<8;y++){var values=[width,y];for(var x=0;x<width;x++)values.push(source.getPixel32(x,y));emit("source",values.join(","));}
 var mc=createEmptyMovieClip("leaf",1);mc.beginBitmapFill(source,new flash.geom.Matrix(),false,true);mc.moveTo(0,0);mc.lineTo(width,0);mc.lineTo(width,8);mc.lineTo(0,8);mc.lineTo(0,0);mc.endFill();
 for(var si=0;si<scales.length;si++)for(var oi=0;oi<origins.length;oi++){
  var matrix=new flash.geom.Matrix(scales[si],0,0,1,origins[oi],0);var dest=new flash.display.BitmapData(384,8,true,0);
  for(var x=0;x<384;x++)dest.draw(mc,matrix,undefined,"normal",new flash.geom.Rectangle(x,4,1,1),false);
  var black=new flash.display.BitmapData(384,8,false,0);black.draw(dest);
  var values=[id,width,scales[si],origins[oi],matrix.a,matrix.d,matrix.tx,matrix.ty];
  for(var x=0;x<384;x++)values.push(dest.getPixel32(x,4),black.getPixel32(x,4));emit("case",values.join(","));
  black.dispose();dest.dispose();id++;
 }
 mc.removeMovieClip();source.dispose();
}emit("done","ok");fscommand("quit");
