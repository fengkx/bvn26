stop();var seq=0;
function emit(k,v){trace("AIREF|png-byte-decode-r86|"+(seq++)+"|0|0|0|"+k+"|"+v);}
var target=createEmptyMovieClip("target",1);var loader=new MovieClipLoader();var listener={};
listener.onLoadError=function(mc,error,status){emit("error",error+","+status);fscommand("quit");};
listener.onLoadInit=function(mc){
 emit("loaded",[mc._width,mc._height,mc._xscale,mc._yscale,mc._alpha].join(","));
 var b=new flash.display.BitmapData(256,768,true,0);b.draw(mc,new flash.geom.Matrix(),undefined,"normal",undefined,false);
 var black=new flash.display.BitmapData(256,768,false,0);black.draw(b);
 for(var y=0;y<768;y++){var values="";for(var x=0;x<256;x++)values+=","+b.getPixel32(x,y)+","+black.getPixel32(x,y);emit("row",y+values);}
 b.dispose();black.dispose();emit("done","ok");fscommand("quit");
};loader.addListener(listener);loader.loadClip("probe.png",target);
