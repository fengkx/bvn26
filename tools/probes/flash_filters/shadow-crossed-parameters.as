stop();var seq=0;
function emit(k,v){trace("AIREF|shadow-crossed-parameters-r78|"+(seq++)+"|0|0|0|"+k+"|"+v);}
function row(id,stage,b){var black=new flash.display.BitmapData(64,64,false,0);black.draw(b);var values="";for(var x=0;x<64;x++)values+=","+b.getPixel32(x,32)+","+black.getPixel32(x,32);for(var y=0;y<64;y++)values+=","+b.getPixel32(32,y)+","+black.getPixel32(32,y);emit("row",id+","+stage+values);black.dispose();}
var kernels=[3.99609375,7.99609375,8.25];var alphas=[25,135];var qualities=[1,3];
var offsets=[[0,0],[45,0.375],[45,-0.375],[0,-0.501953125],[135,1.25]];
var filterAlphas=[0.5,0.75,1];var strengths=[0.75,1,2.5];var id=0;
for(var ki=0;ki<kernels.length;ki++)for(var ai=0;ai<alphas.length;ai++)for(var pattern=0;pattern<3;pattern++)for(var qi=0;qi<qualities.length;qi++)for(var oi=0;oi<offsets.length;oi++)for(var fi=0;fi<filterAlphas.length;fi++)for(var si=0;si<strengths.length;si++){
 var source=new flash.display.BitmapData(64,64,true,0);var alpha=alphas[ai];
 for(var y=24;y<41;y++)for(var x=24;x<41;x++){
  var a=alpha;if(pattern==1 && (x!=32 || y!=32))a=0;
  if(pattern==2)a=Math.floor(alpha*(x-24)/16);
  source.setPixel32(x,y,(a<<24)|16777215);
 }
 var k=kernels[ki];var bx=k;var by=k;var quality=qualities[qi];var angle=offsets[oi][0];var distance=offsets[oi][1];
 var fa=filterAlphas[fi];var strength=strengths[si];
 var filter=new flash.filters.DropShadowFilter(distance,angle,5362671,fa,bx,by,strength,quality,false,false,false);
 emit("case",id+","+k+","+alpha+","+pattern+","+quality+","+fa+","+strength+","+angle+","+distance+","+filter.blurX+","+filter.blurY+","+filter.quality+","+filter.alpha+","+filter.strength+","+filter.angle+","+filter.distance);
 row(id,"input",source);
 var blur=new flash.display.BitmapData(64,64,true,0);blur.applyFilter(source,source.rectangle,new flash.geom.Point(0,0),new flash.filters.BlurFilter(bx,by,quality));row(id,"blur",blur);blur.dispose();
 var dest=new flash.display.BitmapData(64,64,true,0);dest.applyFilter(source,source.rectangle,new flash.geom.Point(0,0),filter);row(id,"filtered",dest);
 source.dispose();dest.dispose();id++;
}emit("done","ok");fscommand("quit");
