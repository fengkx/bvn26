stop();var seq=0;
function emit(k,v){trace("AIREF|png-draw-paths-r87|"+(seq++)+"|0|0|0|"+k+"|"+v);}
function dump(stage,b){var black=new flash.display.BitmapData(64,64,false,0);black.draw(b);for(var y=0;y<64;y++){var values="";for(var x=0;x<64;x++)values+=","+b.getPixel32(x,y)+","+black.getPixel32(x,y);emit("row",stage+","+y+values);}black.dispose();}
var target=createEmptyMovieClip("target",1);var loader=new MovieClipLoader();var listener={};
listener.onLoadError=function(mc,error,status){emit("error",error+","+status);fscommand("quit");};
listener.onLoadInit=function(mc){
 emit("loaded",[mc._width,mc._height,mc._xscale,mc._yscale,mc._alpha].join(","));
 var full=new flash.display.BitmapData(64,64,true,0);full.draw(mc,new flash.geom.Matrix(),undefined,"normal",undefined,false);dump("full",full);
 var direct=new flash.display.BitmapData(64,64,false,0);direct.draw(mc,new flash.geom.Matrix(),undefined,"normal",undefined,false);dump("direct_black",direct);direct.dispose();
 var clipped=new flash.display.BitmapData(64,64,true,0);
 for(var y=0;y<64;y++)for(var x=0;x<64;x++)clipped.draw(mc,new flash.geom.Matrix(),undefined,"normal",new flash.geom.Rectangle(x,y,1,1),false);
 dump("single_clip",clipped);clipped.dispose();
 var redraw=new flash.display.BitmapData(64,64,true,0);redraw.draw(full);dump("redraw",redraw);redraw.dispose();
 full.dispose();emit("done","ok");fscommand("quit");
};loader.addListener(listener);loader.loadClip("probe.png",target);
