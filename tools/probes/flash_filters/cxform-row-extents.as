stop();
var seq=0;
function emit(k,v) { trace("AIREF|cxform-row-extents-r40|"+(seq++)+"|0|0|0|"+k+"|"+v); }
var widths=[34,35,47,63,64,65,127,128,129,255,256,257,511,512,513];
var starts=[0,3];var translations=[-590,-15,0,11,590];
var alphas=[135,197];var opacities=[50,100];var id=0;
for(var ai=0;ai<2;ai++)for(var oi=0;oi<2;oi++)for(var wi=0;wi<15;wi++)
for(var si=0;si<2;si++)for(var ti=0;ti<5;ti++) {
    var input=new flash.display.BitmapData(600,1,true,0);
    for(var sx=0;sx<600;sx++)input.setPixel32(sx,0,(alphas[ai]<<24)|(70<<16)|((192+sx%16)<<8)|236);
    var sourceBlack=new flash.display.BitmapData(600,1,false,0);sourceBlack.draw(input);
    var output=new flash.display.BitmapData(640,1,true,0);
    var matrix=new flash.geom.Matrix();matrix.translate(translations[ti],0);
    var cxform=new flash.geom.ColorTransform(0.5,0.75,1,opacities[oi]/100,8,0,-4,0);
    output.draw(input,matrix,cxform,"normal",new flash.geom.Rectangle(starts[si],0,widths[wi],1),false);
    var black=new flash.display.BitmapData(640,1,false,0);black.draw(output);
    // Chunk trace payloads, not draw calls: preserve the whole native scan row.
    for(var base=0;base<640;base+=32) {
        var row=[id,alphas[ai],opacities[oi],widths[wi],starts[si],translations[ti],base];
        for(var x=base;x<base+32;x++) {
            var sx=x-translations[ti];
            row.push(sx>=0 && sx<600 ? input.getPixel32(sx,0) : 0);
            row.push(sx>=0 && sx<600 ? sourceBlack.getPixel32(sx,0) : -16777216);
            row.push(output.getPixel32(x,0),black.getPixel32(x,0));
        }
        emit("row",row.join(","));
    }
    id++;input.dispose();sourceBlack.dispose();output.dispose();black.dispose();
}
emit("done","ok");fscommand("quit");
