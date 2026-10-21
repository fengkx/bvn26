stop();var seq=0;var tick=0;var cases=[{id:"fighters-yihu-clock-14",samples:[0,8,9,12,18,19,22,97,98,100],scale:1,x:264.5,y:175.5},{id:"fighters-yihu-clock-33",samples:[0,8,9,12,18,19,22,97,98,100],scale:1,x:252.5,y:176.5},{id:"fighters-yihu-clock-56",samples:[0,8,9,12,18,19,22,97,98,100],scale:1,x:265.0,y:123.0},{id:"fighters-yihu-clock-354",samples:[0,8,9,12,18,19,22,97,98,100],scale:1,x:270.1,y:187.15},{id:"fighters-yihu-clock-531",samples:[0,8,9,12,18,19,22,97,98,100],scale:1,x:270.625,y:164.5},{id:"fighters-yihu-clock-596",samples:[0,8,9,12,18,19,22,97,98,100],scale:1,x:240.0,y:150.0},{id:"fighters-yihu-clock-632",samples:[0,8,9,12,18,19,22,97,98,100],scale:1,x:148.0,y:168.0},{id:"fighters-yihu-clock-637",samples:[0,8,9,12,18,19,22,97,98,100],scale:1,x:280.0,y:189.0}];
function emit(k,v){trace("AIREF|component-yihu-e7c9e017|"+(seq++)+"|0|"+tick+"|0|"+k+"|"+v);}
function clocks(mc,path){emit("clock",path+","+mc._currentframe);for(var k in mc){var c=mc[k];if(typeof(c)=="movieclip" && c._parent==mc){var depth=c.getDepth();if(depth<0)depth+=16384;clocks(c,path+"/"+depth);}}}
function capture(mc,item){
 var b=new flash.display.BitmapData(600,400,false,6316128);var m=new flash.geom.Matrix(item.scale,0,0,item.scale,item.x,item.y);b.draw(mc,m);
 for(var y=0;y<400;y++){var row="";var last=b.getPixel(0,y);var count=1;for(var x=1;x<=600;x++){var pixel=x<600?b.getPixel(x,y):-1;if(pixel==last)count++;else{row+=count.toString(16)+":"+last.toString(16)+",";count=1;last=pixel;}}emit("pixels",item.id+","+y+","+row);}b.dispose();
}
function observe(){for(var i=0;i<cases.length;i++){var mc=_root["case"+i];clocks(mc,cases[i].id);for(var j=0;j<cases[i].samples.length;j++)if(cases[i].samples[j]==tick)capture(mc,cases[i]);}}
for(var i=0;i<cases.length;i++){var mc=_root.attachMovie("case"+i,"case"+i,i+1);mc.gotoAndStop(1);}
observe();
_root.onEnterFrame=function(){tick++;if(tick==10 || tick==20){for(var i=0;i<cases.length;i++)_root["case"+i].gotoAndStop(tick==10?2:1);}observe();if(tick>=100){emit("done","ok");fscommand("quit");}};
