(function(root){
const DISTANCE=2400,MAX_PLAYERS=16;
class Race{
 constructor(random=Math.random,allowed=null){this.random=random;this.allowed=allowed;this.order=[];this.players=[];this.teams=[];this.phase='lobby';this.time=0;this.countdown=0;this.events=[];}
 join(user,species,avatar=''){
  if(this.allowed&&!this.allowed.includes(species))return{ok:false,message:'Sólo Pokémon de agua.'};if(this.phase!=='lobby')return{ok:false,message:'La carrera ya comenzó.'};
  user=String(user).trim().replace(/^@/,'').toLowerCase();if(!user)return{ok:false,message:'Escribe el entrenador.'};
  let p=this.players.find(p=>p.user===user);
  if(p){p.species=species;p.avatar=avatar||p.avatar;return{ok:true,player:p};}
  if(this.players.length>=MAX_PLAYERS)return{ok:false,message:'La sala tiene 16 participantes.'};
  p={id:this.players.length,user,species,avatar,stock:{rose:0,corn:0,popular:0},hp:100,sp:0,credits:0,stroke:0,taps:0};
  this.players.push(p);return{ok:true,player:p};
 }
 start(){
  if(this.phase!=='lobby'||this.players.length<2)return false;
  const lanes=Math.min(4,this.players.length);this.teams=Array.from({length:lanes},(_,id)=>({id,members:[],distance:0,stage:0,relayUntil:0,boostUntil:0,stock:{rose:0,corn:0,popular:0},finished:false}));
  const shuffled=this.players.slice();for(let i=shuffled.length-1;i>0;i--){const j=Math.floor(this.random()*(i+1));[shuffled[i],shuffled[j]]=[shuffled[j],shuffled[i]];}
  shuffled.forEach((p,i)=>{const t=this.teams[i%lanes];p.team=t.id;t.members.push(p);for(const k of Object.keys(t.stock))t.stock[k]+=p.stock[k];});
  this.phase='countdown';this.countdown=3;return true;
 }
 active(team){return team.members[team.stage];}
 tap(user,count=1){if(this.phase!=='race')return false;const p=this.players.find(p=>p.user===user),t=p&&this.teams[p.team];if(!t||t.finished||!Number.isFinite(count))return false;const taps=Math.max(0,Math.min(1000000,Math.floor(count)));p.taps+=taps;const swimmer=this.active(t);swimmer.credits=Math.min(120,swimmer.credits+taps);return true;}
 gift(user,key,count=1){const p=this.players.find(p=>p.user===user);if(!p||!['rose','corn','popular'].includes(key)||this.phase==='finished')return false;const stock=this.phase==='lobby'?p.stock:this.teams[p.team].stock;stock[key]+=Math.max(1,Math.min(100,Math.floor(count)));return true;}
 update(dt){
  dt=Math.max(0,Math.min(.1,dt));
  if(this.phase==='countdown'){this.countdown-=dt;if(this.countdown<=0){this.phase='race';this.events.push({type:'dive'});}return;}
  if(this.phase!=='race')return;this.time+=dt;
  const strokes=[];
  for(const t of this.teams){
   if(t.finished||t.relayUntil>this.time)continue;const p=this.active(t);
   if(p.hp<=50&&t.stock.rose>0){t.stock.rose--;p.hp=Math.min(100,p.hp+30);this.events.push({type:'heal',team:t.id});}
   if(p.sp<=50&&t.stock.corn>0){t.stock.corn--;p.sp=Math.min(100,p.sp+50);}
   if(t.boostUntil<=this.time&&t.stock.popular>0){t.stock.popular--;t.boostUntil=this.time+8;}
   const boosted=t.boostUntil>this.time;
   if(p.freezeUntil>this.time){p.stroke=0;continue;}
   p.stroke+=dt;
   while(p.credits>0&&p.stroke>=.125){p.credits--;p.stroke-=.125;t.distance+=5*(.35+.65*p.hp/100)*(boosted?1.5:1)*(p.jetUntil>this.time?1.3:1)*(p.slowUntil>this.time?.65:1)*(p.paralyzeUntil>this.time?.5:1);strokes.push(t.id);}
   p.stroke=Math.min(p.stroke,.125);
   if(t.distance>=DISTANCE){t.distance=DISTANCE;t.finished=true;this.order.push(t.id);t.place=this.order.length;this.winner=this.order[0];this.events.push({type:'finish',team:t.id});if(this.teams.every(v=>v.finished)){this.phase='finished';this.events.push({type:'victory',team:this.winner});}continue;}
   const next=Math.min(t.members.length-1,Math.floor(t.distance/(DISTANCE/t.members.length)));
   if(next>t.stage){const previous=this.active(t);t.stage=next;t.relayUntil=this.time+2;this.active(t).credits=previous.credits;previous.credits=0;this.active(t).stroke=0;this.events.push({type:'relay',team:t.id,from:previous.user,to:this.active(t).user});}
  }
  if(this.teams.length===4&&this.order.length===3){const last=this.teams.find(t=>!t.finished);last.finished=true;last.autoLast=true;last.place=4;this.order.push(last.id);this.phase='finished';this.events.push({type:'finish',team:last.id,forced:true},{type:'victory',team:this.winner});}
  // Rival strokes charge SP equally across lanes, with compensation for smaller rosters.
  const largest=Math.max(...this.teams.map(t=>t.members.length));
  for(const t of this.teams){
   if(t.finished)continue;
   const p=this.active(t),rivalStrokes=strokes.filter(id=>id!==t.id).length;
   p.sp=Math.min(100,p.sp+rivalStrokes*2/(this.teams.length-1)*largest/t.members.length/(root.SwimSpecials?.get(p).charge||1));
  }
  for(const t of this.teams){
   if(t.finished||t.relayUntil>this.time)continue;
   const p=this.active(t),rivals=this.teams.filter(v=>v!==t&&!v.finished);
   if(p.sp>=100&&rivals.length){
    if(root.SwimSpecials){root.SwimSpecials.apply(this,t,rivals);continue;}const target=rivals[Math.floor(this.random()*rivals.length)];
    this.active(target).hp=Math.max(15,this.active(target).hp-18);
    this.events.push({type:'special',from:t.id,to:target.id});p.sp=0;
   }
  }
 }
}
const api={Race,DISTANCE,MAX_PLAYERS};if(typeof module==='object')module.exports=api;else root.SwimRace=api;
})(globalThis);
