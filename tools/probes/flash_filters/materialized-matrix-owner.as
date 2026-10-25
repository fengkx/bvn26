stop();var seq=0;var tick=0;var samples=[0,8];
function emit(k,v){trace("AIREF|RUN|"+(seq++)+"|0|"+tick+"|0|"+k+"|"+v);}
function clocks(mc,path){emit("clock",path+","+mc._currentframe);for(var k in mc){var c=mc[k];if(typeof(c)=="movieclip" && c._parent==mc){var depth=c.getDepth();if(depth<0)depth+=16384;clocks(c,path+"/"+depth);}}}
function pixels(label,image){var black=new flash.display.BitmapData(image.width,image.height,false,0);black.draw(image);emit("size",[label,image.width,image.height].join(","));for(var y=0;y<image.height;y++){var row=[];for(var x=0;x<image.width;x++)row.push(image.getPixel32(x,y),black.getPixel32(x,y));emit("row",label+","+y+","+row.join(","));}black.dispose();}
var mc=_root.attachMovie("case0","source",1);mc.gotoAndStop(1);
function observe(){
 clocks(mc,"CASE_ID");if(tick!=0 && tick!=8)return;
 var child=mc.getInstanceAtDepth(1-16384);var filters=child.filters;var cached=child.cacheAsBitmap;var frame=child._currentframe;var draw=new flash.geom.Matrix(1,0,0,1,DRAW_X,DRAW_Y);var cm=child.transform.matrix;
 emit("props",[frame,cached,filters.length].concat(filters[0].matrix).join(","));emit("matrix",[cm.a,cm.b,cm.c,cm.d,cm.tx,cm.ty,draw.a,draw.b,draw.c,draw.d,draw.tx,draw.ty].join(","));
 var authored=new flash.display.BitmapData(600,400,true,0);authored.draw(mc,draw);pixels("authored",authored);
 child.filters=[];child.cacheAsBitmap=true;var cache=new flash.display.BitmapData(600,400,true,0);cache.draw(mc,draw);pixels("cache",cache);
 var source=new flash.display.BitmapData(CACHE_WIDTH,CACHE_HEIGHT,true,0);source.copyPixels(cache,new flash.geom.Rectangle(CACHE_X,CACHE_Y,CACHE_WIDTH,CACHE_HEIGHT),new flash.geom.Point(0,0));pixels("source",source);
 var applied=new flash.display.BitmapData(CACHE_WIDTH,CACHE_HEIGHT,true,0);applied.applyFilter(source,source.rectangle,new flash.geom.Point(0,0),filters[0]);pixels("apply",applied);
 var holder=_root.createEmptyMovieClip("holder",100);var material=holder.createEmptyMovieClip("material",1);material.attachBitmap(source,1);material.filters=filters;
 var bounds=material.getBounds(material);emit("material",[bounds.xMin,bounds.xMax,bounds.yMin,bounds.yMax,material.cacheAsBitmap,material.filters.length].concat(material.filters[0].matrix).join(","));
 var displayed=new flash.display.BitmapData(CACHE_WIDTH,CACHE_HEIGHT,true,0);displayed.draw(holder);pixels("display",displayed);holder.removeMovieClip();
 child.filters=filters;child.cacheAsBitmap=cached;emit("restore",[frame,child._currentframe,child.cacheAsBitmap,child.filters.length].join(","));
 authored.dispose();cache.dispose();source.dispose();applied.dispose();displayed.dispose();
}
observe();_root.onEnterFrame=function(){tick++;observe();if(tick>=8){delete _root.onEnterFrame;emit("done","ok");fscommand("quit");}};
