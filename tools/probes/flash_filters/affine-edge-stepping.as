stop();var seq=0;var phase=0;
function emit(k,v){trace("AIREF|RUN|"+(seq++)+"|0|0|0|"+k+"|"+v);}
var source=new flash.display.BitmapData(64,64,true,0xff907808);var blackSource=new flash.display.BitmapData(64,64,false,0);blackSource.draw(source);
for(var y=0;y<64;y++){var row=[];for(var x=0;x<64;x++)row.push(source.getPixel32(x,y),blackSource.getPixel32(x,y));emit("source",y+","+row.join(","));}blackSource.dispose();
var heights=[7,31,127,257];var slopes=[-65,-17,17,65];var phases=[0,0.25];var cases=[];
for(var hi=0;hi<heights.length;hi++)for(var si=0;si<slopes.length;si++)for(var pi=0;pi<phases.length;pi++)cases.push([heights[hi],slopes[si],phases[pi]]);
_root.onEnterFrame=function(){
 var ci=Math.floor(phase/2);var kind=phase%2;var v=cases[ci];var h=v[0];var dx=v[1];var p=v[2];var x0=150+p;var y0=10+p;var points=[x0,y0,x0+19,y0,x0+19+dx,y0+h,x0+dx,y0+h];
 var child=_root.createEmptyMovieClip("child",1);
 if(kind==0)child.beginBitmapFill(source,new flash.geom.Matrix(),true,false);else child.beginFill(0x907808,100);
 child.moveTo(points[0],points[1]);for(var i=2;i<8;i+=2)child.lineTo(points[i],points[i+1]);child.lineTo(points[0],points[1]);child.endFill();
 var local=child.getBounds(child);var cm=child.transform.matrix;
 var left=Math.floor(Math.min(x0,x0+dx))-4;var right=Math.ceil(Math.max(x0+19,x0+19+dx))+4;var top=Math.floor(y0)-4;var bottom=Math.ceil(y0+h)+4;
 var image=new flash.display.BitmapData(512,512,true,0);image.draw(child);var black=new flash.display.BitmapData(512,512,false,0);black.draw(image);var used=image.getColorBoundsRect(0xff000000,0,false);
 emit("case",[phase,ci,kind,h,dx,p].concat(points).concat([local.xMin,local.xMax,local.yMin,local.yMax,cm.a,cm.b,cm.c,cm.d,cm.tx,cm.ty,left,top,right-left,bottom-top,used.x,used.y,used.width,used.height]).join(","));
 for(var y=top;y<bottom;y++){var row=[];for(var x=left;x<right;x++)row.push(image.getPixel32(x,y),black.getPixel32(x,y));emit("row",y+","+row.join(","));}
 image.dispose();black.dispose();child.removeMovieClip();phase++;if(phase==cases.length*2){source.dispose();delete _root.onEnterFrame;emit("done","ok");fscommand("quit");}
};
