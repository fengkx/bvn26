stop();var seq=0;
function emit(k,v){trace("AIREF|filter-blur-bounds-r02|"+(seq++)+"|0|0|0|"+k+"|"+v);}
var widths=[1,2,4,8,12,16,32];var sizes=[6,7,8,9,10,11,15,20,21,30];
for(var w=0;w<widths.length;w++)for(var k=0;k<sizes.length;k++)for(var q=1;q<=3;q++){
 var wrap=_root.createEmptyMovieClip("wrap",1);var m=wrap.createEmptyMovieClip("m",1);
 m.beginFill(16711680,100);m.moveTo(60,60);m.lineTo(60+widths[w],60);m.lineTo(60+widths[w],100);m.lineTo(60,100);m.endFill();
 m.filters=[new flash.filters.BlurFilter(sizes[k],0,q)];
 var b=new flash.display.BitmapData(160,160,true,0);b.draw(wrap);
 var row="";for(var x=0;x<160;x++)row+=","+b.getPixel32(x,80);
 emit("bounds",widths[w]+","+sizes[k]+","+q+row);b.dispose();wrap.removeMovieClip();
}
emit("done","ok");fscommand("quit");