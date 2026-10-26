stop();var seq=0;var phase=0;
function emit(k,v){trace("AIREF|RUN|"+(seq++)+"|0|0|0|"+k+"|"+v);}
var filter=new flash.filters.ColorMatrixFilter([-0.5946630835533142,1.0937881469726562,0.5008748769760132,0.0,8.999999046325684,0.4649420976638794,0.5073584318161011,0.02769942581653595,0.0,9.0,0.10156211256980896,1.652533769607544,-0.7540958523750305,0.0,9.000000953674316,0.0,0.0,0.0,1.0,0.0]);emit("matrix",filter.matrix.join(","));
var origins=[0,1,3];var colors=[0xa08008,0xf8e830];var cases=[];
for(var w=1;w<=9;w++){var targets=w==1?[0]:(w==2?[0,1]:[0,1,w-1]);for(var si=0;si<3;si++)for(var di=0;di<3;di++)for(var ti=0;ti<targets.length;ti++)for(var mode=0;mode<4;mode++)for(var ci=0;ci<2;ci++)cases.push([w,origins[si],origins[di],targets[ti],mode,ci]);}
function row(label,image){var black=new flash.display.BitmapData(64,1,false,0);black.draw(image);var values=[];for(var x=0;x<64;x++)values.push(image.getPixel32(x,0),black.getPixel32(x,0));emit(label,values.join(","));black.dispose();}
_root.onEnterFrame=function(){var v=cases[phase];var w=v[0];var sx=v[1];var dx=v[2];var at=v[3];var mode=v[4];var color=colors[v[5]];
 var fill=mode==0?(0xff000000|color):(mode==1?0:(mode==2?0xff00ff00:0xff000000));var source=new flash.display.BitmapData(64,1,true,fill);source.setPixel32(sx+at,0,0xff000000|color);
 emit("case",[phase].concat(v).concat([sx+at,dx+at]).join(","));row("source",source);
 var dest=new flash.display.BitmapData(64,1,true,0);dest.applyFilter(source,new flash.geom.Rectangle(sx,0,w,1),new flash.geom.Point(dx,0),filter);row("filtered",dest);
 source.dispose();dest.dispose();phase++;if(phase==cases.length){delete _root.onEnterFrame;emit("done","ok");fscommand("quit");}
};
