stop();var seq=0;
function emit(k,v){trace("AIREF|shadow-materialized-opacity-r84|"+(seq++)+"|0|0|0|"+k+"|"+v);}
function row(id,stage,b){var black=new flash.display.BitmapData(64,64,false,0);black.draw(b);var values="";for(var x=0;x<64;x++)values+=","+b.getPixel32(x,32)+","+black.getPixel32(x,32);for(var y=0;y<64;y++)values+=","+b.getPixel32(32,y)+","+black.getPixel32(32,y);emit("row",id+","+stage+values);black.dispose();}
function empty(){return new flash.display.BitmapData(64,64,true,0);}
function draw(target,src,opacity){target.draw(src,new flash.geom.Matrix(),new flash.geom.ColorTransform(1,1,1,opacity/100,0,0,0,0),"normal",undefined,false);}
var configs=[[1137375,135,2,3.99609375,3,135,1.25,0.75,2.5],[16712064,25,0,8.25,1,0,-0.501953125,0.5,0.75]];
var alphas=[0,1,64,128,254,255];var childOp=[1,25,50,99,100];var parentOp=[25,50,100];var id=0;
for(var ci=0;ci<configs.length;ci++)for(var api=0;api<2;api++)for(var ai=0;ai<alphas.length;ai++)for(var oi=0;oi<childOp.length;oi++)for(var pi=0;pi<parentOp.length;pi++){
 var c=configs[ci];var source=empty();
 for(var y=24;y<41;y++)for(var x=24;x<41;x++){var a=c[1];if(c[2]==2)a=Math.floor(a*(x-24)/16);source.setPixel32(x,y,(a<<24)|c[0]);}
 var f=new flash.filters.DropShadowFilter(c[6],c[5],5362671,c[7],c[3],c[3],c[8],c[4],false,false,false);
 var filtered=empty();
 if(api==0)filtered.applyFilter(source,source.rectangle,new flash.geom.Point(0,0),f);
 else{var wrap=createEmptyMovieClip("wrap",1);var m=wrap.createEmptyMovieClip("m",1);m.attachBitmap(source,1,"auto",false);m.filters=[f];filtered.draw(wrap);wrap.removeMovieClip();}
 var middle=new flash.display.BitmapData(64,64,true,(64<<24)|0x3355cc);
 var back=new flash.display.BitmapData(64,64,true,(alphas[ai]<<24)|0x81d3ef);
 var child=empty();draw(child,filtered,childOp[oi]);
 var parent=empty();draw(parent,middle,100);draw(parent,child,100);
 var result=empty();draw(result,back,100);draw(result,parent,parentOp[pi]);
 emit("case",[id,ci,api,alphas[ai],childOp[oi],parentOp[pi],f.alpha,f.strength,f.blurX,f.blurY,f.quality,f.angle,f.distance].join(","));
 row(id,"input",source);row(id,"middle",middle);row(id,"back",back);row(id,"filtered",filtered);row(id,"child",child);row(id,"parent",parent);row(id,"final",result);
 source.dispose();middle.dispose();back.dispose();filtered.dispose();child.dispose();parent.dispose();result.dispose();id++;
}emit("done","ok");fscommand("quit");
