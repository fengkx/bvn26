stop();var seq=0;var phase=0;var shifts=[-128,0,128];
function emit(k,v){trace("AIREF|RUN|"+(seq++)+"|0|0|0|"+k+"|"+v);}
function capture(label,mc,child,matrix){
 var filters=child.filters;var values=[label,child.cacheAsBitmap,filters.length];
 for(var i=0;i<filters.length;i++)values.push(filters[i].blurX,filters[i].blurY,filters[i].quality,filters[i].color,filters[i].alpha,filters[i].strength,filters[i].inner,filters[i].knockout);
 emit("props",values.join(","));
 var image=new flash.display.BitmapData(600,400,true,0);image.draw(mc,matrix);
 var black=new flash.display.BitmapData(600,400,false,0);black.draw(image);
 for(var y=0;y<400;y++){var row=[];for(var x=0;x<600;x++)row.push(image.getPixel32(x,y),black.getPixel32(x,y));emit("row",label+","+y+","+row.join(","));}
 image.dispose();black.dispose();
}
_root.onEnterFrame=function(){
 var mc=_root.attachMovie("case0","source",1);mc.gotoAndStop(1);
 var child=mc.getInstanceAtDepth(DEPTH-16384);var shape=child.getInstanceAtDepth(1-16384);
 if(child==undefined){emit("error","missing authored child");delete _root.onEnterFrame;fscommand("quit");return;}
 var draw=new flash.geom.Matrix(SCALE,0,0,SCALE,ORIGIN_X+shifts[phase],ORIGIN_Y);
 var cm=child.transform.matrix;var bounds=child.getBounds(child);
 if(shape==undefined)emit("shape_access",phase+",undefined");
 else {var sm=shape.transform.matrix;emit("shape_access",[phase,sm.a,sm.d,sm.tx,sm.ty].join(","));}
 emit("matrix",[phase,shifts[phase],draw.a,draw.d,draw.tx,draw.ty,cm.a,cm.d,cm.tx,cm.ty,bounds.xMin,bounds.yMin,bounds.xMax,bounds.yMax].join(","));
 capture(phase+"-authored",mc,child,draw);
 child.filters=[];child.cacheAsBitmap=false;capture(phase+"-clear",mc,child,draw);
 child.cacheAsBitmap=true;capture(phase+"-cache",mc,child,draw);
 mc.removeMovieClip();phase++;
 if(phase==shifts.length){delete _root.onEnterFrame;emit("done","ok");fscommand("quit");}
};
