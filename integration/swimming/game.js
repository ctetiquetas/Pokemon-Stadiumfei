(()=>{
if(new URLSearchParams(location.search).get('window')==='1')document.body.classList.add('obs');const $=id=>document.getElementById(id),ctx=$('pool').getContext('2d'),data=swimData;
const waterIds=[7,8,9,54,55,60,61,62,72,73,79,80,86,87,90,91,98,99,116,117,118,119,120,121,129,130,131,134,138,139,140,141];const water=data.spriteDefinitions.map((d,i)=>waterIds.includes(Number(d[0]))?i:-1).filter(i=>i>=0);let race=new SwimRace.Race(Math.random,water),last=0,camera=0,fx=[],direction='up',musicPhase='';
const pool=new Image();pool.src='/swimming/pool.png';
const atlas=new Image();atlas.src='/swimming/pool-atlas.png';
const sheets=data.spriteDefinitions.map(d=>{const im=new Image();im.src='https://cdn.jsdelivr.net/gh/PMDCollab/SpriteCollab@master/sprite/'+d[0]+'/Walk-Anim.png';return im;});
const trainers=data.trainerSprites.map(src=>{const im=new Image();im.src=src;return im;});
let introUntil=0;
const portraits=new Map(),audio=new Audio();audio.volume=.3;
function message(s){$('message').textContent=s}
function music(phase){if(phase===musicPhase)return;musicPhase=phase;audio.pause();audio.loop=phase==='lobby';audio.src=phase==='lobby'?'/music/select.mp3':phase==='victory'?'/music/victory.mp3':['/pokemon-battle.mp3','/music/battle2.mp3','/music/battle3.mp3','/music/battle4.mp3'][Math.floor(Math.random()*4)];audio.play().catch(()=>{});}
audio.onended=()=>{if(musicPhase==='race'){musicPhase='';music('race');}};
$('mute').onchange=()=>audio.muted=$('mute').checked;
data.names.forEach((name,i)=>{if(!water.includes(i))return;const o=document.createElement('option');o.value=i;o.textContent=name;$('species').append(o)});
function render(){
 const user=$('pilot').value;$('pilot').replaceChildren();$('roster').replaceChildren();
 for(const p of race.players){const o=document.createElement('option');o.value=p.user;o.textContent=p.user;$('pilot').append(o);const row=document.createElement('div');row.className='person';row.textContent=p.user+' · '+data.names[p.species]+' · 🌹 '+p.stock.rose+' 🌽 '+p.stock.corn+' 🚀 '+p.stock.popular;$('roster').append(row);}
 if(race.players.some(p=>p.user===user))$('pilot').value=user;
 $('start').disabled=race.players.length<2||race.phase!=='lobby';
}
function join(user,species,avatar='',testParticipant=true){const r=race.join(user,species,avatar);if(r.ok)r.player.testParticipant=testParticipant;if(r.ok)r.player.dex=Number(data.spriteDefinitions[r.player.species][0]);message(r.ok?'Inscrito: '+r.player.user:r.message);render();return r}
function gift(user,key,count=1){if(race.gift(user,key,count)){message('Regalo guardado para el equipo de '+user);render();}}
$('join').onclick=()=>{music('lobby');join($('user').value,Number($('species').value))};
$('demo').onclick=()=>{if(race.phase!=='lobby')return;for(let i=0;i<16;i++)join('Entrenador'+(i+1),water[i%water.length]);music('lobby');};
let rewardRound=null,starting=false,settling=false;const pendingKey='kafei-swim-pending-prize-v1';
async function reward(payload){const response=await fetch('/swimming-reward',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});const result=await response.json();if(!response.ok)throw Error(result.error||'Error de premios');return result;}
async function settle(payload){settling=true;try{const result=await reward(payload);localStorage.removeItem(pendingKey);message(Object.entries(result.paid).map(([u,n])=>u+': '+n+' K$').join(' · ')+(result.carry?' · Pozo siguiente: '+result.carry+' K$':''));settling=false;}catch(error){message('Premio pendiente: '+error.message);setTimeout(()=>settle(payload),5000);}}
const saved=localStorage.getItem(pendingKey);if(saved){try{settle(JSON.parse(saved));}catch{localStorage.removeItem(pendingKey);}}
$('start').onclick=async()=>{if(starting||settling||race.phase!=='lobby')return;starting=true;try{rewardRound=null;if(race.players.length>=2&&race.players.every(p=>!p.testParticipant)&&!$('auto').checked){rewardRound=(await reward({action:'begin',roster:race.players.map(p=>p.user)})).round;}if(race.start()){introUntil=last+race.players.length*1.5;direction=$('direction').value;music('race');render();message('Relevos repartidos · los taps de todos impulsan al nadador de su equipo.')}else message('Se necesitan al menos dos inscritos.');}catch(error){message(error.message);}finally{starting=false;}};
$('reset').onclick=()=>{if(starting||settling)return;rewardRound=null;race=new SwimRace.Race(Math.random,water);introUntil=0;camera=0;fx=[];$('winner').textContent='';document.querySelectorAll('.gift-side').forEach(el=>el.hidden=false);music('lobby');render();};
$('tap').onclick=()=>{music(race.phase==='lobby'?'lobby':'race');race.tap($('pilot').value,1)};
document.querySelectorAll('[data-gift]').forEach(b=>b.onclick=()=>gift($('pilot').value,b.dataset.gift));
$('view').onclick=()=>document.body.classList.toggle('obs');
const norm=s=>String(s||'').toLowerCase().replace(/^@/,'').trim();
const events=new EventSource('/live-events');
events.onmessage=e=>{const v=JSON.parse(e.data),user=norm(v.user);if(v.type==='control'){if(v.message==='swimming:room')$('reset').click();if(v.message==='swimming:start')$('start').click();return;}
 if(v.type==='comment'&&/^!unir(?:\s|$)/i.test(v.message)){
  const request=norm(v.message.replace(/^!unir\s*!?/i,'')),key=s=>s.normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]/g,'');
  let species=data.names.findIndex((n,i)=>water.includes(i)&&key(n)===key(request));if(species<0)species=water[Math.floor(Math.random()*water.length)];join(user,species,v.avatar,false);return;
 }
 if(v.type==='like')race.tap(user,Number(v.count)||0);
 if(v.type==='gift'){const key=norm(v.gift).replace(/[’']/g,'');gift(user,['rose','rosa'].includes(key)?'rose':['its corn'].includes(key)?'corn':['go popular','hazte popular'].includes(key)?'popular':'',v.count);}
};
function avatar(p,x,y,r=13){if(p.avatar){let im=portraits.get(p.avatar);if(!im){im=new Image();im.src=p.avatar;portraits.set(p.avatar,im)}if(im.complete&&im.naturalWidth){ctx.save();ctx.beginPath();ctx.arc(x,y,r,0,7);ctx.clip();ctx.drawImage(im,x-r,y-r,r*2,r*2);ctx.restore();return;}}ctx.fillStyle='#173e60';ctx.beginPath();ctx.arc(x,y,r,0,7);ctx.fill();ctx.fillStyle='white';ctx.font='bold '+Math.max(10,r)+'px Arial';ctx.textAlign='center';ctx.fillText(p.user.slice(0,2).toUpperCase(),x,y+3);}
function pokemon(p,x,y,now,swim){const d=data.spriteDefinitions[p.species],im=sheets[p.species],frame=Math.floor(now*7)%d[3].length,scale=1.7;
 ctx.save();ctx.imageSmoothingEnabled=false;if(im.complete&&im.naturalWidth){const row=direction==='up'?4:0;ctx.drawImage(im,frame*d[1],row*d[2],d[1],d[2],x-d[1]*scale/2,y-d[2]*scale/2+Math.sin(now*7)*2,d[1]*scale,d[2]*scale);}
 if(swim){ctx.fillStyle='#35b8d44d';ctx.beginPath();ctx.ellipse(x,y+12,26,12,0,0,7);ctx.fill();for(let i=0;i<3;i++){ctx.strokeStyle='#e8ffff88';ctx.lineWidth=1;ctx.beginPath();ctx.ellipse(x,y+20+i*8,17+i*5,4+i*2,0,0,7);ctx.stroke();}}
 ctx.restore();
}
function tick(ms){const now=ms/1000,dt=Math.min(.1,now-last||0);last=now;
 if($('auto').checked&&race.phase==='race'){rewardRound=null;}
 if($('auto').checked&&race.phase==='race')for(const t of race.teams)race.tap(race.active(t).user,1);
 if(now>=introUntil)race.update(dt);
 for(const e of race.events.splice(0)){if(e.type==='special'){fx.push({...e,at:now});SwimShow.cry(e.player||race.active(race.teams[e.from]));}if(e.type==='relay'){message(e.from+' entregó el pergamino a '+e.to);SwimShow.cry(race.active(race.teams[e.team]));}if(e.type==='victory'){if(rewardRound){const payload={action:'finish',round:rewardRound,winners:race.teams[race.winner].members.map(p=>p.user)};rewardRound=null;localStorage.setItem(pendingKey,JSON.stringify(payload));settle(payload);}else message('Ronda de prueba · sin premio');music('victory');$('winner').textContent='';document.querySelectorAll('.gift-side').forEach(el=>el.hidden=true);}}
 $('count').textContent=now<introUntil?'':race.phase==='countdown'?Math.ceil(race.countdown):race.phase==='race'&&race.time<.6?'¡YA!':'';$('status').textContent=race.phase==='lobby'?'INSCRIPCIÓN':race.phase==='countdown'?'A SUS MARCAS':race.phase==='finished'?'¡CAMPEONES!':'CARRERA EN VIVO';$('clock').textContent=Math.floor(race.time)+' s · 2400 m';fx=fx.filter(f=>now-f.at<1);SwimScene.draw({ctx,race,pool,atlas,trainers,pokemon,avatar,now,direction,fx});SwimShow.draw({ctx,race,trainers,pokemon,avatar,now,introUntil,fx,data,muted:audio.muted});SwimVictory.draw({ctx,race,trainers,pokemon,avatar,now});requestAnimationFrame(tick);
}render();requestAnimationFrame(tick);
})();
