stop();
var seq = 0;
function emit(k,v) { trace("AIREF|RUN|" + (seq++) + "|0|0|0|" + k + "|" + v); }
var coefficients = [-0.5946631,1.0937881,0.5008749,0.4649421,0.50735843,0.027699426,0.10156211,1.6525338,-0.75409585];
for(var opacityIndex = 0; opacityIndex < 2; opacityIndex++) {
 for(var row = 0; row < 3; row++) {
  for(var component = 0; component < 4; component++) {
   var wrap = _root.createEmptyMovieClip("wrap",1);
   var m = wrap.createEmptyMovieClip("m",1);
   m.beginFill(13402026,opacityIndex == 0 ? 100 : 80);
   m.moveTo(40,40);m.lineTo(104,40);m.lineTo(104,104);m.lineTo(40,104);m.endFill();
   var r = component == 0 || component == 3 ? coefficients[row*3] : 0;
   var g = component == 1 || component == 3 ? coefficients[row*3+1] : 0;
   var b = component == 2 || component == 3 ? coefficients[row*3+2] : 0;
   var offset = component == 3 ? 9 : (r < 0 || g < 0 || b < 0 ? 128 : 0);
   var input = new flash.display.BitmapData(160,160,true,0);input.draw(wrap);
   var inputBlack = new flash.display.BitmapData(160,160,false,0);inputBlack.draw(input);
   emit("input",(opacityIndex == 0 ? 100 : 80)+","+row+","+component+","+input.getPixel32(70,70)+","+inputBlack.getPixel32(70,70));
   input.dispose();inputBlack.dispose();
   m.filters = [new flash.filters.ColorMatrixFilter([r,g,b,0,offset,0,1,0,0,0,0,0,1,0,0,0,0,0,1,0])];
   emit("matrix",m.filters[0].matrix.join(","));
   var bitmap = new flash.display.BitmapData(160,160,true,0);
   bitmap.draw(wrap);
   var black = new flash.display.BitmapData(160,160,false,0);
   black.draw(bitmap);
   emit("sample",(opacityIndex == 0 ? 100 : 80)+","+row+","+component+","+bitmap.getPixel32(70,70)+","+black.getPixel32(70,70));
   black.dispose();bitmap.dispose();wrap.removeMovieClip();
  }
 }
}
emit("done","ok");fscommand("quit");
