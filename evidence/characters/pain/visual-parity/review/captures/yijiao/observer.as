stop();var seq=0;var tick=0;var cases=[{id:"fighters-yijiao-clock-3",samples:[0,3],scale:0.6322209851123054,x:294.0938105673624,y:212.99526646317202},{id:"fighters-yijiao-clock-189",samples:[0,11,12,15],scale:1,x:178.0,y:155.0},{id:"fighters-yijiao-blend-455-28-189-373-4",samples:[0,6,12,15],scale:1,x:184.5,y:215.899878},{id:"fighters-yijiao-blend-455-28-298-543-5",samples:[0,25,49,52],scale:0.5846923275448276,x:283.5771185869898,y:213.28498947925178},{id:"fighters-yijiao-blend-455-27-368-675-4",samples:[0,5,9,12],scale:1,x:296.35,y:255.9},{id:"fighters-yijiao-blend-455-30-368-675-4",samples:[0,5,9,12],scale:1,x:296.35,y:255.9}];
function emit(k,v){trace("AIREF|component-yijiao-cd51c3c5|"+(seq++)+"|0|"+tick+"|0|"+k+"|"+v);}
function clocks(mc,path){emit("clock",path+","+mc._currentframe);for(var k in mc){var c=mc[k];if(typeof(c)=="movieclip" && c._parent==mc){var depth=c.getDepth();if(depth<0)depth+=16384;clocks(c,path+"/"+depth);}}}
function capture(mc,item){
 var b=new flash.display.BitmapData(600,400,false,6316128);var m=new flash.geom.Matrix(item.scale,0,0,item.scale,item.x,item.y);b.draw(mc,m);
 for(var y=0;y<400;y++){var row="";var last=b.getPixel(0,y);var count=1;for(var x=1;x<=600;x++){var pixel=x<600?b.getPixel(x,y):-1;if(pixel==last)count++;else{row+=count.toString(16)+":"+last.toString(16)+",";count=1;last=pixel;}}emit("pixels",item.id+","+y+","+row);}b.dispose();
}
function observe(){for(var i=0;i<cases.length;i++){var mc=_root["case"+i];clocks(mc,cases[i].id);for(var j=0;j<cases[i].samples.length;j++)if(cases[i].samples[j]==tick)capture(mc,cases[i]);}}
for(var i=0;i<cases.length;i++){var mc=_root.attachMovie("case"+i,"case"+i,i+1);mc.gotoAndStop(1);}
observe();
_root.onEnterFrame=function(){tick++;if(tick==10 || tick==20){for(var i=0;i<cases.length;i++)_root["case"+i].gotoAndStop(tick==10?2:1);}observe();if(tick>=100){emit("done","ok");fscommand("quit");}};
