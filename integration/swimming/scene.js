(()=>{
function draw({ctx,race,pool,atlas,trainers,pokemon,avatar,now,direction,fx}){
 function texture(part,x,y,w,h){
  if(!atlas?.complete||!atlas.naturalWidth)return false;
  const size=atlas.naturalWidth/2;
  ctx.drawImage(atlas,(part%2)*size,Math.floor(part/2)*size,size,size,x,y,w,h);return true;
 }
 const count=Math.min(4,Math.max(2,race.players.length)),teams=race.teams.length?race.teams:Array.from({length:count},(_,i)=>({id:i,members:race.players.filter((_,j)=>j%count===i),stage:0,distance:0,camera:0}));
 const width=440/teams.length,up=direction==='up';
 ctx.fillStyle='#d2d9d4';ctx.fillRect(0,0,540,900);
 for(let y=0;y<900;y+=30){ctx.strokeStyle='#9aa9ab';ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(540,y);ctx.stroke();}
 texture(3,0,0,50,900);texture(3,490,0,50,900);
 for(const t of teams){
  const left=50+t.id*width,x=left+width/2;
  const target=Math.max(0,Math.min(2220,t.distance-90));t.camera=(t.camera||0)+(target-(t.camera||0))*.08;
  const camera=t.camera,yAt=m=>up?650-(m-camera)*1.5 :260+(m-camera)*1.5,offset=(camera*1.5)%900;
  ctx.save();ctx.beginPath();ctx.rect(left,0,width,900);ctx.clip();
  ctx.fillStyle='#1b94b3';ctx.fillRect(left,0,width,900);
  ctx.imageSmoothingEnabled=false;
  for(let ty=-180;ty<900;ty+=180){
   const y=ty+(up?offset:-offset)%180;
   if(!texture(0,left,y,width,180)&&pool.complete&&pool.naturalWidth)ctx.drawImage(pool,left,y,width,180);
  }
  for(let m=Math.floor(camera/50)*50;m<camera+650;m+=50){const y=yAt(m);if(m>2400||y<0||y>900)continue;ctx.strokeStyle='#07597a55';ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(left+12,y);ctx.lineTo(left+width-12,y);ctx.stroke();ctx.font='bold 11px "Stadium Local", sans-serif';ctx.textAlign='center';ctx.fillStyle='#08425b99';ctx.fillText(m+' m',x,y-7);}
  const finish=yAt(2400);
  if(finish>0&&finish<900){
   ctx.fillStyle='#c9d1cb';if(up)ctx.fillRect(left,0,width,finish);else ctx.fillRect(left,finish,width,900-finish);
   ctx.save();ctx.beginPath();ctx.rect(left,up?0:finish,width,up?finish:900-finish);ctx.clip();
   for(let ty=-100;ty<1000;ty+=150)texture(1,left,ty,width,150);
   texture(2,left,up?finish-130:finish,width,130);ctx.restore();
   ctx.strokeStyle='#84979b';for(let y=up?finish-30:finish+30;up?y>0:y<900;y+=up?-30:30){ctx.beginPath();ctx.moveTo(left,y);ctx.lineTo(left+width,y);ctx.stroke();}
   for(let i=0;i<Math.ceil(width/12);i++){ctx.fillStyle=i%2?'#152b39':'#fff8e5';ctx.fillRect(left+i*12,finish-5,12,10);}
   ctx.fillStyle='#172d3b';ctx.font='bold 12px "Stadium Local", sans-serif';ctx.textAlign='center';ctx.fillText('META · 2400 m',x,finish+(up?-15:20));
   const coach=t.members.at(-1),image=coach&&trainers[coach.id%trainers.length];if(image?.complete){const bounce=Math.abs(Math.sin(now*5+t.id))*8;ctx.imageSmoothingEnabled=false;ctx.drawImage(image,x-30,finish+(up?-100:38)-bounce,60,60);}
  }
  const p=t.members[t.stage];
  if(p){
   let y=race.phase==='lobby'?350:yAt(t.distance);if(t.finished)y=finish+(up?-30:30);
   if(race.phase==='race'&&race.time<.8)y-=Math.sin(race.time/.8*Math.PI)*40;
   pokemon(p,x,y,now,race.phase==='race'&&!t.finished);avatar(p,x,y-60);
   window.SwimShow?.effect(ctx,t,p,x,y,now,race,fx);
   ctx.font='18px "Stadium Local", sans-serif';ctx.textAlign='center';ctx.strokeStyle='#163747';ctx.lineWidth=3;ctx.fillStyle='white';ctx.strokeText(p.user,x,y+45,width-14);ctx.fillText(p.user,x,y+45,width-14);
   ctx.fillStyle='#244459';ctx.fillRect(x-28,y-39,56,4);ctx.fillStyle='#a9e284';ctx.fillRect(x-28,y-39,56*p.hp/100,4);ctx.fillStyle='#ffc768';ctx.fillRect(x-28,y-32,56*p.sp/100,3);
   for(let i=0;i<t.members.length;i++)if(i!==t.stage){
    const point=i<t.stage?2400*(i+1)/t.members.length:2400*i/t.members.length;
    const py=race.phase==='lobby'?350+i*110:yAt(point);if(py<130||py>850)continue;
    const member=t.members[i];pokemon(member,x,py,now,false);avatar(member,x,py-44,13);ctx.textAlign='center';ctx.font='17px "Stadium Local", sans-serif';ctx.fillStyle='#fff4d6';ctx.strokeStyle='#082335';ctx.lineWidth=3;ctx.strokeText(member.user,x,py+34,width-14);ctx.fillText(member.user,x,py+34,width-14);ctx.font='11px "Stadium Local", sans-serif';const label=i<t.stage?'RELEVO LISTO':'ESPERANDO';ctx.strokeText(label,x,py+53,width-14);ctx.fillText(label,x,py+53,width-14);
   }
   if(t.relayUntil>race.time){ctx.font='bold 12px "Stadium Local", sans-serif';ctx.strokeStyle='#082335';ctx.lineWidth=4;ctx.fillStyle='#ffe6a0';ctx.strokeText('¡RELEVO!',x,y+70);ctx.fillText('¡RELEVO!',x,y+70);}
   if(fx.some(f=>(f.from===t.id||f.to===t.id)&&now-f.at<1)){ctx.strokeStyle='#ffe27a';ctx.lineWidth=3;ctx.beginPath();ctx.arc(x,y,30+Math.sin(now*20)*5,0,7);ctx.stroke();}
  }
  ctx.fillStyle='#163747dd';ctx.fillRect(left+3,12,width-6,87);ctx.fillStyle='white';ctx.font='bold 11px "Stadium Local", sans-serif';ctx.textAlign='center';ctx.fillText('CARRIL '+(t.id+1),x,31);ctx.fillText(Math.floor(t.distance)+' / 2400 m',x,50);ctx.fillText(t.finished?'LUGAR '+t.place:'RELEVO '+(t.stage+1)+' / '+t.members.length,x,67);const stock=t.stock||p?.stock;if(stock)ctx.fillText('🌹'+stock.rose+' 🌽'+stock.corn+' 🚀'+stock.popular,x,86);
  ctx.restore();
  for(let y=-30;y<940;y+=26){ctx.fillStyle=Math.floor(y/26)%2?'#eee2ca':'#db5548';ctx.beginPath();ctx.ellipse(left,y+(up?offset:-offset)%26,4,8,0,0,7);ctx.fill();}
 }
 ctx.strokeStyle='#467384';ctx.lineWidth=6;ctx.strokeRect(48,-4,444,908);
}
window.SwimScene={draw};
})();
