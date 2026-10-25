stop();var seq=0;var phase=0;var id=0;
function emit(k,v){trace("AIREF|RUN|"+(seq++)+"|0|0|0|"+k+"|"+v);}
function makeSource(label,width){
 var source=new flash.display.BitmapData(width,8,true,0);
 for(var y=0;y<8;y++){var row=[];for(var x=0;x<width;x++){source.setPixel32(x,y,4278190080+(x%2)*255*65536+((x*37+17)%256)*256+113);row.push(source.getPixel32(x,y));}emit("source",label+","+width+","+y+","+row.join(","));}return source;
}
function bits(v){
 if(v==0)return "0";var sign=v<0?-1:1;var n=Math.abs(v);var exponent=0;
 while(n>=2){n/=2;exponent++;}while(n<1){n*=2;exponent--;}
 var digits="";for(var bit=0;bit<53;bit++){var d=Math.floor(n);digits+=d;n=(n-d)*2;}
 return sign+":"+exponent+":"+digits;
}
var shared=makeSource("shared",16);var scales=[5,7];var shifts=[128,128.25,256.5];
_root.onEnterFrame=function(){
 var width=16;var origins=[];for(var j=0;j<10;j++)origins.push((-20+phase*10+j)/20);
 for(var mode=0;mode<1;mode++)for(var si=0;si<scales.length;si++)for(var oi=0;oi<origins.length;oi++)for(var ti=0;ti<shifts.length;ti++){
  var source=shared;var painted=mode==2?16:width;
  var parent=_root.createEmptyMovieClip("parent",1);var child=parent.createEmptyMovieClip("child",1);
  child.beginBitmapFill(source,new flash.geom.Matrix(),false,true);child.moveTo(0,0);child.lineTo(painted,0);child.lineTo(painted,8);child.lineTo(0,8);child.lineTo(0,0);child.endFill();
  if(mode==2){child.beginFill(0,0);child.moveTo(width-1,0);child.lineTo(width,0);child.lineTo(width,8);child.lineTo(width-1,8);child.lineTo(width-1,0);child.endFill();}
  child.transform.matrix=new flash.geom.Matrix(scales[si],0,0,1,origins[oi],0);var inner=child.transform.matrix;var outer=new flash.geom.Matrix(1,0,0,1,shifts[ti],4);var bounds=child.getBounds(parent);
  emit("case",[id++,width,mode,source.width,scales[si],origins[oi],shifts[ti],inner.a,inner.tx,bounds.xMin,bounds.xMax,painted].join(","));
  var inv=inner.clone();inv.invert();var twice=inv.clone();twice.invert();
  var full=inner.clone();full.concat(outer);var fi=full.clone();fi.invert();var back=fi.clone();back.invert();
  var numbers=[inner.a,inner.tx,inv.a,inv.tx,twice.a,twice.tx,full.a,full.tx,fi.a,fi.tx,back.a,back.tx,1/inner.a,inner.tx/inner.a,inner.tx*(1/inner.a)];var binary=[];for(var ni=0;ni<numbers.length;ni++)binary.push(bits(numbers[ni]));emit("binary",binary.join(","));
  for(var cache=0;cache<2;cache++){
   child.cacheAsBitmap=cache==1;emit("cache",[cache,child.cacheAsBitmap].join(","));var b=new flash.display.BitmapData(1024,16,false,0);b.draw(parent,outer);var row=[];for(var x=0;x<1024;x++)row.push(b.getPixel(x,7));emit(cache==0?"clear":"cached",row.join(","));b.dispose();
  }
  parent.removeMovieClip();
 }
 phase++;if(phase==4){delete _root.onEnterFrame;emit("done","ok");fscommand("quit");}
};
