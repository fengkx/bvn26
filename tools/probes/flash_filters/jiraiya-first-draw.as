stop();var seq=0;var tick=0;var instances=[];
function emit(k,v){trace("AIREF|RUN|"+(seq++)+"|0|"+tick+"|0|"+k+"|"+v);}
function props(label,child){
 var m=child.transform.matrix;var f=child.filters;var r=[label,typeof(child),child.getDepth(),child._currentframe,child.cacheAsBitmap,f.length,m.a,m.b,m.c,m.d,m.tx,m.ty];
 for(var i=0;i<f.length;i++)r.push(f[i].blurX,f[i].blurY,f[i].quality);
 emit("props",r.join(","));
}
function capture(label,target){
 var m=new flash.geom.Matrix(1,0,0,1,281.549878,212.4046024);
 var b=new flash.display.BitmapData(600,400,true,0);b.draw(target,m);
 var black=new flash.display.BitmapData(600,400,false,0);black.draw(b);
 for(var y=0;y<400;y++){var row=[];for(var x=0;x<600;x++)row.push(b.getPixel32(x,y),black.getPixel32(x,y));emit("row",label+","+y+","+row.join(","));}
 b.dispose();black.dispose();
}
for(var i=0;i<3;i++){
 var mc=_root.attachMovie("case0","source"+i,i+1);mc.gotoAndStop(1);var child=mc.getInstanceAtDepth(27-16384);
 props("initial-"+i,child);
 if(i==1)capture("first-authored",mc);
 if(i==2){var tiny=new flash.display.BitmapData(1,1,true,0);tiny.draw(mc);tiny.dispose();}
 child.filters=[];child.cacheAsBitmap=false;props("cleared-"+i,child);capture("cleared-"+i,mc);instances.push(mc);
}
_root.onEnterFrame=function(){tick++;
 for(var i=0;i<instances.length;i++){var mc=instances[i];var child=mc.getInstanceAtDepth(27-16384);props("next-"+i,child);capture("next-"+i,mc);}
 delete _root.onEnterFrame;emit("done","ok");fscommand("quit");};
