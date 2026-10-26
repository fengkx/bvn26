stop();var seq=0;var tick=0;var samples=SAMPLES;
function emit(k,v){trace("AIREF|RUN|"+(seq++)+"|0|"+tick+"|0|"+k+"|"+v);}
function clocks(mc,path){emit("clock",path+","+mc._currentframe);for(var k in mc){var c=mc[k];if(typeof(c)=="movieclip" && c._parent==mc){var depth=c.getDepth();if(depth<0)depth+=16384;clocks(c,path+"/"+depth);}}}
function capture(label,mc,child,matrix){
 var filters=child.filters;var values=[label,child._currentframe,child.cacheAsBitmap,filters.length];
 for(var i=0;i<filters.length;i++)values.push(filters[i].blurX,filters[i].blurY,filters[i].quality);
 emit("props",values.join(","));
 var image=new flash.display.BitmapData(600,400,true,0);image.draw(mc,matrix);var black=new flash.display.BitmapData(600,400,false,0);black.draw(image);
 for(var y=0;y<400;y++){var row=[];for(var x=0;x<600;x++)row.push(image.getPixel32(x,y),black.getPixel32(x,y));emit("row",label+","+y+","+row.join(","));}
 image.dispose();black.dispose();
}
var mc=_root.attachMovie("case0","source",1);mc.gotoAndStop(1);
function observe(){
 clocks(mc,"CASE_ID");var selected=false;for(var i=0;i<samples.length;i++)if(samples[i]==tick)selected=true;if(!selected)return;
 var child=mc.getInstanceAtDepth(DEPTH-16384);
 if(typeof(child)!="movieclip"){emit("error","missing authored child");delete _root.onEnterFrame;fscommand("quit");return;}
 var draw=new flash.geom.Matrix(SCALE,0,0,SCALE,ORIGIN_X,ORIGIN_Y);var cm=child.transform.matrix;var bounds=child.getBounds(child);
 emit("matrix",[tick,draw.a,draw.d,draw.tx,draw.ty,cm.a,cm.d,cm.tx,cm.ty,bounds.xMin,bounds.yMin,bounds.xMax,bounds.yMax].join(","));
 var filters=child.filters;var cached=child.cacheAsBitmap;var frame=child._currentframe;
 capture(tick+"-authored",mc,child,draw);
 child.filters=[];child.cacheAsBitmap=false;capture(tick+"-clear",mc,child,draw);
 child.cacheAsBitmap=true;capture(tick+"-cache",mc,child,draw);
 child.filters=filters;child.cacheAsBitmap=cached;
 emit("restore",[tick,frame,child._currentframe,child.cacheAsBitmap,child.filters.length].join(","));
}
observe();
_root.onEnterFrame=function(){tick++;if(tick==10 || tick==20)mc.gotoAndStop(tick==10?2:1);observe();if(tick>=MAX_TICK){delete _root.onEnterFrame;emit("done","ok");fscommand("quit");}};
