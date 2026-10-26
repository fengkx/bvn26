stop();
var seq=0;var phase=0;var id=0;var caseId=0;
function emit(k,v){trace("AIREF|RUN|"+(seq++)+"|0|0|0|"+k+"|"+v);}
var source=new flash.display.BitmapData(16,16,true,0);
for(var y=0;y<16;y++)for(var x=0;x<16;x++)source.setPixel32(x,y,0xff000000+x*65536+y*256+73);
var blackSource=new flash.display.BitmapData(16,16,false,0);blackSource.draw(source);
for(var y=0;y<16;y++){
 var row=[];for(var x=0;x<16;x++)row.push(source.getPixel32(x,y),blackSource.getPixel32(x,y));
 emit("source",y+","+row.join(","));
}
blackSource.dispose();
var matrices=[[1,0,0,1],[-1,0,0,1],[1,0,0,-1],[-1,0,0,-1],[-1,0,0.5,1],[-1,0,-0.5,1],[1,0.5,0,-1],[1,-0.5,0,-1],[-1,0.5,0,1],[-1,-0.5,0,1],[1,0,0.5,-1],[1,0,-0.5,-1]];
var positions=[[4,4],[8,8],[12,12]];
function makeChild(parent,m,factor,axis,step){
 var child=parent.createEmptyMovieClip("child",1);
 var fm=new flash.geom.Matrix(factor,0,0,factor,axis==0?step:0,axis==1?step:0);
 child.beginBitmapFill(source,fm,false,false);
 child.moveTo(0,0);child.lineTo(16*factor,0);child.lineTo(16*factor,16*factor);child.lineTo(0,16*factor);child.lineTo(0,0);child.endFill();
 child.transform.matrix=new flash.geom.Matrix(m[0]/factor,m[1]/factor,m[2]/factor,m[3]/factor,0,0);
 return child;
}
_root.onEnterFrame=function(){
 var direction=0;var h=0;var m=matrices[phase];
 var draw=new flash.geom.Matrix(1,0,0,1,128,128);
 for(var fi=0;fi<2;fi++){
  var factor=fi==0?1:64;var parent=_root.createEmptyMovieClip("parent",1);
  var child=makeChild(parent,m,factor,0,0);var cm=child.transform.matrix;
  var image=new flash.display.BitmapData(256,256,true,0);image.draw(parent,draw);
  var black=new flash.display.BitmapData(256,256,false,0);black.draw(image);
  var bounds=image.getColorBoundsRect(0xff000000,0,false);
  emit("case",[caseId++,phase,direction,h,factor,cm.a,cm.b,cm.c,cm.d,cm.tx,cm.ty,bounds.x,bounds.y,bounds.width,bounds.height].join(","));
  for(var yy=96;yy<160;yy++){
   var row=[];for(var xx=96;xx<160;xx++)row.push(image.getPixel32(xx,yy),black.getPixel32(xx,yy));
   emit("row",yy+","+row.join(","));
  }
  image.dispose();black.dispose();parent.removeMovieClip();
 }
 for(var axis=0;axis<2;axis++)for(var step=-64;step<=64;step++){
  var parent=_root.createEmptyMovieClip("parent",1);var child=makeChild(parent,m,64,axis,step);var cm=child.transform.matrix;
  for(var pi=0;pi<3;pi++){
   var sx=positions[pi][0];var sy=positions[pi][1];
   var xx=Math.floor(cm.a*sx*64+cm.c*sy*64+128);var yy=Math.floor(cm.b*sx*64+cm.d*sy*64+128);
   var image=new flash.display.BitmapData(256,256,true,0);image.draw(parent,draw,null,null,new flash.geom.Rectangle(xx,yy,1,1));
   var black=new flash.display.BitmapData(256,256,false,0);black.draw(image);
   emit("sample",[id++,phase,direction,h,axis,step,pi,cm.a,cm.b,cm.c,cm.d,cm.tx,cm.ty,sx,sy,xx,yy,image.getPixel32(xx,yy),black.getPixel32(xx,yy)].join(","));
   image.dispose();black.dispose();
  }
  parent.removeMovieClip();
 }
 phase++;if(phase==matrices.length){source.dispose();delete _root.onEnterFrame;emit("done","ok");fscommand("quit");}
};
