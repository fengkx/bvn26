stop();var seq=0;var phase=0;var id=0;
function emit(k,v){trace("AIREF|RUN|"+(seq++)+"|0|0|0|"+k+"|"+v);}
var source=new flash.display.BitmapData(16,16,true,0);
for(var y=0;y<16;y++)for(var x=0;x<16;x++)source.setPixel32(x,y,0xff000000+x*65536+y*256+73);
var blackSource=new flash.display.BitmapData(16,16,false,0);blackSource.draw(source);
for(var y=0;y<16;y++){var row=[];for(var x=0;x<16;x++)row.push(source.getPixel32(x,y),blackSource.getPixel32(x,y));emit("source",y+","+row.join(","));}blackSource.dispose();
var scales=[3,5,7,13,-3,-5,-7,-13];var positions=[4,8,12];var targets=[0,1,7,16,31,63];var deltas=[-0.5,-0.25,0,0.25,0.5];
_root.onEnterFrame=function(){
 var axis=Math.floor(phase/8);var scale=scales[phase%8];
 var parent=_root.createEmptyMovieClip("parent",1);var child=parent.createEmptyMovieClip("child",1);
 child.beginBitmapFill(source,new flash.geom.Matrix(),false,false);child.moveTo(0,0);child.lineTo(16,0);child.lineTo(16,16);child.lineTo(0,16);child.lineTo(0,0);child.endFill();
 child.transform.matrix=new flash.geom.Matrix(axis==0?scale:1,0,0,axis==1?scale:1,0,0);var cm=child.transform.matrix;
 for(var pi=0;pi<3;pi++)for(var ti=0;ti<6;ti++)for(var di=0;di<5;di++){
  var sx=positions[pi];var sy=positions[pi];var xx=targets[ti];var yy=targets[ti];var delta=deltas[di];
  var draw=new flash.geom.Matrix(1,0,0,1,xx+0.5-cm.a*sx+(axis==0?delta:0),yy+0.5-cm.d*sy+(axis==1?delta:0));
  var image=new flash.display.BitmapData(128,128,true,0);image.draw(parent,draw,null,null,new flash.geom.Rectangle(xx,yy,1,1));var black=new flash.display.BitmapData(128,128,false,0);black.draw(image);
  emit("sample",[id++,phase,pi,ti,di,cm.a,cm.b,cm.c,cm.d,cm.tx,cm.ty,draw.a,draw.b,draw.c,draw.d,draw.tx,draw.ty,sx,sy,xx,yy,image.getPixel32(xx,yy),black.getPixel32(xx,yy)].join(","));
  image.dispose();black.dispose();
 }
 parent.removeMovieClip();phase++;if(phase==16){source.dispose();delete _root.onEnterFrame;emit("done","ok");fscommand("quit");}
};
