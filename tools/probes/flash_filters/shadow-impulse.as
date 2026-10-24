stop();
var seq = 0;
function emit(k, v) { trace("AIREF|shadow-impulse|" + (seq++) + "|0|0|0|" + k + "|" + v); }
var alphas = [1,64,128,255];
for (var diagonal = 0; diagonal < 2; diagonal++) {
    for (var step = 0; step <= 16; step++) {
        for (var a = 0; a < alphas.length; a++) {
            var wrap = createEmptyMovieClip("wrap",1);
            var m = wrap.createEmptyMovieClip("m",1);
            m.beginFill(16777215,alphas[a]*100/255);
            m.moveTo(8,8); m.lineTo(9,8); m.lineTo(9,9); m.lineTo(8,9); m.endFill();
            var b = new flash.display.BitmapData(20,20,true,0);
            b.draw(wrap);
            var input = b.getPixel32(8,8);
            b.fillRect(b.rectangle,0);
            m.filters = [new flash.filters.DropShadowFilter(step/16*(diagonal?Math.SQRT2:1),diagonal?45:0,0,1,0,0,1,1,false,false,true)];
            b.draw(wrap);
            var pixels = [];
            for (var y=7;y<11;y++) for(var x=7;x<11;x++) pixels.push(b.getPixel32(x,y));
            emit("impulse",diagonal+","+step+","+alphas[a]+","+input+","+pixels.join(","));
            b.dispose(); wrap.removeMovieClip();
        }
    }
}
emit("done","ok"); fscommand("quit");
