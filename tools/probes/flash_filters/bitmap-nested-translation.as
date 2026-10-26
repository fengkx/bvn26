stop();var seq=0;function emit(k,v){trace("AIREF|RUN|"+(seq++)+"|0|0|0|"+k+"|"+v);}
var source=new flash.display.BitmapData(60,8,true,0);
for(var y=0;y<8;y++){var row=[];for(var x=0;x<60;x++){var p=4278190080+(x%2)*255*65536+((x*37+17)%256)*256+113;source.setPixel32(x,y,p);row.push(source.getPixel32(x,y));}emit("source",y+","+row.join(","));}
var parent=_root.createEmptyMovieClip("parent",1);var child=parent.createEmptyMovieClip("child",1);
child.beginBitmapFill(source,new flash.geom.Matrix(),false,true);child.moveTo(0,0);child.lineTo(60,0);child.lineTo(60,8);child.lineTo(0,8);child.lineTo(0,0);child.endFill();
var shifts=[281.4,281.449,281.45,281.499,281.5,281.549878,281.55,281.599,281.6];
var origins=[-18.55,-0.05,0,0.05,18.55];var scales=[1,1.23333740234375,3,5];var id=0;
for(var si=0;si<scales.length;si++)for(var oi=0;oi<origins.length;oi++)for(var ti=0;ti<shifts.length;ti++){
 var s=scales[si];var origin=origins[oi];var tx=shifts[ti];child.transform.matrix=new flash.geom.Matrix(s,0,0,1,origin,0);
 var inner=child.transform.matrix;var outer=new flash.geom.Matrix(1,0,0,1,tx,4);var composed=inner.clone();composed.concat(outer);
 emit("case",[id++,s,origin,tx,inner.a,inner.tx,outer.tx,composed.a,composed.tx].join(","));
 for(var mode=0;mode<2;mode++){
  var b=new flash.display.BitmapData(600,16,false,0);var row=[];
  for(var x=0;x<600;x++){b.draw(mode==0?parent:child,mode==0?outer:composed,null,null,new flash.geom.Rectangle(x,7,1,1),true);row.push(b.getPixel(x,7));}
  emit(mode==0?"nested":"direct",row.join(","));b.dispose();
 }
}
emit("done","ok");fscommand("quit");
