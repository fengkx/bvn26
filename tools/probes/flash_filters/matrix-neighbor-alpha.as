stop();var seq=0;var phase=0;
function emit(k,v){trace("AIREF|RUN|"+(seq++)+"|0|0|0|"+k+"|"+v);}
var filter=new flash.filters.ColorMatrixFilter([-0.5946630835533142,1.0937881469726562,0.5008748769760132,0.0,8.999999046325684,0.4649420976638794,0.5073584318161011,0.02769942581653595,0.0,9.0,0.10156211256980896,1.652533769607544,-0.7540958523750305,0.0,9.000000953674316,0.0,0.0,0.0,1.0,0.0]);emit("matrix",filter.matrix.join(","));
var widths=[4,8,16,17,33,223];var colors=[0xa08008,0xf8e830];var cases=[];
for(var wi=0;wi<widths.length;wi++){var w=widths[wi];var starts=w==4?[0]:[0,1,w-4];for(var bi=0;bi<starts.length;bi++)for(var lane=0;lane<4;lane++)for(var mask=0;mask<8;mask++)for(var ai=0;ai<2;ai++)for(var ci=0;ci<2;ci++)cases.push([w,starts[bi],lane,mask,ai==0?255:127,ci]);}
function row(label,image){var black=new flash.display.BitmapData(image.width,1,false,0);black.draw(image);var values=[];for(var x=0;x<image.width;x++)values.push(image.getPixel32(x,0),black.getPixel32(x,0));emit(label,values.join(","));black.dispose();}
_root.onEnterFrame=function(){var v=cases[phase];var w=v[0];var base=v[1];var lane=v[2];var mask=v[3];var neighborAlpha=v[4];var color=colors[v[5]];var source=new flash.display.BitmapData(w,1,true,0xff000000|color);var bit=0;
 for(var j=0;j<4;j++){if(j==lane)continue;var a=(mask&(1<<bit))!=0?neighborAlpha:0;source.setPixel32(base+j,0,(a<<24)|color);bit++;}
 emit("case",[phase].concat(v).concat([base+lane]).join(","));row("source",source);
 var dest=new flash.display.BitmapData(w,1,true,0);dest.applyFilter(source,source.rectangle,new flash.geom.Point(0,0),filter);row("filtered",dest);
 source.dispose();dest.dispose();phase++;if(phase==cases.length){delete _root.onEnterFrame;emit("done","ok");fscommand("quit");}
};
