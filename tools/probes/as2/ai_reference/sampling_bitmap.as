// Capture synchronously before the root observer's terminal boundary.
_root.aiBitmapSample = function()
{
   if(_root.aiFight < 0) return;
   var image = new flash.display.BitmapData(600,400,false,0);
   image.draw(_root);
   _root.aiEvent("bitmap_begin","600,400,RGBA8,opaque-black,root-observer");
   for(var y=0;y<400;y++)
   {
      var row="";
      var last=image.getPixel32(0,y);
      var count=1;
      for(var x=1;x<=600;x++)
      {
         var value=x<600 ? image.getPixel32(x,y) : -1;
         if(x<600 && value==last) count++;
         else
         {
            // AVM1 bitwise results are signed; encode the opaque alpha explicitly.
            var hex=(last & 0xffffff).toString(16);
            while(hex.length<6) hex="0"+hex;
            hex="ff"+hex;
            row+=hex+":"+count+";";
            last=value;
            count=1;
         }
      }
      _root.aiEvent("bitmap_row",y+","+row);
   }
   image.dispose();
   _root.aiEvent("bitmap_end","400");
};
