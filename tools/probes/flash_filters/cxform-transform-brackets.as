stop();
var seq=0;
function emit(k,v) { trace("AIREF|cxform-transform-brackets-r46|"+(seq++)+"|0|0|0|"+k+"|"+v); }
// r45 counterexample sources plus center/neighbor alpha controls; every source uses the same transform grid.
var sites=[[49,13,2049,-896,67],[51,0,2048,-895,100],[204,9,1024,-385,100]];
var cases=[[0,0,45,-8],[8,0,45,0],[25,0,46,0],[37,0,47,-5],[42,0,47,0],[57,0,48,-2],[76,0,49,0],[93,0,50,0],[110,0,51,0],[127,0,52,0],[144,0,53,0],[161,1,47,0],[178,1,48,0],[187,1,49,-8],[193,1,49,-2],[198,1,49,3],[203,1,49,8],[212,1,50,0],[227,1,51,-2],[232,1,51,3],[237,1,51,8],[246,1,52,0],[263,1,53,0],[280,1,54,0],[297,1,55,0],[314,2,200,0],[321,2,200,7],[331,2,201,0],[348,2,202,0],[365,2,203,0],[374,2,204,-8],[375,2,204,-7],[377,2,204,-5],[378,2,204,-4],[379,2,204,-3],[380,2,204,-2],[382,2,204,0],[383,2,204,1],[384,2,204,2],[385,2,204,3],[387,2,204,5],[388,2,204,6],[389,2,204,7],[390,2,204,8],[399,2,205,0],[416,2,206,0],[433,2,207,0],[450,2,208,0]];
var multiplierDeltas=[-2,-1,0,1,2];var offsetDeltas=[-256,-1,0,1,256];
var id=0;
for(var ci=0;ci<cases.length;ci++) {
    var ref=cases[ci][0];var si=cases[ci][1];var a=cases[ci][2];var dg=cases[ci][3];
    var input=new flash.display.BitmapData(32,1,true,0);
    for(var x=0;x<32;x++) {
        var g=120+(x%16)+(x==sites[si][1] ? dg : 0);
        input.setPixel32(x,0,(a<<24)|(117<<16)|(g<<8)|240);
    }
    var sourceBlack=new flash.display.BitmapData(32,1,false,0);sourceBlack.draw(input);
    for(var mi=0;mi<multiplierDeltas.length;mi++)for(var di=0;di<offsetDeltas.length;di++) {
        var m=sites[si][2]+multiplierDeltas[mi];var d=sites[si][3]*256+offsetDeltas[di];var op=sites[si][4];
        var output=new flash.display.BitmapData(32,1,true,0);
        var cxform=new flash.geom.ColorTransform(0.5,m/256,1,op/100,8,d/256,-4,0);
        output.draw(input,new flash.geom.Matrix(),cxform,"normal",new flash.geom.Rectangle(0,0,32,1),false);
        var black=new flash.display.BitmapData(32,1,false,0);black.draw(output);
        var row=[id,ref,si,a,dg,m,d,op];
        for(var x=0;x<32;x++)row.push(input.getPixel32(x,0),sourceBlack.getPixel32(x,0),output.getPixel32(x,0),black.getPixel32(x,0));
        emit("row",row.join(","));id++;output.dispose();black.dispose();
    }
    input.dispose();sourceBlack.dispose();
}
emit("done","ok");fscommand("quit");
