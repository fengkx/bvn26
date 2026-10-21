stop();var seq=0;var tick=0;var cases=[{id:"fighters-byakuya-clock-14",samples:[0,8,9,12,18,19,22,97,98,100],scale:1,x:271.0,y:167.5},{id:"fighters-byakuya-clock-33",samples:[0,8,9,12,18,19,22,97,98,100],scale:1,x:279.475,y:176.1},{id:"fighters-byakuya-clock-51",samples:[0,8,9,12,18,19,22,97,98,100],scale:1,x:267.5,y:127.0},{id:"fighters-byakuya-clock-66",samples:[0,8,9,12,18,19,22,97,98,100],scale:1,x:300.0,y:200.0},{id:"fighters-byakuya-clock-100",samples:[0,8,9,12,18,19,22,97,98,100],scale:1,x:231.75,y:127.35},{id:"fighters-byakuya-clock-588",samples:[0,8,9,12,18,19,22,97,98,100],scale:1,x:237.075,y:161.65},{id:"fighters-byakuya-clock-617",samples:[0,8,9,12,18,19,22,97,98,100],scale:1,x:246.5,y:129.0},{id:"fighters-byakuya-clock-618",samples:[0,8,9,12,18,19,22,97,98,100],scale:1,x:251.5,y:129.5}];
function emit(k,v){trace("AIREF|component-Byakuya-45635afd|"+(seq++)+"|0|"+tick+"|0|"+k+"|"+v);}
function clocks(mc,path){emit("clock",path+","+mc._currentframe);for(var k in mc){var c=mc[k];if(typeof(c)=="movieclip" && c._parent==mc){var depth=c.getDepth();if(depth<0)depth+=16384;clocks(c,path+"/"+depth);}}}
function capture(mc,item){
 var b=new flash.display.BitmapData(600,400,false,6316128);var m=new flash.geom.Matrix(item.scale,0,0,item.scale,item.x,item.y);b.draw(mc,m);
 for(var y=0;y<400;y++){var row="";var last=b.getPixel(0,y);var count=1;for(var x=1;x<=600;x++){var pixel=x<600?b.getPixel(x,y):-1;if(pixel==last)count++;else{row+=count.toString(16)+":"+last.toString(16)+",";count=1;last=pixel;}}emit("pixels",item.id+","+y+","+row);}b.dispose();
}
function observe(){for(var i=0;i<cases.length;i++){var mc=_root["case"+i];clocks(mc,cases[i].id);for(var j=0;j<cases[i].samples.length;j++)if(cases[i].samples[j]==tick)capture(mc,cases[i]);}}
for(var i=0;i<cases.length;i++){var mc=_root.attachMovie("case"+i,"case"+i,i+1);mc.gotoAndStop(1);}
observe();
_root.onEnterFrame=function(){tick++;if(tick==10 || tick==20){for(var i=0;i<cases.length;i++)_root["case"+i].gotoAndStop(tick==10?2:1);}observe();if(tick>=100){emit("done","ok");fscommand("quit");}};
