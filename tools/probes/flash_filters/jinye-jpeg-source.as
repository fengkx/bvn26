stop();var seq=0;var y=0;
function emit(k,v){trace("AIREF|RUN|"+(seq++)+"|0|0|0|"+k+"|"+v);}
var source=flash.display.BitmapData.loadBitmap("original_bitmap_55");
if(source==undefined){emit("error","missing original bitmap");fscommand("quit");}
else {
 emit("dimensions",[source.width,source.height,source.transparent].join(","));
 var black=new flash.display.BitmapData(source.width,source.height,false,0);black.draw(source);
 _root.onEnterFrame=function(){for(var batch=0;batch<8 && y<source.height;batch++,y++){var values=[y];for(var x=0;x<source.width;x++)values.push(source.getPixel32(x,y),black.getPixel32(x,y));emit("row",values.join(","));}if(y==source.height){delete _root.onEnterFrame;emit("done","ok");fscommand("quit");}};
}
