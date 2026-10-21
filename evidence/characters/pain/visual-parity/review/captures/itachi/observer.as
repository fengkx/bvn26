stop();var seq=0;var tick=0;var cases=[{id:"fighters-itachi-clock-3",samples:[0,3],scale:0.59155460255753,x:169.8489624781556,y:254.06901196673607},{id:"fighters-itachi-clock-61",samples:[0,26,27,30],scale:1,x:294.9024755,y:171.725},{id:"fighters-itachi-clock-108",samples:[0,17,18,21],scale:1,x:274.1,y:177.35},{id:"fighters-itachi-clock-181",samples:[0,28,29,32],scale:0.7518796992481203,x:213.1578947368421,y:50.0},{id:"fighters-itachi-clock-203",samples:[0,56,57,60],scale:0.5274261603375527,x:88.73945147679328,y:231.30274261603375},{id:"fighters-itachi-blend-294-28-108-405-4",samples:[0,9,18,21],scale:1,x:157.5,y:191.8},{id:"fighters-itachi-blend-294-32-181-600-4",samples:[0,15,29,32],scale:0.39315463756551244,x:217.72050889220742,y:282.19712894619164},{id:"fighters-itachi-blend-294-30-203-678-6",samples:[0,29,57,60],scale:0.5274261603375527,x:7.383966244725741,y:220.4377637130802}];
function emit(k,v){trace("AIREF|component-itachi-10c09117|"+(seq++)+"|0|"+tick+"|0|"+k+"|"+v);}
function clocks(mc,path){emit("clock",path+","+mc._currentframe);for(var k in mc){var c=mc[k];if(typeof(c)=="movieclip" && c._parent==mc){var depth=c.getDepth();if(depth<0)depth+=16384;clocks(c,path+"/"+depth);}}}
function capture(mc,item){
 var b=new flash.display.BitmapData(600,400,false,6316128);var m=new flash.geom.Matrix(item.scale,0,0,item.scale,item.x,item.y);b.draw(mc,m);
 for(var y=0;y<400;y++){var row="";var last=b.getPixel(0,y);var count=1;for(var x=1;x<=600;x++){var pixel=x<600?b.getPixel(x,y):-1;if(pixel==last)count++;else{row+=count.toString(16)+":"+last.toString(16)+",";count=1;last=pixel;}}emit("pixels",item.id+","+y+","+row);}b.dispose();
}
function observe(){for(var i=0;i<cases.length;i++){var mc=_root["case"+i];clocks(mc,cases[i].id);for(var j=0;j<cases[i].samples.length;j++)if(cases[i].samples[j]==tick)capture(mc,cases[i]);}}
for(var i=0;i<cases.length;i++){var mc=_root.attachMovie("case"+i,"case"+i,i+1);mc.gotoAndStop(1);}
observe();
_root.onEnterFrame=function(){tick++;if(tick==10 || tick==20){for(var i=0;i<cases.length;i++)_root["case"+i].gotoAndStop(tick==10?2:1);}observe();if(tick>=100){emit("done","ok");fscommand("quit");}};
