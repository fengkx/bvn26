stop();var seq=0;var phase=0;var id=0;
function emit(k,v){trace("AIREF|RUN|"+(seq++)+"|0|0|0|"+k+"|"+v);}
var source=new flash.display.BitmapData(16,16,true,0);
for(var y=0;y<16;y++)for(var x=0;x<16;x++)source.setPixel32(x,y,0xff000000+x*65536+y*256+73);
var blackSource=new flash.display.BitmapData(16,16,false,0);blackSource.draw(source);
for(var y=0;y<16;y++){var row=[];for(var x=0;x<16;x++)row.push(source.getPixel32(x,y),blackSource.getPixel32(x,y));emit("source",y+","+row.join(","));}blackSource.dispose();
var matrices=[[1,0,0,1],[55446/65536,-34752/65536,34752/65536,55446/65536],[62795/65536,-18755/65536,18755/65536,62795/65536],[1,0,0.5,1],[1,0,-0.5,1]];
var positions=[[4,4],[8,8],[12,12]];
_root.onEnterFrame=function(){
 var m=matrices[phase];
 for(var axis=0;axis<2;axis++)for(var step=-64;step<=64;step++){
  var parent=_root.createEmptyMovieClip("parent",1);var child=parent.createEmptyMovieClip("child",1);var delta=step/64;
  var fm=new flash.geom.Matrix(1,0,0,1,axis==0?delta:0,axis==1?delta:0);
  child.beginBitmapFill(source,fm,false,false);child.moveTo(0,0);child.lineTo(16,0);child.lineTo(16,16);child.lineTo(0,16);child.lineTo(0,0);child.endFill();
  child.transform.matrix=new flash.geom.Matrix(m[0],m[1],m[2],m[3],0,0);
  var draw=new flash.geom.Matrix(1,0,0,1,128,128);var cm=child.transform.matrix;
  for(var pi=0;pi<3;pi++){
   var sx=positions[pi][0];var sy=positions[pi][1];var xx=Math.floor(cm.a*sx+cm.c*sy+draw.tx);var yy=Math.floor(cm.b*sx+cm.d*sy+draw.ty);
   var image=new flash.display.BitmapData(256,256,true,0);image.draw(parent,draw,null,null,new flash.geom.Rectangle(xx,yy,1,1));var black=new flash.display.BitmapData(256,256,false,0);black.draw(image);
   emit("sample",[id++,phase,axis,step,pi,cm.a,cm.b,cm.c,cm.d,cm.tx,cm.ty,draw.a,draw.b,draw.c,draw.d,draw.tx,draw.ty,fm.tx,fm.ty,sx,sy,xx,yy,image.getPixel32(xx,yy),black.getPixel32(xx,yy)].join(","));
   image.dispose();black.dispose();
  }
  parent.removeMovieClip();
 }
 phase++;if(phase==matrices.length){source.dispose();delete _root.onEnterFrame;emit("done","ok");fscommand("quit");}
};
