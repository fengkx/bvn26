stop();var seq=0;var phase=0;var id=0;
function emit(k,v){trace("AIREF|RUN|"+(seq++)+"|0|0|0|"+k+"|"+v);}
var source=new flash.display.BitmapData(16,16,true,0);
for(var y=0;y<16;y++)for(var x=0;x<16;x++)source.setPixel32(x,y,0xff000000+x*65536+y*256+73);
var blackSource=new flash.display.BitmapData(16,16,false,0);blackSource.draw(source);
for(var y=0;y<16;y++){var row=[];for(var x=0;x<16;x++)row.push(source.getPixel32(x,y),blackSource.getPixel32(x,y));emit("source",y+","+row.join(","));}blackSource.dispose();
var matrices=[[1,0,0,1],[55446/65536,-34752/65536,34752/65536,55446/65536],[62795/65536,-18755/65536,18755/65536,62795/65536],[1,0,0.5,1],[1,0,-0.5,1]];
var scales=[1,4,16,64,128];
_root.onEnterFrame=function(){
 var m=matrices[phase];
 for(var si=0;si<scales.length;si++){
  var factor=scales[si];var parent=_root.createEmptyMovieClip("parent",1);var child=parent.createEmptyMovieClip("child",1);
  var fm=new flash.geom.Matrix(factor,0,0,factor,0,0);var extent=16*factor;
  child.beginBitmapFill(source,fm,false,false);child.moveTo(0,0);child.lineTo(extent,0);child.lineTo(extent,extent);child.lineTo(0,extent);child.lineTo(0,0);child.endFill();
  child.transform.matrix=new flash.geom.Matrix(m[0]/factor,m[1]/factor,m[2]/factor,m[3]/factor,0,0);
  var draw=new flash.geom.Matrix(1,0,0,1,128,128);var cm=child.transform.matrix;var bounds=child.getBounds(child);
  var image=new flash.display.BitmapData(256,256,true,0);image.draw(parent,draw);var black=new flash.display.BitmapData(256,256,false,0);black.draw(image);var used=image.getColorBoundsRect(0xff000000,0,false);
  emit("case",[id++,phase,factor,cm.a,cm.b,cm.c,cm.d,cm.tx,cm.ty,fm.a,fm.b,fm.c,fm.d,fm.tx,fm.ty,draw.a,draw.b,draw.c,draw.d,draw.tx,draw.ty,bounds.xMin,bounds.yMin,bounds.xMax,bounds.yMax,used.x,used.y,used.width,used.height].join(","));
  for(var y=96;y<160;y++){var row=[];for(var x=96;x<160;x++)row.push(image.getPixel32(x,y),black.getPixel32(x,y));emit("row",y+","+row.join(","));}
  image.dispose();black.dispose();parent.removeMovieClip();
 }
 phase++;if(phase==matrices.length){source.dispose();delete _root.onEnterFrame;emit("done","ok");fscommand("quit");}
};
