_root.s274Generation = 0;
_root.s274Life = function(mc, phase)
{
   if(phase == "load") { mc.s274Generation = ++_root.s274Generation; }
   if(phase == "unload" && mc.s274Generation == 2) _root.s274Unloaded2 = true;
   _root.aiEvent("s274_life", phase + "," + String(mc) + "," + mc.getDepth() + "," + mc.s274Generation + "," + mc._currentframe);
};
_root.s274Entry = function(mc)
{
   if(mc.s274Generation == 2 && _root.aiFight == 1) _root.s274RetainedEntry2 = true;
   _root.aiEvent("s274_entry", String(mc) + "," + mc.getDepth() + "," + mc.s274Generation + "," + mc._currentframe);
};
_root.s274State = function(phase, mc)
{
   _root.aiEvent("s274_state", phase + "," + String(mc) + "," + mc.getDepth() + "," + mc.s274Generation + "," + mc._currentframe);
};
_root.s274Sample = function()
{
   var timer = _root.s258Timer;
   _root.s274State("sample", timer.个);
   if(_root.aiFight == 0)
   {
      timer.个.duplicateMovieClip("__s274Control", 100001);
      timer.__s274Control._visible = false;
      _root.aiEvent("s274_control", "created");
   }
   if(_root.aiFight == 1)
   {
      _root.s274State("retained_before", timer.__s274Control);
      timer.__s274Control.gotoAndStop(2);
      timer.__s274Control.gotoAndStop(1);
      _root.s274State("retained_after", timer.__s274Control);
   }
   if(_root.aiFight == 2)
   {
      _root.s274State("replace_before", timer.__s274Control);
      timer.__s274Control.removeMovieClip();
      timer.个.duplicateMovieClip("__s274Control", 100001);
      timer.__s274Control._visible = false;
      _root.aiEvent("s274_control", "replaced");
   }
   if(_root.aiFight == 3)
   {
      _root.s274State("replace_after", timer.__s274Control);
      _root.s274Calibrated = timer.__s274Control.s274Generation == 3
         && _root.s274Unloaded2 == true && _root.s274RetainedEntry2 == true;
   }
   if(_root.aiFight == 5)
   {
      _root.s274State("encoded_retained_before", timer.__s274Control);
      timer.__s274Control.gotoAndStop(2);
      timer.__s274Control.gotoAndStop(1);
      _root.s274State("encoded_retained_after", timer.__s274Control);
   }
   if(_root.aiFight == 6)
   {
      _root.s274State("encoded_replace_before", timer.__s274Control);
      timer.__s274Control.removeMovieClip();
      timer.个.duplicateMovieClip("__s274Control", 100001);
      timer.__s274Control._visible = false;
   }
   if(_root.aiFight == 7) _root.s274State("encoded_replace_after", timer.__s274Control);
   if(_root.aiFight == 8) timer.__s274Control.removeMovieClip();
   _root.aiEvent("s274_boundary", "before");
   _root.s262Snapshot();
   _root.s258Observe("snapshot_before", timer);
   if(_root.aiFight >= 4)
   {
      // This admits only a bounded observation experiment, never a scene image.
      var digit = timer.个;
      var admitted = _root.s274Calibrated == true && typeof(digit) == "movieclip"
         && digit.s274Generation == 1 && digit.getDepth() == -16381
         && digit._totalframes == 10 && timer._currentframe == 1;
      _root.aiEvent("s274_admission", String(admitted));
      _root.s274State("draw_before", digit);
      if(admitted)
      {
         var image = new flash.display.BitmapData(600,400,false,0);
         _root.aiEvent("s274_memory", "draw_before");
         image.draw(_root);
         _root.aiEvent("s274_memory", "draw_after");
         var chars = 0;
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
                  var hex=(last & 0xffffff).toString(16);
                  while(hex.length<6) hex="0"+hex;
                  hex="ff"+hex;
                  row+=hex+":"+count+";";
                  last=value;
                  count=1;
               }
            }
            chars += row.length;
         }
         // Retain only a work-size count; no pixel/row payload leaves memory.
         _root.aiEvent("s274_encoded_size", String(chars));
         image.dispose();
         _root.aiEvent("s274_memory", "encoding_after");
      }
      _root.s274State("draw_after", digit);
   }
   _root.s258Observe("snapshot_after", timer);
   _root.aiEvent("s274_boundary", "after");
};
