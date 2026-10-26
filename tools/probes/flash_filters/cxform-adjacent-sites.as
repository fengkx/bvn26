stop();
var seq=0;
function emit(k,v) { trace("AIREF|cxform-adjacent-sites-r45|"+(seq++)+"|0|0|0|"+k+"|"+v); }
// Keep each r44 site's complete row and transform; vary alpha and one input byte independently.
var sites=[[49,13,2049,-896,67],[51,0,2048,-895,100],[204,9,1024,-385,100]];
var id=0;
for(var si=0;si<sites.length;si++)for(var da=-4;da<=4;da++)for(var dg=-8;dg<=8;dg++) {
    var a=sites[si][0]+da;var input=new flash.display.BitmapData(32,1,true,0);
    var r=117;var b=240;
    var multiplier=sites[si][2];
    var offset=sites[si][3];
    for(var x=0;x<32;x++) {
        var g=120+(x%16)+(x==sites[si][1] ? dg : 0);
        input.setPixel32(x,0,(a<<24)|(r<<16)|(g<<8)|b);
    }
    var sourceBlack=new flash.display.BitmapData(32,1,false,0);sourceBlack.draw(input);
    var output=new flash.display.BitmapData(32,1,true,0);
    var cxform=new flash.geom.ColorTransform(0.5,multiplier/256,1,sites[si][4]/100,8,offset,-4,0);
    output.draw(input,new flash.geom.Matrix(),cxform,"normal",new flash.geom.Rectangle(0,0,32,1),false);
    var black=new flash.display.BitmapData(32,1,false,0);black.draw(output);
    var row=[id,si,a,dg,multiplier,offset,sites[si][4]];
    for(var x=0;x<32;x++)row.push(input.getPixel32(x,0),sourceBlack.getPixel32(x,0),output.getPixel32(x,0),black.getPixel32(x,0));
    emit("row",row.join(","));id++;
    input.dispose();sourceBlack.dispose();output.dispose();black.dispose();
}
emit("done","ok");fscommand("quit");
