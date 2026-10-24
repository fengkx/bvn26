stop();var seq=0;
function emit(k,v){trace("AIREF|glow-shadow-multipass-r76|"+(seq++)+"|0|0|0|"+k+"|"+v);}
function row(id,stage,b){var black=new flash.display.BitmapData(64,64,false,0);black.draw(b);var values="";for(var x=0;x<64;x++)values+=","+b.getPixel32(x,32)+","+black.getPixel32(x,32);for(var y=0;y<64;y++)values+=","+b.getPixel32(32,y)+","+black.getPixel32(32,y);emit("row",id+","+stage+values);black.dispose();}
var kernels=[1.5,3.99609375,7.99609375,8.25,16];
var alphas=[25,135];var id=0;
for(var ki=0;ki<kernels.length;ki++)for(var ai=0;ai<alphas.length;ai++)for(var pattern=0;pattern<3;pattern++)for(var axis=0;axis<3;axis++)for(var quality=1;quality<=3;quality++)for(var family=0;family<2;family++){
 var source=new flash.display.BitmapData(64,64,true,0);var alpha=alphas[ai];
 for(var y=24;y<41;y++)for(var x=24;x<41;x++){
  var a=alpha;if(pattern==1 && (x!=32 || y!=32))a=0;
  if(pattern==2)a=Math.floor(alpha*(x-24)/16);
  source.setPixel32(x,y,(a<<24)|16777215);
 }
 var k=kernels[ki];var bx=axis==1?1:k;var by=axis==0?1:k;
 var filter;
 if(family==0)filter=new flash.filters.GlowFilter(5362671,1,bx,by,1,quality,false,false);
 else filter=new flash.filters.DropShadowFilter(0,0,5362671,1,bx,by,1,quality,false,false,false);
 emit("case",id+","+k+","+alpha+","+pattern+","+axis+","+filter.blurX+","+filter.blurY+","+quality+","+filter.quality+","+family+","+filter.color+","+filter.alpha+","+filter.strength);
 row(id,"input",source);
 var blur=new flash.display.BitmapData(64,64,true,0);blur.applyFilter(source,source.rectangle,new flash.geom.Point(0,0),new flash.filters.BlurFilter(bx,by,quality));row(id,"blur",blur);blur.dispose();
 var dest=new flash.display.BitmapData(64,64,true,0);dest.applyFilter(source,source.rectangle,new flash.geom.Point(0,0),filter);row(id,"filtered",dest);
 source.dispose();dest.dispose();id++;
}emit("done","ok");fscommand("quit");
