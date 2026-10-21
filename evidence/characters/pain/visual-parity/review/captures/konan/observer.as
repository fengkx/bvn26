stop();var seq=0;var tick=0;var cases=[{id:"fighters-konan-clock-3",samples:[0,3],scale:0.3172550611074993,x:168.8851666515264,y:214.45554610915258},{id:"fighters-konan-clock-284",samples:[0,24,25,28],scale:1,x:303.1,y:189.825},{id:"fighters-konan-clock-344",samples:[0,44,45,48],scale:1,x:300.96509,y:208.48033965},{id:"fighters-konan-clock-399",samples:[0,39,40,43],scale:0.7553489232689384,x:296.6324833912532,y:191.95476329752034},{id:"fighters-konan-blend-563-28-471-911-4",samples:[0,5,9,12],scale:1,x:314.40207045,y:239.62469101}];
function emit(k,v){trace("AIREF|component-konan-337c8a4a|"+(seq++)+"|0|"+tick+"|0|"+k+"|"+v);}
function clocks(mc,path){emit("clock",path+","+mc._currentframe);for(var k in mc){var c=mc[k];if(typeof(c)=="movieclip" && c._parent==mc){var depth=c.getDepth();if(depth<0)depth+=16384;clocks(c,path+"/"+depth);}}}
function capture(mc,item){
 var b=new flash.display.BitmapData(600,400,false,6316128);var m=new flash.geom.Matrix(item.scale,0,0,item.scale,item.x,item.y);b.draw(mc,m);
 for(var y=0;y<400;y++){var row="";var last=b.getPixel(0,y);var count=1;for(var x=1;x<=600;x++){var pixel=x<600?b.getPixel(x,y):-1;if(pixel==last)count++;else{row+=count.toString(16)+":"+last.toString(16)+",";count=1;last=pixel;}}emit("pixels",item.id+","+y+","+row);}b.dispose();
}
function observe(){for(var i=0;i<cases.length;i++){var mc=_root["case"+i];clocks(mc,cases[i].id);for(var j=0;j<cases[i].samples.length;j++)if(cases[i].samples[j]==tick)capture(mc,cases[i]);}}
for(var i=0;i<cases.length;i++){var mc=_root.attachMovie("case"+i,"case"+i,i+1);mc.gotoAndStop(1);}
observe();
_root.onEnterFrame=function(){tick++;if(tick==10 || tick==20){for(var i=0;i<cases.length;i++)_root["case"+i].gotoAndStop(tick==10?2:1);}observe();if(tick>=100){emit("done","ok");fscommand("quit");}};
