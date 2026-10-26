stop();var seq=0;var tick=0;var cases=[{id:"jinye-0-41-1",samples:[0,10,20,23],scale:0.19524852731221515,raster_input_only:true,depth:1,x:265.44847540050284,y:181.45391660013064}];
function emit(k,v){trace("AIREF|component-jinye-374fac05|"+(seq++)+"|0|"+tick+"|0|"+k+"|"+v);}
function clocks(mc,path){emit("clock",path+","+mc._currentframe);for(var k in mc){var c=mc[k];if(typeof(c)=="movieclip" && c._parent==mc){var depth=c.getDepth();if(depth<0)depth+=16384;clocks(c,path+"/"+depth);}}}
function capture(mc,item){
 var b=new flash.display.BitmapData(600,400,false,6316128);var m=new flash.geom.Matrix(item.scale,0,0,item.scale,item.x,item.y);b.draw(mc,m);
 for(var y=0;y<400;y++){var row="";var last=b.getPixel(0,y);var count=1;for(var x=1;x<=600;x++){var pixel=x<600?b.getPixel(x,y):-1;if(pixel==last)count++;else{row+=count.toString(16)+":"+last.toString(16)+",";count=1;last=pixel;}}emit("pixels",item.id+","+y+","+row);}b.dispose();
}
function observe(){for(var i=0;i<cases.length;i++){var mc=_root["case"+i];if(cases[i].raster_input_only){var child=mc.getInstanceAtDepth(cases[i].depth-16384);if(typeof(child)!="movieclip"){emit("input_error",cases[i].id);fscommand("quit");return;}child.filters=[];child.cacheAsBitmap=false;if(tick==0)emit("raster_input",cases[i].id+","+child.filters.length+","+child.cacheAsBitmap);}clocks(mc,cases[i].id);for(var j=0;j<cases[i].samples.length;j++)if(cases[i].samples[j]==tick)capture(mc,cases[i]);}}
for(var i=0;i<cases.length;i++){var mc=_root.attachMovie("case"+i,"case"+i,i+1);mc.gotoAndStop(1);}
observe();
_root.onEnterFrame=function(){tick++;if(tick==10 || tick==20){for(var i=0;i<cases.length;i++)_root["case"+i].gotoAndStop(tick==10?2:1);}observe();if(tick>=100){delete _root.onEnterFrame;emit("done","ok");fscommand("quit");}};
