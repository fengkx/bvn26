stop();var seq=0;var phase=0;
function emit(k,v){trace("AIREF|RUN|"+(seq++)+"|0|0|0|"+k+"|"+v);}
var coefficients=[];for(var centerIndex=0;centerIndex<3;centerIndex++){var center=[0.5,1,2][centerIndex];for(var delta=-4;delta<=4;delta++)coefficients.push(center+delta/8192);}var cases=[];
var bytes=[0,1,63,64,127,128,191,192,254,255];var offsets=[-1,-0.75,-0.5,-0.25,0,0.25,0.5,0.75,1];
for(var ci=0;ci<coefficients.length;ci++)for(var vi=0;vi<bytes.length;vi++)for(var oi=0;oi<offsets.length;oi++)for(var neighbor=0;neighbor<2;neighbor++)cases.push([ci,bytes[vi],neighbor==0?255:0,offsets[oi]]);
function row(label,image){var black=new flash.display.BitmapData(4,1,false,0);black.draw(image);var values=[];for(var x=0;x<4;x++)values.push(image.getPixel32(x,0),black.getPixel32(x,0));emit(label,values.join(","));black.dispose();}
function sample(){var v=cases[phase];var ci=v[0];var value=v[1];var neighbor=v[2];var axis=1;var coefficient=coefficients[ci];var offset=v[3];
 var matrix=[0,0,0,0,offset,0,1,0,0,0,0,0,1,0,0,0,0,0,1,0];matrix[axis]=coefficient;var filter=new flash.filters.ColorMatrixFilter(matrix);
 var source=new flash.display.BitmapData(4,1,true,0);source.setPixel32(0,0,0xff000000|(value<<(16-axis*8)));source.setPixel32(1,0,neighbor<<24);
 emit("case",[phase,ci,axis,value,neighbor,offset].join(","));emit("matrix",filter.matrix.join(","));row("source",source);
 var dest=new flash.display.BitmapData(4,1,true,0);dest.applyFilter(source,source.rectangle,new flash.geom.Point(0,0),filter);row("filtered",dest);source.dispose();dest.dispose();phase++;}
_root.onEnterFrame=function(){for(var batch=0;batch<32 && phase<cases.length;batch++)sample();if(phase==cases.length){delete _root.onEnterFrame;emit("done","ok");fscommand("quit");}};
