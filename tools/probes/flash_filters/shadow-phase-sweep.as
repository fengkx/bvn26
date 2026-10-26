stop();
var seq = 0;
function emit(k, v) { trace("AIREF|shadow-phase-sweep|" + (seq++) + "|0|0|0|" + k + "|" + v); }
var angles = [-135,-91,-45,-17,0,23,89,135];
var distances = [];
for(var step=0;step<65;step++) distances.push(step/128);
var offsets = [0];
for (var a=0;a<8;a++) for(var d=0;d<65;d++) for(var j=0;j<1;j++) {
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
