stop();
var seq = 0;
function emit(k,v) { trace("AIREF|filter-color-arithmetic-ramp-r12|" + (seq++) + "|0|0|0|" + k + "|" + v); }
for(var opacityIndex = 0; opacityIndex < 2; opacityIndex++) {
 for(var mode = 0; mode < 4; mode++) {
  var row = "";
  var blackRow = "";
  for(var value = 0; value < 256; value++) {
   var wrap = _root.createEmptyMovieClip("wrap",1);
   var m = wrap.createEmptyMovieClip("m",1);
   var source = mode == 2 ? (204 << 16) | (value << 8) | 170 : (value << 16) | (127 << 8) | 170;
   m.beginFill(source,opacityIndex == 0 ? 100 : 80);
   m.moveTo(0,0);m.lineTo(2,0);m.lineTo(2,2);m.lineTo(0,2);m.endFill();
   var r = mode == 0 || mode == 1 ? -0.5946631 : (mode == 3 ? 0.10156211 : 0);
   var g = mode == 0 || mode == 2 ? 1.0937881 : 0;
   var b = mode == 0 ? 0.5008749 : 0;
   var offset = mode == 0 ? 9 : (mode == 1 ? 128 : 0);
   m.filters = [new flash.filters.ColorMatrixFilter([r,g,b,0,offset,0,1,0,0,0,0,0,1,0,0,0,0,0,1,0])];
   var bitmap = new flash.display.BitmapData(2,2,true,0);
   bitmap.draw(wrap);
   var black = new flash.display.BitmapData(2,2,false,0);
   black.draw(bitmap);
   row += "," + bitmap.getPixel32(0,0);
   blackRow += "," + black.getPixel32(0,0);
   black.dispose();bitmap.dispose();wrap.removeMovieClip();
  }
  emit("color",(opacityIndex == 0 ? 100 : 80)+","+mode+row);
  emit("black",(opacityIndex == 0 ? 100 : 80)+","+mode+blackRow);
 }
}
emit("done","ok");fscommand("quit");
