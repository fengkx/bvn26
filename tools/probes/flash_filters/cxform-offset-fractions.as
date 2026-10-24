stop();
var seq=0;
function emit(k,v) { trace("AIREF|cxform-offset-fractions-r46|"+(seq++)+"|0|0|0|"+k+"|"+v); }
var alphas=[49,51,135,204,255];
var offsets=[-513,-512,-511,-257,-256,-255,-1,0,1,255,256,257,511,512,513];
var id=0;
for(var ai=0;ai<alphas.length;ai++)for(var di=0;di<offsets.length;di++) {
    var a=alphas[ai];var d=offsets[di];
    var input=new flash.display.BitmapData(32,1,true,(a<<24)|(117<<16)|(128<<8)|240);
    var sourceBlack=new flash.display.BitmapData(32,1,false,0);sourceBlack.draw(input);
    var output=new flash.display.BitmapData(32,1,true,0);
    var cxform=new flash.geom.ColorTransform(0.5,1,1,1,8,d/256,-4,0);
    output.draw(input,new flash.geom.Matrix(),cxform,"normal",new flash.geom.Rectangle(0,0,32,1),false);
    var black=new flash.display.BitmapData(32,1,false,0);black.draw(output);
    // The property readback separates stored float values from draw consumption.
    var row=[id,a,d,cxform.greenOffset*256];
    for(var x=0;x<32;x++)row.push(input.getPixel32(x,0),sourceBlack.getPixel32(x,0),output.getPixel32(x,0),black.getPixel32(x,0));
    emit("row",row.join(","));id++;
    input.dispose();sourceBlack.dispose();output.dispose();black.dispose();
}
emit("done","ok");fscommand("quit");
