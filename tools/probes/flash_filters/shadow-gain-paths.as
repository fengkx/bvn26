stop();var seq=0;
function emit(k,v){trace("AIREF|shadow-gain-paths-r80|"+(seq++)+"|0|0|0|"+k+"|"+v);}
function row(id,stage,b){var black=new flash.display.BitmapData(256,4,false,0);black.draw(b);var values="";for(var x=0;x<256;x++)values+=","+b.getPixel32(x,1)+","+black.getPixel32(x,1);emit("row",id+","+stage+values);black.dispose();}
var alphas=[0.5,0.75,1];var strengths=[0.75,1,2.5];var id=0;
for(var ai=0;ai<alphas.length;ai++)for(var si=0;si<strengths.length;si++)for(var hidden=0;hidden<2;hidden++){
 var source=new flash.display.BitmapData(256,4,true,0);
 for(var y=0;y<4;y++)for(var x=0;x<256;x++)source.setPixel32(x,y,(x<<24)|16777215);
 var f=new flash.filters.DropShadowFilter(0,0,5362671,alphas[ai],0,0,strengths[si],1,false,false,hidden==1);
 emit("case",id+","+alphas[ai]+","+strengths[si]+","+hidden+","+f.alpha+","+f.strength+","+(f.hideObject?1:0)+","+f.blurX+","+f.blurY+","+f.angle+","+f.distance+","+f.quality+","+f.color);
 row(id,"input",source);
 var wrap=createEmptyMovieClip("wrap",1);var m=wrap.createEmptyMovieClip("m",1);m.attachBitmap(source,1,"auto",false);
 var b=new flash.display.BitmapData(256,4,true,0);b.draw(wrap);row(id,"display_input",b);b.dispose();
 b=new flash.display.BitmapData(256,4,true,0);b.applyFilter(source,source.rectangle,new flash.geom.Point(0,0),f);row(id,"apply",b);b.dispose();
 m.filters=[f];b=new flash.display.BitmapData(256,4,true,0);b.draw(wrap);row(id,"display",b);b.dispose();
 wrap.removeMovieClip();source.dispose();id++;
}emit("done","ok");fscommand("quit");
