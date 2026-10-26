stop();var seq=0;var phase=0;var id=0;
function emit(k,v){trace("AIREF|RUN|"+(seq++)+"|0|0|0|"+k+"|"+v);}
var source=new flash.display.BitmapData(128,128,true,0);
for(var y=0;y<128;y++)for(var x=0;x<128;x++)source.setPixel32(x,y,0xff000000+x*65536+y*256+73);
var blackSource=new flash.display.BitmapData(128,128,false,0);blackSource.draw(source);
for(var y=0;y<128;y++){var row=[];for(var x=0;x<128;x++)row.push(source.getPixel32(x,y),blackSource.getPixel32(x,y));emit("source",y+","+row.join(","));}blackSource.dispose();
var matrices=[[1.25,0.375,-0.625,0.875],[0.625,-0.875,0.375,1.25],[0.5,0.25,-0.125,0.75],[1.5,-0.5,0.25,2],[1,0.125,0.25,1],[1,-0.375,-0.625,1],[1,0.75,-0.875,1],[0.75,0.5,-0.5,0.75],[1/3,0.125,-0.25,2/3],[2/3,-1/3,1/3,2/3],[1.25,0,0.375,0.5],[0.5,-0.375,0,1.25],[1.5,0.5,0.25,0.75],[0.75,-0.25,-0.5,1.5],[2,0.125,-0.625,0.5],[0.5,-0.625,0.125,2]];
var origins=[[384,384],[384.25,383.75],[383.5,384.5],[384.75,384.25]];var positions=[8,40,80,112];
_root.onEnterFrame=function(){
 var m=matrices[phase%16];var reflected=phase>=16;var sign=reflected?-1:1;
 for(var oi=0;oi<4;oi++){
  var parent=_root.createEmptyMovieClip("parent",1);var child=parent.createEmptyMovieClip("child",1);
  child.beginBitmapFill(source,new flash.geom.Matrix(),false,false);child.moveTo(0,0);child.lineTo(128,0);child.lineTo(128,128);child.lineTo(0,128);child.lineTo(0,0);child.endFill();
  child.transform.matrix=new flash.geom.Matrix(sign*m[0],sign*m[1],m[2],m[3],0,0);var cm=child.transform.matrix;
  var draw=new flash.geom.Matrix(1,0,0,1,origins[oi][0],origins[oi][1]);
  for(var yi=0;yi<4;yi++)for(var xi=0;xi<4;xi++){
   var sx=positions[xi];var sy=positions[yi];var xx=Math.floor(cm.a*sx+cm.c*sy+draw.tx);var yy=Math.floor(cm.b*sx+cm.d*sy+draw.ty);
   var image=new flash.display.BitmapData(768,768,true,0);image.draw(parent,draw,null,null,new flash.geom.Rectangle(xx,yy,1,1));
   var black=new flash.display.BitmapData(768,768,false,0);black.draw(image);
   emit("sample",[id++,phase,xi,yi,oi,cm.a,cm.b,cm.c,cm.d,cm.tx,cm.ty,draw.a,draw.b,draw.c,draw.d,draw.tx,draw.ty,sx,sy,xx,yy,image.getPixel32(xx,yy),black.getPixel32(xx,yy)].join(","));
   image.dispose();black.dispose();
  }
  parent.removeMovieClip();
 }
 phase++;if(phase==32){source.dispose();delete _root.onEnterFrame;emit("done","ok");fscommand("quit");}
};
