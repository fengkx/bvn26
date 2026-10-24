stop();
var seq = 0;
function emit(k, v) { trace("AIREF|placement-overlay-grid|" + (seq++) + "|0|0|0|" + k + "|" + v); }
var w = createEmptyMovieClip("w", 1);
var back = new flash.display.BitmapData(256, 256, false, 0);
var front = new flash.display.BitmapData(256, 256, false, 0);
for (var y = 0; y < 256; y++) {
    for (var x = 0; x < 256; x++) {
        back.setPixel(x, y, x * 65793);
        front.setPixel(x, y, y * 65793);
    }
}
w.attachBitmap(back, 1);
var g = w.createEmptyMovieClip("g", 2);
g.attachBitmap(front, 1);
g.blendMode = "overlay";
var result = new flash.display.BitmapData(256, 256, true, 0);
result.draw(w);
for (var y = 0; y < 256; y++) {
    var row = [];
    for (var x = 0; x < 256; x++) { row.push(result.getPixel32(x, y)); }
    emit("row", y + ":" + row.join(","));
}
emit("done", "ok");
fscommand("quit");
