stop();var seq=0;var tick=0;
function emit(k,v){trace("AIREF|RUN|"+(seq++)+"|0|"+tick+"|0|"+k+"|"+v);}
var mc=_root.attachMovie("case0","source",1);mc.gotoAndStop(1);
var child=mc.getInstanceAtDepth(27-16384);
function props(label){
 var m=child.transform.matrix;var f=child.filters;var r=[label,typeof(child),child.getDepth(),child._currentframe,child.cacheAsBitmap,f.length,m.a,m.b,m.c,m.d,m.tx,m.ty];
 for(var i=0;i<f.length;i++)r.push(f[i].blurX,f[i].blurY,f[i].quality);
 emit("props",r.join(","));
}
function capture(label,target,matrix){
 var b=new flash.display.BitmapData(600,400,true,0);b.draw(target,matrix);
 var black=new flash.display.BitmapData(600,400,false,0);black.draw(b);
 for(var y=0;y<400;y++){var row=[];for(var x=0;x<600;x++)row.push(b.getPixel32(x,y),black.getPixel32(x,y));emit("row",label+","+y+","+row.join(","));}
 var gray=new flash.display.BitmapData(600,400,false,6316128);gray.draw(target,matrix);
 for(var y=0;y<400;y++){var row=[];for(var x=0;x<600;x++)row.push(gray.getPixel(x,y));emit("gray",label+","+y+","+row.join(","));}
 b.dispose();black.dispose();gray.dispose();
}
var matrix=new flash.geom.Matrix(1,0,0,1,281.549878,212.4046024);
props("authored");capture("authored",mc,matrix);
child.filters=[];child.cacheAsBitmap=false;props("cleared");capture("cleared",mc,matrix);
var cm=child.transform.matrix.clone();cm.concat(matrix);emit("composed",[cm.a,cm.b,cm.c,cm.d,cm.tx,cm.ty].join(","));
capture("child-draw",child,cm);
child.filters=[new flash.filters.BlurFilter(15,0,3)];props("reassigned");capture("reassigned",mc,matrix);
child.filters=[];child.cacheAsBitmap=false;
_root.onEnterFrame=function(){tick++;props("next-frame");capture("next-frame",mc,matrix);delete _root.onEnterFrame;emit("done","ok");fscommand("quit");};
