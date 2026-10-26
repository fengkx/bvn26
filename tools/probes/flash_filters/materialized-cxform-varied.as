stop();
var seq = 0;
function emit(k,v) { trace("AIREF|materialized-cxform-varied-r38|"+(seq++)+"|0|0|0|"+k+"|"+v); }
function bitmap(w,h,c,a) { return new flash.display.BitmapData(w,h,true,(a<<24)|c); }
function drawAt(target,source,x,y,opacity,cx) {
    var matrix = new flash.geom.Matrix();
    matrix.translate(x,y);
    var transform = new flash.geom.ColorTransform(cx ? 0.5 : 1,cx ? 0.75 : 1,1,opacity/100,cx ? 8 : 0,0,cx ? -4 : 0,0);
    target.draw(source,matrix,transform,"normal",undefined,false);
}
function sourcePixel(b) {
    var black = new flash.display.BitmapData(1,1,false,0);
    black.draw(b);
    var result = [b.getPixel32(0,0),black.getPixel32(0,0)];
    black.dispose();return result;
}
function dump(id,stage,b) {
    var black = new flash.display.BitmapData(b.width,b.height,false,0);
    black.draw(b);
    for(var y=0;y<b.height;y++) {
        var row = [id,stage,y];
        for(var x=0;x<b.width;x++) row.push(b.getPixel32(x,y),black.getPixel32(x,y));
        emit("row",row.join(","));
    }
    black.dispose();
}
var widths=[1,3,4,7,8,12,15,16,17,18,31,32,33];var origins=[0,1,3];var alphas=[7,93,135,231];var ops=[25,50,100];var id=0;
for(var wi=0;wi<widths.length;wi++)for(var oi=0;oi<origins.length;oi++)for(var ai=0;ai<alphas.length;ai++)for(var pi=0;pi<ops.length;pi++) {
 var width=widths[wi];var origin=origins[oi];
 var input=bitmap(width,1,0x46c4ec,alphas[ai]);var result=bitmap(width+origin+2,1,0,0);
 for(var sx=0;sx<width;sx++)input.setPixel32(sx,0,(alphas[ai]<<24)|(sx%2==0 ? 0x46c4ec : 0xff8001));
 drawAt(result,input,origin,0,ops[pi],1);
 var black=new flash.display.BitmapData(result.width,1,false,0);black.draw(result);
 var row=[id,width,origin,alphas[ai],ops[pi]].concat(sourcePixel(input));
 for(var x=0;x<result.width;x++)row.push(result.getPixel32(x,0),black.getPixel32(x,0));
 emit("span",row.join(","));input.dispose();result.dispose();black.dispose();id++;
}
emit("done","ok");fscommand("quit");
