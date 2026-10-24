stop();
var seq=0;
function emit(k,v) { trace("AIREF|cxform-amplified-rejected-r44|"+(seq++)+"|0|0|0|"+k+"|"+v); }
// One fixed transform grid for every alpha; centered offsets avoid clamping.
var alphas=[2,6,7,12,14,15,24,28,30,33,35,41,43,45,47,49,51,53,55,59,61,63,67,71,75,79,87,91,95,103,107,111,119,135,143,146,151,159,167,175,183,191,197,199,204,206,207,223,231,244,247];
var gains=[2,4,8];var adjacent=[-1,0,1];var offsets=[-1,0,1];var opacities=[33,67,100];
var id=0;
for(var ai=0;ai<alphas.length;ai++)for(var mi=0;mi<gains.length;mi++)for(var ji=0;ji<adjacent.length;ji++)
for(var di=0;di<offsets.length;di++)for(var oi=0;oi<opacities.length;oi++) {
    var a=alphas[ai];var input=new flash.display.BitmapData(32,1,true,0);
    var r=117;var b=240;
    var multiplier=gains[mi]*256+adjacent[ji];
    var offset=-(gains[mi]-1)*128+offsets[di];
    for(var x=0;x<32;x++) {
        var g=120+(x%16);
        input.setPixel32(x,0,(a<<24)|(r<<16)|(g<<8)|b);
    }
    var sourceBlack=new flash.display.BitmapData(32,1,false,0);sourceBlack.draw(input);
    var output=new flash.display.BitmapData(32,1,true,0);
    var cxform=new flash.geom.ColorTransform(0.5,multiplier/256,1,opacities[oi]/100,8,offset,-4,0);
    output.draw(input,new flash.geom.Matrix(),cxform,"normal",new flash.geom.Rectangle(0,0,32,1),false);
    var black=new flash.display.BitmapData(32,1,false,0);black.draw(output);
    var row=[id,a,multiplier,offset,opacities[oi]];
    for(var x=0;x<32;x++)row.push(input.getPixel32(x,0),sourceBlack.getPixel32(x,0),output.getPixel32(x,0),black.getPixel32(x,0));
    emit("row",row.join(","));id++;
    input.dispose();sourceBlack.dispose();output.dispose();black.dispose();
}
emit("done","ok");fscommand("quit");
