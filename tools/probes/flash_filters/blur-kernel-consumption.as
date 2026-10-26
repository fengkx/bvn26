stop();var seq=0;
function emit(k,v){trace("AIREF|blur-kernel-consumption-r72|"+(seq++)+"|0|0|0|"+k+"|"+v);}
function row(id,stage,b){var black=new flash.display.BitmapData(32,32,false,0);black.draw(b);var values="";for(var x=0;x<32;x++)values+=","+b.getPixel32(x,16)+","+black.getPixel32(x,16);for(var y=0;y<32;y++)values+=","+b.getPixel32(16,y)+","+black.getPixel32(16,y);emit("row",id+","+stage+values);black.dispose();}
var kernels=[];var centers=[2.0625,3.5,3.9375,4,5.0625,7.9375,8];var offsets=[-17,-16,-15,-1,0,1,15,16,17];
for(var ci=0;ci<centers.length;ci++)for(var oi=0;oi<offsets.length;oi++)kernels.push(centers[ci]+offsets[oi]/1024);
var alphas=[25,135,255];var id=0;
for(var ki=0;ki<kernels.length;ki++)for(var ai=0;ai<alphas.length;ai++)for(var pattern=0;pattern<2;pattern++)for(var axis=0;axis<3;axis++){
 var source=new flash.display.BitmapData(32,32,true,0);var alpha=alphas[ai];
 for(var y=8;y<25;y++)for(var x=8;x<25;x++){
  var a=alpha;if(pattern==1 && (x!=16 || y!=16))a=0;
  if(pattern==2)a=Math.floor(alpha*(x-8)/16);
  source.setPixel32(x,y,(a<<24)|16777215);
 }
 var k=kernels[ki];var bx=axis==1?1:k;var by=axis==0?1:k;
 var filter=new flash.filters.BlurFilter(bx,by,1);
 emit("case",id+","+k+","+alpha+","+pattern+","+axis+","+filter.blurX+","+filter.blurY);
 row(id,"input",source);
 var dest=new flash.display.BitmapData(32,32,true,0);dest.applyFilter(source,source.rectangle,new flash.geom.Point(0,0),filter);row(id,"filtered",dest);
 source.dispose();dest.dispose();id++;
}emit("done","ok");fscommand("quit");
