stop();var seq=0;
function emit(k,v){trace("AIREF|blur-kernel-heldout-r73|"+(seq++)+"|0|0|0|"+k+"|"+v);}
function row(id,stage,b){var black=new flash.display.BitmapData(64,64,false,0);black.draw(b);var values="";for(var x=0;x<64;x++)values+=","+b.getPixel32(x,32)+","+black.getPixel32(x,32);for(var y=0;y<64;y++)values+=","+b.getPixel32(32,y)+","+black.getPixel32(32,y);emit("row",id+","+stage+values);black.dispose();}
var kernels=[];var centers=[0.5,1,1.5,2,8.25,15.5,16,16.25];var offsets=[-1,0,1];
for(var ci=0;ci<centers.length;ci++)for(var oi=0;oi<offsets.length;oi++)kernels.push(centers[ci]+offsets[oi]/1024);
var alphas=[25,135];var id=0;
for(var ki=0;ki<kernels.length;ki++)for(var ai=0;ai<alphas.length;ai++)for(var pattern=0;pattern<3;pattern++)for(var axis=0;axis<3;axis++)for(var quality=1;quality<=3;quality++){
 var source=new flash.display.BitmapData(64,64,true,0);var alpha=alphas[ai];
 for(var y=24;y<41;y++)for(var x=24;x<41;x++){
  var a=alpha;if(pattern==1 && (x!=32 || y!=32))a=0;
  if(pattern==2)a=Math.floor(alpha*(x-24)/16);
  source.setPixel32(x,y,(a<<24)|16777215);
 }
 var k=kernels[ki];var bx=axis==1?1:k;var by=axis==0?1:k;
 var filter=new flash.filters.BlurFilter(bx,by,quality);
 emit("case",id+","+k+","+alpha+","+pattern+","+axis+","+filter.blurX+","+filter.blurY+","+quality+","+filter.quality);
 row(id,"input",source);
 var dest=new flash.display.BitmapData(64,64,true,0);dest.applyFilter(source,source.rectangle,new flash.geom.Point(0,0),filter);row(id,"filtered",dest);
 source.dispose();dest.dispose();id++;
}emit("done","ok");fscommand("quit");
