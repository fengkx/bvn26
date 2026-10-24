stop();
var seq = 0;
function emit(k,v) { trace("AIREF|materialized-cxform-r38|"+(seq++)+"|0|0|0|"+k+"|"+v); }
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
var colors=[0x46c4ec,0x81d3ef,0xff8001,0x017ffe];var alphas=[0,1,2,7,63,128,254,255];var ops=[25,50,100];var id=0;
for(var c=0;c<4;c++)for(var a=0;a<8;a++)for(var o=0;o<3;o++){
 var input=bitmap(1,1,colors[c],alphas[a]);var result=bitmap(1,1,0,0);
 drawAt(result,input,0,0,ops[o],1);
 emit("cx",[id,c,alphas[a],ops[o]].concat(sourcePixel(input),sourcePixel(result)).join(","));
 input.dispose();result.dispose();id++;
}
emit("done","ok");fscommand("quit");
