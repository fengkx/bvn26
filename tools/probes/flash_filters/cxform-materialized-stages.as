stop();
var seq=0;
function emit(k,v) { trace("AIREF|cxform-materialized-stages-r42|"+(seq++)+"|0|0|0|"+k+"|"+v); }
var alphas=[7,14,93,135,146,197,206,210,229,231,244];
var multipliers=[255,256,257];var offsets=[-1,0,1];var opacities=[33,67,100];var id=0;
function opaque(input) { var black=new flash.display.BitmapData(32,1,false,0);black.draw(input);return black; }
function drawBuffer(input,rm,gm,bm,op,rd,gd,bd) {
    var output=new flash.display.BitmapData(32,1,true,0);
    var cxform=new flash.geom.ColorTransform(rm,gm,bm,op/100,rd,gd,bd,0);
    output.draw(input,new flash.geom.Matrix(),cxform,"normal",new flash.geom.Rectangle(0,0,32,1),false);
    return output;
}
function record(stage,input,sourceBlack,output) {
    var black=opaque(output);var row=[id,a,m,d,op,stage];
    for(var x=0;x<32;x++)row.push(input.getPixel32(x,0),sourceBlack.getPixel32(x,0),output.getPixel32(x,0),black.getPixel32(x,0));
    emit("row",row.join(","));black.dispose();
}
for(var ai=0;ai<alphas.length;ai++)for(var mi=0;mi<multipliers.length;mi++)
for(var di=0;di<offsets.length;di++)for(var oi=0;oi<opacities.length;oi++) {
    var a=alphas[ai];var m=multipliers[mi];var d=offsets[di];var op=opacities[oi];
    var input=new flash.display.BitmapData(32,1,true,0);
    var r=a==14 ? 91 : 117;var b=a==14 ? 237 : 240;
    for(var x=0;x<32;x++) {
        var g=Math.round(Math.min(a,(x+1)*4)*255/a);
        input.setPixel32(x,0,(a<<24)|(r<<16)|(g<<8)|b);
    }
    var sourceBlack=opaque(input);
    var combined=drawBuffer(input,0.5,m/256,1,op,8,d,-4);
    // Both intermediate sources are real BitmapData allocations. No cache inference.
    var multiplied=drawBuffer(input,0.5,m/256,1,100,0,0,0);
    var offset=drawBuffer(input,1,1,1,100,8,d,-4);
    var multBlack=opaque(multiplied);var offsetBlack=opaque(offset);
    var multThenOffset=drawBuffer(multiplied,1,1,1,op,8,d,-4);
    var offsetThenMult=drawBuffer(offset,0.5,m/256,1,op,0,0,0);
    record(0,input,sourceBlack,combined);
    record(1,input,sourceBlack,multiplied);
    record(2,input,sourceBlack,offset);
    record(3,multiplied,multBlack,multThenOffset);
    record(4,offset,offsetBlack,offsetThenMult);
    input.dispose();sourceBlack.dispose();combined.dispose();multiplied.dispose();offset.dispose();
    multBlack.dispose();offsetBlack.dispose();multThenOffset.dispose();offsetThenMult.dispose();id++;
}
emit("done","ok");fscommand("quit");
