(()=>{
 const backdrop=new Image();backdrop.src='/swimming/victory-pool.png';
 function label(ctx,text,x,y,size,width=460){
  ctx.font=size+'px "Stadium Local", sans-serif';ctx.textAlign='center';ctx.lineWidth=4;ctx.strokeStyle='#062344';ctx.fillStyle='#ffdd60';
  ctx.strokeText(text,x,y,width);ctx.fillText(text,x,y,width);
 }
 function draw({ctx,race,trainers,pokemon,avatar,now}){
  if(race.phase!=='finished')return;
  ctx.fillStyle='#0a2138';ctx.fillRect(0,0,540,900);
  if(backdrop.complete&&backdrop.naturalWidth)ctx.drawImage(backdrop,0,0,540,900);
  ctx.fillStyle='#071c35cc';ctx.fillRect(0,0,540,112);
  label(ctx,'¡CAMPEONES DE RELEVOS!',270,48,36);label(ctx,'CARRIL '+(race.winner+1)+' · 2400 METROS',270,85,23);
  const team=race.teams[race.winner],n=team.members.length;
  const cols=n===1?1:2,rows=Math.ceil(n/cols),cardW=n===1?310:238,cardH=225;
  const top=rows===1?485:385;
  team.members.forEach((p,i)=>{
   const col=i%cols,row=Math.floor(i/cols),count=Math.min(cols,n-row*cols);
   const x=270+(col-(count-1)/2)*256,y=top+row*245;
   ctx.fillStyle='#061d39da';ctx.strokeStyle='#ffe17b88';ctx.lineWidth=2;
   ctx.beginPath();ctx.roundRect(x-cardW/2,y,cardW,cardH,18);ctx.fill();ctx.stroke();
   avatar(p,x,y+43,28);
   const im=trainers[p.id%trainers.length],bounce=Math.abs(Math.sin(now*6+i))*5;
   ctx.imageSmoothingEnabled=false;
   if(im?.complete&&im.naturalWidth)ctx.drawImage(im,x-77,y+88-bounce,64,64);
   pokemon(p,x+42,y+121,now,false);
   label(ctx,p.user,x,y+192,27,cardW-24);
  });
 }
 window.SwimVictory={draw};
})();
