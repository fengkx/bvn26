stop();
var seq=0;
function emit(k,v) { trace("AIREF|cxform-zero-green-offset-r42|"+(seq++)+"|0|0|0|"+k+"|"+v); }
// Residual and boundary alphas; zero green isolates offset normalization.
var alphas=[6,14,135,146,197,231,244,255];
var multipliers=[256];var offsets=[1,7,64,127,255];var opacities=[33,67,100];
var id=0;
for(var ai=0;ai<alphas.length;ai++)for(var mi=0;mi<multipliers.length;mi++)
for(var di=0;di<offsets.length;di++)for(var oi=0;oi<opacities.length;oi++) {
    var a=alphas[ai];var input=new flash.display.BitmapData(32,1,true,0);
    // Zero green removes reciprocal dependence from the offset measurement.
    var r=a==14 ? 91 : 117;var b=a==14 ? 237 : 240;
    for(var x=0;x<32;x++) {
        var g=0;
        input.setPixel32(x,0,(a<<24)|(r<<16)|(g<<8)|b);
    }
    var sourceBlack=new flash.display.BitmapData(32,1,false,0);sourceBlack.draw(input);
    var output=new flash.display.BitmapData(32,1,true,0);
    var cxform=new flash.geom.ColorTransform(0.5,multipliers[mi]/256,1,opacities[oi]/100,8,offsets[di],-4,0);
    output.draw(input,new flash.geom.Matrix(),cxform,"normal",new flash.geom.Rectangle(0,0,32,1),false);
    var black=new flash.display.BitmapData(32,1,false,0);black.draw(output);
    var row=[id,a,multipliers[mi],offsets[di],opacities[oi]];
    for(var x=0;x<32;x++)row.push(input.getPixel32(x,0),sourceBlack.getPixel32(x,0),output.getPixel32(x,0),black.getPixel32(x,0));
    emit("row",row.join(","));id++;
    input.dispose();sourceBlack.dispose();output.dispose();black.dispose();
}
emit("done","ok");fscommand("quit");
