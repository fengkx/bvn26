stop();
var seq = 0;
function emit(k,v) { trace("AIREF|nested-filter-r38|"+(seq++)+"|0|0|0|"+k+"|"+v); }
function bitmap(w,h,c,a) { return new flash.display.BitmapData(w,h,true,(a<<24)|c); }
function drawAt(target,source,x,y,opacity,cx) {
    var matrix = new flash.geom.Matrix();
    matrix.translate(x,y);
    var transform = new flash.geom.ColorTransform(cx ? 0.5 : 1,cx ? 0.75 : 1,1,opacity/100,cx ? 8 : 0,0,cx ? -4 : 0,0);
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
var alphas = [0,128,255];
var children = [25,100];var parents = [50,100];var id=0;
for(var profile=0;profile<2;profile++) for(var ai=0;ai<3;ai++)
for(var ci=0;ci<2;ci++) for(var pi=0;pi<2;pi++) for(var cx=0;cx<2;cx++) {
    var back=bitmap(24,24,0x3355cc,alphas[ai]);
    var middle=bitmap(16,16,0x81d3ef,128);
    var a=bitmap(8,8,0x46c4ec,63);var b=bitmap(4,4,0xff8001,191);
    var sentinel=bitmap(2,24,0xff8001,127);
    var childInput=bitmap(12,12,0,0);
    drawAt(childInput,a,2,2,100,0);drawAt(childInput,b,4,4,100,0);
    var child=bitmap(12,12,0,0);
    var cf=profile==0 ? new flash.filters.GlowFilter(0x51d3ef,1,5,5,1,1,false,false) : new flash.filters.BlurFilter(5,5,1);
    child.applyFilter(childInput,childInput.rectangle,new flash.geom.Point(0,0),cf);
    var parentInput=bitmap(18,18,0,0);
    drawAt(parentInput,middle,1,1,100,0);drawAt(parentInput,child,3,3,children[ci],cx);
    var parent=bitmap(18,18,0,0);
    var pf=profile==0 ? new flash.filters.BlurFilter(3,3,1) : new flash.filters.GlowFilter(0x5de1f4,1,3,3,1,1,false,false);
    parent.applyFilter(parentInput,parentInput.rectangle,new flash.geom.Point(0,0),pf);
    var result=bitmap(24,24,0,0);
    drawAt(result,back,0,0,100,0);drawAt(result,parent,1,1,parents[pi],cx);drawAt(result,sentinel,10,0,100,0);
    emit("case",[id,profile,alphas[ai],children[ci],parents[pi],cx].join(","));
    emit("inputs",[id].concat(sourcePixel(back),sourcePixel(middle),sourcePixel(a),sourcePixel(b),sourcePixel(sentinel)).join(","));
    dump(id,"child_input",childInput);dump(id,"child_filter",child);
    dump(id,"parent_input",parentInput);dump(id,"parent_filter",parent);dump(id,"final",result);
    back.dispose();middle.dispose();a.dispose();b.dispose();sentinel.dispose();
    childInput.dispose();child.dispose();parentInput.dispose();parent.dispose();result.dispose();id++;
}
emit("done","ok");fscommand("quit");
