stop();var seq=0;
function emit(k,v){trace("AIREF|jiraiya-span-controls-r90|"+(seq++)+"|0|0|0|"+k+"|"+v);}
var sx=1.23333740234375;var sy=1.24481201171875;var ys=[20,21,26,27,28];var txs=[4,4.25];var id=0;
for(var ti=0;ti<txs.length;ti++)for(var pattern=0;pattern<6;pattern++){
 var source=new flash.display.BitmapData(60,58,false,0);
 for(var y=0;y<58;y++)for(var x=0;x<60;x++){
  var red=pattern<4?((y%2)*2+x%2==pattern?255:0):(pattern==4?(x%2)*255:(y%2)*255);
  source.setPixel(x,y,(red<<16)|(113<<8)|113);
 }
 for(var y=0;y<58;y++){var row=[txs[ti],pattern,y];for(var x=0;x<60;x++)row.push(source.getPixel32(x,y));emit("source",row.join(","));}
 var mc=createEmptyMovieClip("leaf",1);var fm=new flash.geom.Matrix(1,0,0,1,0,0.8);
 mc.beginBitmapFill(source,fm,false,true);mc.moveTo(0,0.8);mc.lineTo(60,0.8);mc.lineTo(60,58.8);mc.lineTo(0,58.8);mc.lineTo(0,0.8);mc.endFill();
 var matrix=new flash.geom.Matrix(sx,0,0,sy,txs[ti],4);
 for(var kind=0;kind<2;kind++)for(var left=4;left<(kind==0?8:5);left++)for(var right=76;right<(kind==0?81:77);right++){
  var dest=new flash.display.BitmapData(96,96,true,0);
  if(kind==0)dest.draw(mc,matrix,undefined,"normal",new flash.geom.Rectangle(left,0,right-left,96),false);
  else for(var yi=0;yi<ys.length;yi++)for(var x=70;x<80;x++)dest.draw(mc,matrix,undefined,"normal",new flash.geom.Rectangle(x,ys[yi],1,1),false);
  var black=new flash.display.BitmapData(96,96,false,0);black.draw(dest);
  var values=[id,txs[ti],pattern,kind,left,right,matrix.a,matrix.d,matrix.tx,matrix.ty,fm.tx,fm.ty];
  for(var yi=0;yi<ys.length;yi++)for(var x=70;x<80;x++)values.push(dest.getPixel32(x,ys[yi]),black.getPixel32(x,ys[yi]));
  emit("case",values.join(","));black.dispose();dest.dispose();id++;
 }
 mc.removeMovieClip();source.dispose();
}emit("done","ok");fscommand("quit");
