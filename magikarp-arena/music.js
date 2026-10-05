// All audio is generated locally by the original ROM's audio engine.
const audio=document.createElement('audio');audio.id='original-music';audio.hidden=true;document.body.append(audio);audio.preload='auto';audio.volume=.35;
const button=document.querySelector('#music-toggle'),volume=document.querySelector('#music-volume');
let key='',track='',blocked=false,muted=false,retryAt=0,lastCue='',lastSound=0;
const players=new Map(),effects=new Set();
function label(){button.textContent=blocked?'Activar música':muted?'Música apagada':'♫ Música';}
async function play(){if(muted||!audio.getAttribute('src'))return;try{await audio.play();blocked=false;label();}catch(e){if(e.name==='NotAllowedError'){blocked=true;label();}}}
function effect(name,force=false){
 if(muted||(!force&&performance.now()-lastSound<65))return;
 lastSound=performance.now();const clip=new Audio('/music/'+name+'.wav?v=3');clip.volume=audio.volume*.7;effects.add(clip);
 clip.addEventListener('ended',()=>effects.delete(clip));clip.addEventListener('error',()=>effects.delete(clip));
 clip.play().catch(e=>{effects.delete(clip);if(e.name==='NotAllowedError'){blocked=true;label();}});
}
button.addEventListener('click',()=>{if(blocked){blocked=false;muted=false;audio.muted=false;play();}else{muted=!muted;audio.muted=muted;for(const e of effects)e.muted=muted;if(!muted)play();label();}});
volume.addEventListener('input',()=>{audio.volume=Number(volume.value)/100;for(const e of effects)e.volume=audio.volume*.7;});
audio.addEventListener('error',()=>{button.textContent='Música pendiente';retryAt=Date.now()+5000;});
export function updateMusic(state){
 const age=state.duration-state.remaining;
 const next=state.phase==='countdown'||(state.phase==='playing'&&age<.5)?'':state.phase==='finished'?'winner':state.phase==='playing'?'playing':'lobby';
 const nextKey=state.round+':'+next;
 if(key!==nextKey){key=nextKey;track=next;audio.pause();if(next){audio.src='/music/'+track+'.wav?v=3';audio.loop=track!=='winner';audio.currentTime=0;play();}else{audio.removeAttribute('src');audio.load();}}
 else if(next&&audio.error&&Date.now()>=retryAt){retryAt=Date.now()+5000;audio.load();play();}
 if(state.phase==='countdown'){
  const cue=state.round+':'+Math.ceil(state.remaining/.9);
  if(cue!==lastCue){lastCue=cue;effect('countdown',true);}
 }
 for(const p of state.players){
  const previous=players.get(p.id),current={round:state.round,jumps:p.jumps,score:p.score};
  if(previous?.round===state.round&&state.phase==='playing'){
   if(p.score>previous.score)effect('hit');else if(p.jumps>previous.jumps)effect('jump');
  }
  players.set(p.id,current);
 }
}
export function musicDiagnostics(){return {track,blocked,muted,paused:audio.paused,time:audio.currentTime,error:audio.error?.code||null,volume:audio.volume};}