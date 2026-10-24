stop();
var seq = 0;
function emit(k,v) { trace("AIREF|nested-materialized-r37|"+(seq++)+"|0|0|0|"+k+"|"+v); }
function bitmap(w,h,c,a) { return new flash.display.BitmapData(w,h,true,(a<<24)|c); }
function drawAt(target,source,x,y,opacity) {
    var matrix = new flash.geom.Matrix();
    matrix.translate(x,y);
    var transform = new flash.geom.ColorTransform(1,1,1,opacity/100,0,0,0,0);
    target.draw(source,matrix,transform,"normal",undefined,false);
}
function sourcePixel(b) {
    var black = new flash.display.BitmapData(1,1,false,0);
    black.draw(b);
    var result = [b.getPixel32(0,0),black.getPixel32(0,0)];
    black.dispose();return result;
}
function dump(id,stage,b) {
    var black = new flash.display.BitmapData(b.width,b.height,false,0);
    black.draw(b);
    for(var y=0;y<b.height;y++) {
        var row = [id,stage,y];
        for(var x=0;x<b.width;x++) row.push(b.getPixel32(x,y),black.getPixel32(x,y));
        emit("row",row.join(","));
    }
    black.dispose();
}
var palettes = [[0x3355cc,0x81d3ef,0x46c4ec,0xff8001],[0xffffff,0x017ffe,0xcc80aa,0x7f0180]];
var alphas = [0,1,64,128,254,255];
var opacity = [0,1,25,50,99,100];
var id = 0;
for(var pi=0;pi<palettes.length;pi++) for(var ai=0;ai<alphas.length;ai++)
for(var ci=0;ci<opacity.length;ci++) for(var oi=0;oi<opacity.length;oi++) {
    var c = palettes[pi];
    var back = bitmap(16,8,c[0],alphas[ai]);
    var middle = bitmap(12,8,c[1],128);
    var leafA = bitmap(8,8,c[2],63);
    var leafB = bitmap(4,4,c[3],191);
    var sentinel = bitmap(2,8,c[3],127);
    // Actual independently allocated byte buffers; no cacheAsBitmap inference.
    var child = bitmap(8,8,0,0);
    drawAt(child,leafA,0,0,100);
    drawAt(child,leafB,2,2,100);
    var parent = bitmap(12,8,0,0);
    drawAt(parent,middle,0,0,100);
    drawAt(parent,child,2,0,opacity[ci]);
    var result = bitmap(16,8,0,0);
    drawAt(result,back,0,0,100);
    drawAt(result,parent,2,0,opacity[oi]);
    drawAt(result,sentinel,6,0,100);
    emit("case",[id,pi,alphas[ai],opacity[ci],opacity[oi]].join(","));
    emit("inputs",[id].concat(sourcePixel(back),sourcePixel(middle),sourcePixel(leafA),sourcePixel(leafB),sourcePixel(sentinel)).join(","));
    dump(id,"child",child); dump(id,"parent",parent); dump(id,"final",result);
    back.dispose();middle.dispose();leafA.dispose();leafB.dispose();sentinel.dispose();
    child.dispose();parent.dispose();result.dispose();
    id++;
}
emit("done","ok");fscommand("quit");
