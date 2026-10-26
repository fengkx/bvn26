stop();var seq=0;
function emit(k,v){trace("AIREF|filter-rectangle-half-r67|"+(seq++)+"|0|0|0|"+k+"|"+v);}
var bitmap=new flash.display.BitmapData(160,160,true,0);
var centers=[2.5,4.5,6.5,8.5,10.5,12.5];var offsets=[-1/1048576,-1/8388608,-1/16777216,-1/33554432,-1/67108864,0,1/67108864,1/33554432,1/16777216,1/8388608,1/1048576];var id=0;
for(var ci=0;ci<centers.length;ci++)for(var oi=0;oi<offsets.length;oi++)for(var ti=0;ti<2;ti++){
 var value=centers[ci]+offsets[oi];var filter;
 if(ti==0)filter=new flash.filters.GlowFilter(5362671,1,value,value,1,1,false,false);
 else filter=new flash.filters.BlurFilter(value,value,1);
 var r=bitmap.generateFilterRect(new flash.geom.Rectangle(40,40,17,64),filter);
 emit("rect",id+","+centers[ci]+","+offsets[oi]+","+ti+","+value+","+filter.blurX+","+filter.blurY+","+r.x+","+r.y+","+r.width+","+r.height);id++;
}
bitmap.dispose();emit("done","ok");fscommand("quit");
