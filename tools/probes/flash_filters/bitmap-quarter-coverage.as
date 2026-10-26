stop();var seq=0;var phase=0;var id=0;
function emit(k,v){trace("AIREF|RUN|"+(seq++)+"|0|0|0|"+k+"|"+v);}
var alphas=[0,1,2,31,63,64,127,128,254,255];var colors=[0,1,17,63,127,128,254,255];var offsets=[0,0.25,0.5,0.75];
_root.onEnterFrame=function(){
 var alpha=alphas[phase];
 for(var ci=0;ci<colors.length;ci++){
  var color=colors[ci];var source=new flash.display.BitmapData(4,3,true,alpha*16777216+color*65536+(255-color)*256+73);
  var sb=new flash.display.BitmapData(4,3,false,0);sb.draw(source);
  emit("input",[phase,ci,alpha,color,source.getPixel32(0,0),sb.getPixel32(0,0)].join(","));sb.dispose();
  for(var turn=0;turn<2;turn++)for(var xi=0;xi<4;xi++)for(var yi=0;yi<4;yi++){
   var parent=_root.createEmptyMovieClip("parent",1);var child=parent.createEmptyMovieClip("child",1);
   var fm=turn==0?new flash.geom.Matrix():new flash.geom.Matrix(0,1,-1,0,3,0);var rw=turn==0?4:3;var rh=turn==0?3:4;
   child.beginBitmapFill(source,fm,false,true);child.moveTo(0,0);child.lineTo(rw,0);child.lineTo(rw,rh);child.lineTo(0,rh);child.lineTo(0,0);child.endFill();
   var draw=new flash.geom.Matrix(1,0,0,1,2+offsets[xi],2+offsets[yi]);
   emit("case",[id++,phase,ci,turn,draw.a,draw.d,draw.tx,draw.ty,rw,rh,fm.a,fm.b,fm.c,fm.d,fm.tx,fm.ty].join(","));
   var image=new flash.display.BitmapData(8,8,true,0);image.draw(parent,draw);var black=new flash.display.BitmapData(8,8,false,0);black.draw(image);
   for(var y=0;y<8;y++){var row=[];for(var x=0;x<8;x++)row.push(image.getPixel32(x,y),black.getPixel32(x,y));emit("row",y+","+row.join(","));}
   image.dispose();black.dispose();parent.removeMovieClip();
  }
  source.dispose();
 }
 phase++;if(phase==alphas.length){delete _root.onEnterFrame;emit("done","ok");fscommand("quit");}
};
