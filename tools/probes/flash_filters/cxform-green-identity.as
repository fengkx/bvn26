stop();
var seq=0;
function emit(k,v) { trace("AIREF|cxform-green-identity-r42|"+(seq++)+"|0|0|0|"+k+"|"+v); }
// r40 failing alphas, plus the retained 7/93/135/231 controls.
var alphas=[6,7,12,14,15,24,28,30,33,35,41,43,45,47,49,51,53,55,59,61,63,67,71,75,79,87,91,93,95,103,107,111,119,135,143,151,159,167,175,183,191,199,207,223,231,247];
var multipliers=[255,256,257];var offsets=[0];var opacities=[33,67,100];
var id=0;
for(var ai=0;ai<alphas.length;ai++)for(var mi=0;mi<multipliers.length;mi++)
for(var di=0;di<offsets.length;di++)for(var oi=0;oi<opacities.length;oi++) {
    var a=alphas[ai];var input=new flash.display.BitmapData(32,1,true,0);
    // At alpha14, green12 gives the exact residual [5,12,13,14];
    // at alpha135, green108 gives [62,108,127,135]. Readback verifies both.
    var r=a==14 ? 91 : 117;var b=a==14 ? 237 : 240;
    for(var x=0;x<32;x++) {
        var g=Math.round(Math.min(a,(x+1)*4)*255/a);
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
