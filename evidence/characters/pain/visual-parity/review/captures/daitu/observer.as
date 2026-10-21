stop();var seq=0;var tick=0;var cases=[{id:"fighters-daitu-clock-3",samples:[0,3],scale:0.6065542410674882,x:204.7016591842629,y:209.70008532032088},{id:"fighters-daitu-clock-275",samples:[0,63,64,67],scale:0.8038585209003215,x:54.01929260450163,y:94.69453376205789},{id:"fighters-daitu-blend-458-27-177-439-4",samples:[0,5,9,12],scale:1,x:295.15,y:266.0},{id:"fighters-daitu-blend-458-30-177-439-4",samples:[0,5,9,12],scale:1,x:295.15,y:266.0},{id:"fighters-daitu-blend-458-28-275-548-8",samples:[0,34,67,70],scale:0.8038585209003215,x:92.6848874598071,y:245.77974276527328}];
function emit(k,v){trace("AIREF|component-daitu-ccdb9e05|"+(seq++)+"|0|"+tick+"|0|"+k+"|"+v);}
function clocks(mc,path){emit("clock",path+","+mc._currentframe);for(var k in mc){var c=mc[k];if(typeof(c)=="movieclip" && c._parent==mc){var depth=c.getDepth();if(depth<0)depth+=16384;clocks(c,path+"/"+depth);}}}
function capture(mc,item){
 var b=new flash.display.BitmapData(600,400,false,6316128);var m=new flash.geom.Matrix(item.scale,0,0,item.scale,item.x,item.y);b.draw(mc,m);
 for(var y=0;y<400;y++){var row="";var last=b.getPixel(0,y);var count=1;for(var x=1;x<=600;x++){var pixel=x<600?b.getPixel(x,y):-1;if(pixel==last)count++;else{row+=count.toString(16)+":"+last.toString(16)+",";count=1;last=pixel;}}emit("pixels",item.id+","+y+","+row);}b.dispose();
}
function observe(){for(var i=0;i<cases.length;i++){var mc=_root["case"+i];clocks(mc,cases[i].id);for(var j=0;j<cases[i].samples.length;j++)if(cases[i].samples[j]==tick)capture(mc,cases[i]);}}
for(var i=0;i<cases.length;i++){var mc=_root.attachMovie("case"+i,"case"+i,i+1);mc.gotoAndStop(1);}
observe();
_root.onEnterFrame=function(){tick++;if(tick==10 || tick==20){for(var i=0;i<cases.length;i++)_root["case"+i].gotoAndStop(tick==10?2:1);}observe();if(tick>=100){emit("done","ok");fscommand("quit");}};
