stop();var seq=0;var phase=0;var id=0;
function emit(k,v){trace("AIREF|RUN|"+(seq++)+"|0|0|0|"+k+"|"+v);}
var source=new flash.display.BitmapData(8,8,true,0);
for(var y=0;y<8;y++)for(var x=0;x<8;x++)source.setPixel32(x,y,4278190080+(16+24*x)*65536+(16+24*y)*256+73);
var blackSource=new flash.display.BitmapData(8,8,false,0);blackSource.draw(source);
for(var y=0;y<8;y++){var row=[];for(var x=0;x<8;x++)row.push(source.getPixel32(x,y),blackSource.getPixel32(x,y));emit("source",y+","+row.join(","));}blackSource.dispose();
var fillx=[-0.15,-0.1,0.05,0.1,0.15,0.35,0.6,0.85];var filly=[-0.15,0,0.35,0.6];var scales=[1,1.25,3,5];var px=[9,11,15];var py=[7,9,11];
_root.onEnterFrame=function(){
 var fx=fillx[phase];
 for(var fi=0;fi<filly.length;fi++)for(var si=0;si<scales.length;si++)for(var xi=0;xi<px.length;xi++)for(var yi=0;yi<py.length;yi++){
  var parent=_root.createEmptyMovieClip("parent",1);var child=parent.createEmptyMovieClip("child",1);var fm=new flash.geom.Matrix(1,0,0,1,fx,filly[fi]);
  child.beginBitmapFill(source,fm,false,true);child.moveTo(0,0);child.lineTo(8,0);child.lineTo(8,8);child.lineTo(0,8);child.lineTo(0,0);child.endFill();child.transform.matrix=new flash.geom.Matrix(scales[si],0,0,scales[si],0,0);
  var cm=child.transform.matrix;var draw=new flash.geom.Matrix(1,0,0,1,8,6);var clip=new flash.geom.Rectangle(px[xi],py[yi],1,1);
  var image=new flash.display.BitmapData(24,24,true,0);image.draw(parent,draw,null,null,clip);var black=new flash.display.BitmapData(24,24,false,0);black.draw(image);
  emit("sample",[id++,fm.a,fm.d,fm.tx,fm.ty,cm.a,cm.d,draw.tx,draw.ty,clip.x,clip.y,clip.width,clip.height,image.getPixel32(clip.x,clip.y),black.getPixel32(clip.x,clip.y)].join(","));
  image.dispose();black.dispose();parent.removeMovieClip();
 }
 phase++;if(phase==fillx.length){delete _root.onEnterFrame;emit("done","ok");fscommand("quit");}
};
