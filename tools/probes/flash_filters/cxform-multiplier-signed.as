stop();
var seq=0;
function emit(k,v) { trace("AIREF|cxform-multiplier-signed-r47|"+(seq++)+"|0|0|0|"+k+"|"+v); }
var alphas=[49,51,135,204,255];var centers=[-128,0,128];
var deltas=[-256,-255,-129,-128,-127,-1,0,1,127,128,129,255,256];
var id=0;
for(var ai=0;ai<alphas.length;ai++)for(var ci=0;ci<centers.length;ci++) {
    var a=alphas[ai];var input=new flash.display.BitmapData(32,1,true,(a<<24)|(117<<16)|(128<<8)|240);
    var sourceBlack=new flash.display.BitmapData(32,1,false,0);sourceBlack.draw(input);
    for(var di=0;di<deltas.length;di++) {
        var m=centers[ci]*256+deltas[di];
        var output=new flash.display.BitmapData(32,1,true,0);
        var cxform=new flash.geom.ColorTransform(0.5,m/65536,1,1,8,128,-4,0);
        output.draw(input,new flash.geom.Matrix(),cxform,"normal",new flash.geom.Rectangle(0,0,32,1),false);
        var black=new flash.display.BitmapData(32,1,false,0);black.draw(output);
        var row=[id,a,centers[ci],m,cxform.greenMultiplier*65536];
        for(var x=0;x<32;x++)row.push(input.getPixel32(x,0),sourceBlack.getPixel32(x,0),output.getPixel32(x,0),black.getPixel32(x,0));
        emit("row",row.join(","));id++;output.dispose();black.dispose();
    }
    input.dispose();sourceBlack.dispose();
}
emit("done","ok");fscommand("quit");
