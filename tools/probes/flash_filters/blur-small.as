stop();var seq=0;
function emit(k,v){trace("AIREF|filter-loud-fail-r01|"+(seq++)+"|0|0|0|"+k+"|"+v);}
var sizes=[0,1,2,3,5,10,15,20];
for(var k=0;k<sizes.length;k++)for(var q=1;q<=3;q+=2){
 var wrap=_root.createEmptyMovieClip("wrap",1);var m=wrap.createEmptyMovieClip("m",1);
 m.beginFill(16711680,100);m.moveTo(30,30);m.lineTo(38,30);m.lineTo(38,38);m.lineTo(30,38);m.endFill();
 m.filters=[new flash.filters.BlurFilter(sizes[k],0,q)];
 var b=new flash.display.BitmapData(70,70,true,0);b.draw(wrap);
 var row="";for(var x=0;x<70;x++)row+=","+b.getPixel32(x,34);
 emit("blur",sizes[k]+","+q+row);b.dispose();wrap.removeMovieClip();
}
emit("done","ok");fscommand("quit");