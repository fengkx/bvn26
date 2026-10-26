stop();
var seq=0;
function emit(k,v) { trace("AIREF|cxform-alpha-rows-r40|"+(seq++)+"|0|0|0|"+k+"|"+v); }
// Independent straight-byte neighborhoods covering r39 filter counterexamples.
var greens=[140,145,146,147,156,157,158,164,165,166,173,174,175,187,188,189,195,196,197,198,199,200,205,206,207,208,209,210,211,212,213,216];
var opacities=[25,50,100];var id=0;
for(var a=0;a<256;a++)for(var oi=0;oi<3;oi++) {
    var input=new flash.display.BitmapData(32,1,true,0);
    for(var x=0;x<32;x++)input.setPixel32(x,0,(a<<24)|(70<<16)|(greens[x]<<8)|236);
    var sourceBlack=new flash.display.BitmapData(32,1,false,0);sourceBlack.draw(input);
    var output=new flash.display.BitmapData(32,1,true,0);
    var cxform=new flash.geom.ColorTransform(0.5,0.75,1,opacities[oi]/100,8,0,-4,0);
    output.draw(input,new flash.geom.Matrix(),cxform,"normal",new flash.geom.Rectangle(0,0,32,1),false);
    var black=new flash.display.BitmapData(32,1,false,0);black.draw(output);
    var row=[id,a,opacities[oi]];
    for(var x=0;x<32;x++)row.push(input.getPixel32(x,0),sourceBlack.getPixel32(x,0),output.getPixel32(x,0),black.getPixel32(x,0));
    emit("row",row.join(","));id++;
    input.dispose();sourceBlack.dispose();output.dispose();black.dispose();
}
emit("done","ok");fscommand("quit");
