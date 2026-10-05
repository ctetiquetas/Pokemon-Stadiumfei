(()=>{
let muted=false;
function cry(p){if(muted)return;const name=swimData.names[p.species].toLowerCase().replace(/[^a-z0-9]/g,'');const a=new Audio('https://play.pokemonshowdown.com/audio/cries/'+name+'.mp3');a.volume=.55;a.play().catch(()=>{});}
function text(ctx,s,x,y,size=22){ctx.textAlign='center';ctx.font='bold '+size+'px "Stadium Local", sans-serif';ctx.lineWidth=5;ctx.strokeStyle='#08213b';ctx.fillStyle='#fff3c4';ctx.strokeText(s,x,y);ctx.fillText(s,x,y);}
function draw({ctx,race,trainers,pokemon,avatar,now,introUntil,fx,data,muted:isMuted}){
muted=isMuted;
if(now<introUntil){
 const i=Math.min(race.players.length-1,Math.floor((now-(introUntil-race.players.length*1.5))/1.5)),p=race.players[Math.max(0,i)];
 if(!p)return;
 ctx.fillStyle='#061d35ed';ctx.fillRect(0,0,540,900);
 for(let y=0;y<900;y+=70){ctx.strokeStyle='#76daec22';ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(540,y-110);ctx.stroke();}
 text(ctx,'RELEVOS ACUÁTICOS',270,125,28);text(ctx,'CARRIL '+(p.team+1),270,180,22);
 avatar(p,270,285,44);
 const im=trainers[p.id%trainers.length];
 ctx.imageSmoothingEnabled=false;if(im?.complete&&im.naturalWidth)ctx.drawImage(im,120,390,110,110);
 pokemon(p,350,445,now,false);text(ctx,p.user,270,575,Math.min(36,400/Math.max(1,p.user.length)*1.5));text(ctx,data.names[p.species],270,620,23);
 text(ctx,'🌹 ×'+p.stock.rose+'     🌽 ×'+p.stock.corn+'     🚀 ×'+p.stock.popular,270,710,24);
 return;
}
const f=fx.findLast(e=>now-e.at<.65);
if(f){const p=f.player||race.active(race.teams[f.from]);avatar(p,270,145,26);text(ctx,'!',307,155,42);}
}
function effect(ctx,t,p,x,y,now,race,fx){
const kind=p.freezeUntil>race.time?'ice':p.paralyzeUntil>race.time?'electric':p.jetUntil>race.time?'jet':p.slowUntil>race.time?'swirl':p.shieldUntil>race.time?'shield':'';
const recent=fx.findLast(f=>(f.targets||[f.to]).includes(t.id)&&now-f.at<.9);
ctx.save();
if(kind==='ice'){ctx.fillStyle='#cdf6ff88';ctx.strokeStyle='#dcffff';ctx.lineWidth=2;ctx.beginPath();for(let i=0;i<6;i++){const a=i*Math.PI/3;ctx.lineTo(x+Math.cos(a)*32,y+Math.sin(a)*37);}ctx.closePath();ctx.fill();ctx.stroke();text(ctx,'CONGELADO',x,y+68,12);}
if(kind==='electric'){ctx.strokeStyle='#ffe86b';ctx.lineWidth=3;ctx.beginPath();for(let i=0;i<8;i++)ctx.lineTo(x-32+i*9,y+(i%2?-25:25)+Math.sin(now*20)*5);ctx.stroke();text(ctx,'PARALIZADO',x,y+68,12);}
if(kind==='swirl'||recent){ctx.strokeStyle=recent?.move?.kind==='poison'?'#e9a5ff':'#d0ffff';ctx.lineWidth=2;for(let i=0;i<3;i++){ctx.beginPath();ctx.ellipse(x,y+i*9,24+i*5,8,now*3+i,0,7);ctx.stroke();}}
if(kind==='jet'){ctx.strokeStyle='#d9ffff';ctx.lineWidth=3;for(let i=0;i<5;i++){ctx.beginPath();ctx.moveTo(x-16+i*8,y+25);ctx.lineTo(x-20+i*10,y+55+Math.sin(now*18+i)*8);ctx.stroke();}text(ctx,'IMPULSO',x,y+68,12);}
if(kind==='shield'){ctx.strokeStyle='#bcf5ff';ctx.lineWidth=3;ctx.beginPath();ctx.arc(x,y,34,0,7);ctx.stroke();}
ctx.restore();
}
window.SwimShow={draw,cry,effect};
})();
