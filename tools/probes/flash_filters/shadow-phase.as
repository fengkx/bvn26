stop();
var seq = 0;
function emit(k, v) { trace("AIREF|shadow-phase|" + (seq++) + "|0|0|0|" + k + "|" + v); }
var angles = [-45,45,135,225];
var distances = [0.125,0.5,1,2];
var offsets = [-0.000001,0,0.000001];
for (var a=0;a<4;a++) for(var d=0;d<4;d++) for(var j=0;j<3;j++) {
    var wrap = createEmptyMovieClip("wrap",1);
    var m = wrap.createEmptyMovieClip("m",1);
    m.beginFill(0xffffff,100);
    m.moveTo(8,8);m.lineTo(9,8);m.lineTo(9,9);m.lineTo(8,9);m.endFill();
    var f = new flash.filters.DropShadowFilter(distances[d]+offsets[j],angles[a],0,1,0,0,1,1,false,false,true);
    m.filters = [f];
    var b = new flash.display.BitmapData(20,20,true,0);
    b.draw(wrap);
    var pixels=[];
    for(var y=5;y<12;y++) for(var x=5;x<12;x++) pixels.push(b.getPixel32(x,y)>>>24);
    emit("phase",angles[a]+","+distances[d]+","+j+","+f.angle+","+f.distance+","+pixels.join(","));
    b.dispose();wrap.removeMovieClip();
}
emit("done","ok");fscommand("quit");
