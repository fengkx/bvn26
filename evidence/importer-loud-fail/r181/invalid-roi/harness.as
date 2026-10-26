stop();var seq=0;var phase=0;
function emit(k,v){trace("AIREF|RUN|"+(seq++)+"|0|0|0|"+k+"|"+v);}
var sources=[];var sizes=[[17,13],[137,200]];
for(var si=0;si<2;si++){
 var w=sizes[si][0];var h=sizes[si][1];var source=new flash.display.BitmapData(w,h,true,0xff907808);sources.push(source);
 var black=new flash.display.BitmapData(w,h,false,0);black.draw(source);
 for(var y=0;y<h;y++){var row=[];for(var x=0;x<w;x++)row.push(source.getPixel32(x,y),black.getPixel32(x,y));emit("source",[w,h,y].join(",")+","+row.join(","));}black.dispose();
}
var matrices=[[1,0,0,1],[55446/65536,-34752/65536,34752/65536,55446/65536],[62795/65536,-18755/65536,18755/65536,62795/65536],[1,0,0.5,1],[1,-0.5,0,1],[-1,0,0,1],[1.25,0.375,-0.625,0.875],[0,1,-1,0]];
var shifts=[[0,0,0,0],[0.125,-0.125,0.25,0.75],[0.05,0.15,0.5,0.25],[0.25,0.75,0.75,0.5]];
var cases=[];
for(var mi=0;mi<8;mi++)for(var ti=0;ti<4;ti++){
 var m=matrices[mi];var t=shifts[ti];cases.push([0,m[0],m[1],m[2],m[3],t[0],t[1],32+t[2],32+t[3]]);
}
cases.push([1,55446/65536,-34752/65536,34752/65536,55446/65536,-139.85,-70,328.86899819999996,221.71985064]);
_root.onEnterFrame=function(){
 var ci=Math.floor(phase/2);var kind=phase%2;var v=cases[ci];var w=sizes[v[0]][0];var h=sizes[v[0]][1];var parent=_root.createEmptyMovieClip("parent",1);var child=parent.createEmptyMovieClip("child",1);
 if(kind==0)child.beginBitmapFill(sources[v[0]],new flash.geom.Matrix(),false,false);else child.beginFill(0x907808,100);
 child.moveTo(w,0);child.lineTo(w,h);child.lineTo(0,h);child.lineTo(0,0);child.lineTo(w,0);child.endFill();
 child.transform.matrix=new flash.geom.Matrix(v[1],v[2],v[3],v[4],v[5],v[6]);var cm=child.transform.matrix;var draw=new flash.geom.Matrix(1,0,0,1,v[7],v[8]);
 var xs=[];var ys=[];var corners=[[0,0],[w,0],[w,h],[0,h]];
 for(var pi=0;pi<4;pi++){var p=corners[pi];xs.push(cm.a*p[0]+cm.c*p[1]+cm.tx+draw.tx);ys.push(cm.b*p[0]+cm.d*p[1]+cm.ty+draw.ty);}
 var left=Math.floor(Math.min(xs[0],xs[1],xs[2],xs[3]))-4;var top=Math.floor(Math.min(ys[0],ys[1],ys[2],ys[3]))-4;
 var right=Math.ceil(Math.max(xs[0],xs[1],xs[2],xs[3]))+4;var bottom=Math.ceil(Math.max(ys[0],ys[1],ys[2],ys[3]))+4;
 var image=new flash.display.BitmapData(600,400,true,0);image.draw(parent,draw);var black=new flash.display.BitmapData(600,400,false,0);black.draw(image);
 var used=image.getColorBoundsRect(0xff000000,0,false);
 emit("case",[phase,ci,kind,w,h,cm.a,cm.b,cm.c,cm.d,cm.tx,cm.ty,draw.a,draw.b,draw.c,draw.d,draw.tx,draw.ty,left,top,right-left,bottom-top,used.x,used.y,used.width,used.height].join(","));
 for(var y=top;y<bottom;y++){var row=[];for(var x=left;x<right;x++)row.push(image.getPixel32(x,y),black.getPixel32(x,y));emit("row",y+","+row.join(","));}
 image.dispose();black.dispose();parent.removeMovieClip();phase++;
 if(phase==cases.length*2){for(var si=0;si<sources.length;si++)sources[si].dispose();delete _root.onEnterFrame;emit("done","ok");fscommand("quit");}
};
