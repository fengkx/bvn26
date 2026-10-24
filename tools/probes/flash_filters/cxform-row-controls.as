stop();
var seq=0;
function emit(k,v) { trace("AIREF|cxform-row-controls-r39|"+(seq++)+"|0|0|0|"+k+"|"+v); }
var widths=[15,16,17,19,20];var starts=[4,5,7];var translations=[-3,0,1];
var alphas=[7,135,231];var opacities=[25,50,100];var id=0;
for(var pattern=0;pattern<2;pattern++)for(var ai=0;ai<3;ai++)for(var oi=0;oi<3;oi++)
for(var wi=0;wi<5;wi++)for(var si=0;si<3;si++)for(var ti=0;ti<3;ti++) {
    var input=new flash.display.BitmapData(48,1,true,0);
    for(var sx=0;sx<48;sx++) {
        // Independent green ramp around alpha135 / premultiplied green104;
        // the impulse row holds the other channels and all other texels fixed.
        var g=pattern==0 ? 192+sx%16 : (sx%8==3 ? 197 : 196);
        input.setPixel32(sx,0,(alphas[ai]<<24)|(70<<16)|(g<<8)|236);
    }
    var sourceBlack=new flash.display.BitmapData(48,1,false,0);sourceBlack.draw(input);
    var output=new flash.display.BitmapData(32,1,true,0);
    var matrix=new flash.geom.Matrix();matrix.translate(translations[ti],0);
    var cxform=new flash.geom.ColorTransform(0.5,0.75,1,opacities[oi]/100,8,0,-4,0);
    var clip=new flash.geom.Rectangle(starts[si],0,widths[wi],1);
    output.draw(input,matrix,cxform,"normal",clip,false);
    var black=new flash.display.BitmapData(32,1,false,0);black.draw(output);
    var row=[id,pattern,alphas[ai],opacities[oi],widths[wi],starts[si],translations[ti]];
    for(var x=0;x<32;x++) {
        var sourceX=x-translations[ti];
        row.push(sourceX>=0 && sourceX<48 ? input.getPixel32(sourceX,0) : 0);
        row.push(sourceX>=0 && sourceX<48 ? sourceBlack.getPixel32(sourceX,0) : -16777216);
        row.push(output.getPixel32(x,0),black.getPixel32(x,0));
    }
    emit("row",row.join(","));
    input.dispose();sourceBlack.dispose();output.dispose();black.dispose();id++;
}
emit("done","ok");fscommand("quit");
