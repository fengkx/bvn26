stop();var seq=0;
function emit(k,v){trace("AIREF|RUN|"+(seq++)+"|0|0|0|"+k+"|"+v);}
function readback(label,b){
 var black=new flash.display.BitmapData(600,400,false,0);black.draw(b);
 for(var y=0;y<400;y++){var row=[];for(var x=0;x<600;x++)row.push(b.getPixel32(x,y),black.getPixel32(x,y));emit("row",label+","+y+","+row.join(","));}
 black.dispose();
}
var mc=_root.attachMovie("case0","source",1);mc.gotoAndStop(1);var child=mc.getInstanceAtDepth(27-16384);
var matrix=new flash.geom.Matrix(1,0,0,1,281.549878,212.4046024);var filter=new flash.filters.BlurFilter(15,0,3);
var props=child.filters;emit("props",[props.length,props[0].blurX,props[0].blurY,props[0].quality,filter.blurX,filter.blurY,filter.quality].join(","));
var authored=new flash.display.BitmapData(600,400,true,0);authored.draw(mc,matrix);readback("authored",authored);
child.filters=[];child.cacheAsBitmap=false;
var input=new flash.display.BitmapData(600,400,true,0);input.draw(mc,matrix);readback("input",input);
var applied=new flash.display.BitmapData(600,400,true,0);applied.applyFilter(input,input.rectangle,new flash.geom.Point(),filter);readback("apply",applied);
var bitmap=_root.createEmptyMovieClip("bitmap",20);bitmap.attachBitmap(input,1,"never",false);
var plain=new flash.display.BitmapData(600,400,true,0);plain.draw(bitmap);readback("bitmap-input",plain);
bitmap.filters=[filter];var displayed=new flash.display.BitmapData(600,400,true,0);displayed.draw(bitmap);readback("bitmap-filter",displayed);
readback("input-after",input);emit("done","ok");fscommand("quit");
