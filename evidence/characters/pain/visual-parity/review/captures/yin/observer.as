stop();var seq=0;var tick=0;var cases=[{id:"fighters-yin-clock-3",samples:[0,3],scale:0.2511591717887607,x:202.96849357794468,y:207.28828439042172},{id:"fighters-yin-clock-260",samples:[0,15,16,19],scale:0.970873786407767,x:50.0,y:98.54368932038835},{id:"fighters-yin-blend-435-28-260-605-4",samples:[0,9,17,20],scale:0.970873786407767,x:50.43689320388353,y:209.51456310679612}];
function emit(k,v){trace("AIREF|component-yin-f1e49dc6|"+(seq++)+"|0|"+tick+"|0|"+k+"|"+v);}
function clocks(mc,path){emit("clock",path+","+mc._currentframe);for(var k in mc){var c=mc[k];if(typeof(c)=="movieclip" && c._parent==mc){var depth=c.getDepth();if(depth<0)depth+=16384;clocks(c,path+"/"+depth);}}}
function capture(mc,item){
 var b=new flash.display.BitmapData(600,400,false,6316128);var m=new flash.geom.Matrix(item.scale,0,0,item.scale,item.x,item.y);b.draw(mc,m);
 for(var y=0;y<400;y++){var row="";var last=b.getPixel(0,y);var count=1;for(var x=1;x<=600;x++){var pixel=x<600?b.getPixel(x,y):-1;if(pixel==last)count++;else{row+=count.toString(16)+":"+last.toString(16)+",";count=1;last=pixel;}}emit("pixels",item.id+","+y+","+row);}b.dispose();
}
function observe(){for(var i=0;i<cases.length;i++){var mc=_root["case"+i];clocks(mc,cases[i].id);for(var j=0;j<cases[i].samples.length;j++)if(cases[i].samples[j]==tick)capture(mc,cases[i]);}}
for(var i=0;i<cases.length;i++){var mc=_root.attachMovie("case"+i,"case"+i,i+1);mc.gotoAndStop(1);}
observe();
_root.onEnterFrame=function(){tick++;if(tick==10 || tick==20){for(var i=0;i<cases.length;i++)_root["case"+i].gotoAndStop(tick==10?2:1);}observe();if(tick>=100){emit("done","ok");fscommand("quit");}};
