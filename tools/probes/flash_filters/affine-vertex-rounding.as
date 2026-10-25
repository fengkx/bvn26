stop();var seq=0;var phase=0;
function emit(k,v){trace("AIREF|RUN|"+(seq++)+"|0|0|0|"+k+"|"+v);}
var source=new flash.display.BitmapData(64,64,true,0xff907808);var blackSource=new flash.display.BitmapData(64,64,false,0);blackSource.draw(source);
for(var y=0;y<64;y++){var row=[];for(var x=0;x<64;x++)row.push(source.getPixel32(x,y),blackSource.getPixel32(x,y));emit("source",y+","+row.join(","));}blackSource.dispose();
var scales=[1,0.5,-0.5,0.25,-0.25];var cases=[];
for(var si=0;si<scales.length;si++)for(var edge=0;edge<4;edge++)for(var step=-10;step<=10;step++)cases.push([scales[si],edge,step]);
_root.onEnterFrame=function(){
 var ci=Math.floor(phase/2);var kind=phase%2;var v=cases[ci];var scale=v[0];var edge=v[1];var step=v[2];
 var bounds=[8,25,8,21];bounds[edge]+=step/20;var x0=bounds[0];var x1=bounds[1];var y0=bounds[2];var y1=bounds[3];
 var parent=_root.createEmptyMovieClip("parent",1);var child=parent.createEmptyMovieClip("child",1);
 if(kind==0)child.beginBitmapFill(source,new flash.geom.Matrix(),false,false);else child.beginFill(0x907808,100);
 child.moveTo(x1,y0);child.lineTo(x1,y1);child.lineTo(x0,y1);child.lineTo(x0,y0);child.lineTo(x1,y0);child.endFill();
 var local=child.getBounds(child);child.transform.matrix=new flash.geom.Matrix(scale,0,0,scale,0,0);var cm=child.transform.matrix;var draw=new flash.geom.Matrix(1,0,0,1,40,40);
 var left=Math.floor(Math.min(scale*x0+40,scale*x1+40))-4;var right=Math.ceil(Math.max(scale*x0+40,scale*x1+40))+4;
 var top=Math.floor(Math.min(scale*y0+40,scale*y1+40))-4;var bottom=Math.ceil(Math.max(scale*y0+40,scale*y1+40))+4;
 var image=new flash.display.BitmapData(128,128,true,0);image.draw(parent,draw);var black=new flash.display.BitmapData(128,128,false,0);black.draw(image);var used=image.getColorBoundsRect(0xff000000,0,false);
 emit("case",[phase,ci,kind,scale,edge,step,x0,x1,y0,y1,local.xMin,local.xMax,local.yMin,local.yMax,cm.a,cm.b,cm.c,cm.d,cm.tx,cm.ty,draw.a,draw.b,draw.c,draw.d,draw.tx,draw.ty,left,top,right-left,bottom-top,used.x,used.y,used.width,used.height].join(","));
 for(var y=top;y<bottom;y++){var row=[];for(var x=left;x<right;x++)row.push(image.getPixel32(x,y),black.getPixel32(x,y));emit("row",y+","+row.join(","));}
 image.dispose();black.dispose();parent.removeMovieClip();phase++;if(phase==cases.length*2){source.dispose();delete _root.onEnterFrame;emit("done","ok");fscommand("quit");}
};
