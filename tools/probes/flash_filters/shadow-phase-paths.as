stop();var seq=0;
function emit(k,v){trace("AIREF|shadow-phase-paths-r79|"+(seq++)+"|0|0|0|"+k+"|"+v);}
function pixels(id,stage,b,origin){var black=new flash.display.BitmapData(64,64,false,0);black.draw(b);var values="";for(var y=origin-3;y<=origin+3;y++)for(var x=origin-3;x<=origin+3;x++)values+=","+b.getPixel32(x,y)+","+black.getPixel32(x,y);emit("pixels",id+","+stage+values);black.dispose();}
var origins=[8,32];var halves=[0.5,1.5,31.5,127.5,128.5,129.5];var deltas=[-1,0,1];
var routes=[[0,-1],[180,1],[0,1],[180,-1],[90,-1],[-90,1],[90,1],[-90,-1]];var id=0;
for(var oi=0;oi<origins.length;oi++)for(var ri=0;ri<routes.length;ri++)for(var hi=0;hi<halves.length;hi++)for(var di=0;di<deltas.length;di++){
 var origin=origins[oi];var angle=routes[ri][0];var distance=routes[ri][1]*(halves[hi]/256+deltas[di]/65536);
 var source=new flash.display.BitmapData(64,64,true,0);source.setPixel32(origin,origin,4294967295);
 var f=new flash.filters.DropShadowFilter(distance,angle,16777215,1,0,0,1,1,false,false,true);
 emit("case",id+","+origin+","+ri+","+halves[hi]+","+deltas[di]+","+angle+","+distance+","+f.angle+","+f.distance+","+(f.hideObject?1:0)+","+f.blurX+","+f.blurY+","+f.alpha+","+f.strength+","+f.quality);
 pixels(id,"input",source,origin);
 var vw=createEmptyMovieClip("vw",2);var v=vw.createEmptyMovieClip("v",1);v.beginFill(16777215,100);v.moveTo(origin,origin);v.lineTo(origin+1,origin);v.lineTo(origin+1,origin+1);v.lineTo(origin,origin+1);v.endFill();
 var b=new flash.display.BitmapData(64,64,true,0);b.draw(vw);pixels(id,"vector_input",b,origin);b.dispose();
 b=new flash.display.BitmapData(64,64,true,0);b.applyFilter(source,source.rectangle,new flash.geom.Point(0,0),f);pixels(id,"apply",b,origin);b.dispose();
 var bw=createEmptyMovieClip("bw",1);var m=bw.createEmptyMovieClip("m",1);m.attachBitmap(source,1,"auto",false);m.filters=[f];
 b=new flash.display.BitmapData(64,64,true,0);b.draw(bw);pixels(id,"bitmap_display",b,origin);b.dispose();
 v.filters=[f];b=new flash.display.BitmapData(64,64,true,0);b.draw(vw);pixels(id,"vector_display",b,origin);b.dispose();
 bw.removeMovieClip();vw.removeMovieClip();source.dispose();id++;
}emit("done","ok");fscommand("quit");
