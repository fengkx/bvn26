stop();var seq=0;
function emit(k,v){trace("AIREF|filter-cache-bounds-r61|"+(seq++)+"|0|0|0|"+k+"|"+v);}
var bitmap=new flash.display.BitmapData(160,160,true,0);
var widths=[1,2,3,15,16,17,34,64];var blurs=[1,3,5,7];
for(var w=0;w<widths.length;w++)for(var b=0;b<blurs.length;b++){
 var rect=new flash.geom.Rectangle(40,40,widths[w],64);
 var glow=new flash.filters.GlowFilter(5362671,1,blurs[b],blurs[b],1,1,false,false);
 var blur=new flash.filters.BlurFilter(blurs[b],blurs[b],1);
 var gr=bitmap.generateFilterRect(rect,glow);var br=bitmap.generateFilterRect(rect,blur);
 emit("rect",widths[w]+","+blurs[b]+",glow,"+gr.x+","+gr.y+","+gr.width+","+gr.height);
 emit("rect",widths[w]+","+blurs[b]+",blur,"+br.x+","+br.y+","+br.width+","+br.height);
}
bitmap.dispose();emit("done","ok");fscommand("quit");
