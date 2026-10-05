// Original music is captured locally by the port, never bundled in Git.
const audio=document.createElement('audio');audio.id='original-music';audio.hidden=true;
document.body.append(audio);audio.preload='auto';audio.volume=.35;
const button=document.querySelector('#music-toggle');
const volume=document.querySelector('#music-volume');
let key='',track='',blocked=false,muted=false,retryAt=0;
function label(){button.textContent=blocked?'Activar música':muted?'Música apagada':'♫ Música';}
async function play(){
 if(muted)return;
 try{await audio.play();blocked=false;label();}
 catch(e){if(e.name==='NotAllowedError'){blocked=true;label();}}
}
button.addEventListener('click',()=>{
 if(blocked){blocked=false;muted=false;play();}
 else{muted=!muted;audio.muted=muted;if(!muted)play();label();}
});
volume.addEventListener('input',()=>{audio.volume=Number(volume.value)/100;});
audio.addEventListener('error',()=>{button.textContent='Música pendiente';retryAt=Date.now()+5000;});
export function updateMusic(state){
 const phase=state.phase==='countdown'?'lobby':state.phase;
 const next=phase==='finished'?'winner':phase==='playing'?'playing':'lobby';
 const nextKey=state.round+':'+next;
 if(key===nextKey){
  if(audio.error&&Date.now()>=retryAt){retryAt=Date.now()+5000;audio.load();play();}
  return;
 }
 key=nextKey;track=next;audio.pause();audio.src='/music/'+track+'.wav';
 audio.loop=track!=='winner';audio.currentTime=0;play();
}
export function musicDiagnostics(){return {track,blocked,muted,paused:audio.paused,time:audio.currentTime,error:audio.error?.code||null,volume:audio.volume};}
