stop();var seq=0;var phase=0;
function emit(k,v){trace("AIREF|RUN|"+(seq++)+"|0|0|0|"+k+"|"+v);}
var matrix=[-0.5946631,1.0937881,0.5008749,0,8.999999,0.4649421,0.50735843,0.027699426,0,9,0.10156211,1.6525338,-0.75409585,0,9.000001,0,0,0,1,0];
var filter=new flash.filters.ColorMatrixFilter(matrix);emit("matrix",filter.matrix.join(","));
var colors=[0xa08008,0xf8e830,0xcc7faa];var widths=[3,4,5];var neighbors=[0,127,255];var cases=[];
for(var alpha=0;alpha<256;alpha++)for(var color=0;color<colors.length;color++)for(var wi=0;wi<widths.length;wi++)for(var side=0;side<2;side++)for(var ni=0;ni<neighbors.length;ni++)cases.push([alpha,color,widths[wi],side==0?0:widths[wi]-1,neighbors[ni]]);
function row(label,image,w){var black=new flash.display.BitmapData(w,1,false,0);black.draw(image);var values=[];for(var x=0;x<w;x++)values.push(image.getPixel32(x,0),black.getPixel32(x,0));emit(label,values.join(","));black.dispose();}
function sample(){var v=cases[phase];var alpha=v[0];var color=v[1];var w=v[2];var target=v[3];var neighbor=v[4];var source=new flash.display.BitmapData(w,1,true,neighbor<<24);source.setPixel32(target,0,(alpha<<24)|colors[color]);
 emit("case",[phase,alpha,color,w,target,neighbor].join(","));row("source",source,w);var dest=new flash.display.BitmapData(w,1,true,0);dest.applyFilter(source,source.rectangle,new flash.geom.Point(0,0),filter);row("filtered",dest,w);source.dispose();dest.dispose();phase++;}
_root.onEnterFrame=function(){for(var batch=0;batch<32 && phase<cases.length;batch++)sample();if(phase==cases.length){delete _root.onEnterFrame;emit("done","ok");fscommand("quit");}};
