import * as THREE from '/vendor/three.module.js';

const $ = s => document.querySelector(s);
const error = text => {$('#error').hidden=false; $('#error').textContent=text;};
function resize(){document.documentElement.style.setProperty('--scale',Math.min(innerWidth/1080,innerHeight/1920));}
addEventListener('resize',resize);resize();
const scene=new THREE.Scene(), camera=new THREE.OrthographicCamera(-514,514,710,-710,1,2000);
camera.position.z=900;
scene.add(new THREE.AmbientLight(0xffffff,1.8));
const light=new THREE.DirectionalLight(0xffffff,2.2);light.position.set(-400,800,900);scene.add(light);
let renderer,trophyRenderer;
try{
  renderer=new THREE.WebGLRenderer({canvas:$('#game'),alpha:true,antialias:true});
  renderer.setSize(1028,1420,false);renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));
  trophyRenderer=new THREE.WebGLRenderer({canvas:$('#trophy'),alpha:true,antialias:true});
  trophyRenderer.setSize(930,540,false);trophyRenderer.setPixelRatio(Math.min(devicePixelRatio,1.5));
}catch(e){error('No se pudo iniciar el renderizador 3D.\nActiva la aceleración gráfica del navegador.');throw e;}
const trophyScene=new THREE.Scene(),trophyCamera=new THREE.PerspectiveCamera(34,930/540,1,2000);
trophyCamera.position.set(0,60,650);trophyCamera.lookAt(0,0,0);
trophyScene.add(new THREE.AmbientLight(0xffffff,1.8));
const trophyLight=light.clone();trophyScene.add(trophyLight);
let models;
try{
 const response=await fetch('/models.json');if(!response.ok)throw Error('missing');models=await response.json();
}catch(e){error('Faltan los gráficos de tu ROM.\nEjecuta Preparar.ps1 dentro de magikarp-arena.');throw e;}
const loader=new THREE.TextureLoader();
const templates={};
for(const [name,model] of Object.entries(models)){
 const textures=await Promise.all(model.textures.map(async t=>{
  const texture=await loader.loadAsync(t.png);texture.colorSpace=THREE.SRGBColorSpace;
  texture.magFilter=THREE.NearestFilter;texture.minFilter=THREE.LinearFilter;
  texture.wrapS=texture.wrapT=THREE.RepeatWrapping;return texture;
 }));
 const group=new THREE.Group();
 for(const part of model.groups){
  const geometry=new THREE.BufferGeometry();
  geometry.setAttribute('position',new THREE.Float32BufferAttribute(part.position,3));
  geometry.setAttribute('normal',new THREE.Float32BufferAttribute(part.normal,3));
  geometry.setAttribute('uv',new THREE.Float32BufferAttribute(part.uv,2));
  geometry.setAttribute('n64Local',new THREE.Float32BufferAttribute(part.local,3));
  geometry.setAttribute('n64Normal',new THREE.Float32BufferAttribute(part.rawNormal,3));
  geometry.setAttribute('n64Bone',new THREE.Float32BufferAttribute(part.bone,1));
  const material=new THREE.MeshLambertMaterial({map:textures[part.texture],side:THREE.DoubleSide,alphaTest:.1});
  const mesh=new THREE.Mesh(geometry,material);mesh.frustumCulled=false;group.add(mesh);
 }
 // The source model keeps N64's original scale and skeletal rest pose.
 group.rotation.y=-Math.PI*.3125;
 if(name==='magikarp')group.rotation.x=Math.PI/2;
 group.updateMatrixWorld(true);
 const bounds=new THREE.Box3().setFromObject(group),center=bounds.getCenter(new THREE.Vector3());
 const root=new THREE.Group();group.position.sub(center);root.add(group);
 const size=bounds.getSize(new THREE.Vector3());root.scale.setScalar((name==='magikarp'?150:60)/Math.max(size.x,size.y));
 templates[name]=root;
}
function tint(root,color){
 const tint=new THREE.Color(color);
 const poses=models.magikarp.animations;
 const boneMatrices=poses['0'][0].map(m=>new THREE.Matrix4().fromArray(m));
 root.userData.poseMatrices=boneMatrices;
 root.traverse(mesh=>{
  if(!mesh.isMesh)return;
  mesh.material=mesh.material.clone();
  mesh.material.onBeforeCompile=shader=>{
   shader.uniforms.playerTint={value:tint};
   shader.uniforms.n64Matrices={value:boneMatrices};
   shader.vertexShader=`attribute vec3 n64Local; attribute vec3 n64Normal; attribute float n64Bone; uniform mat4 n64Matrices[${boneMatrices.length}];\n`+shader.vertexShader;
   shader.vertexShader=shader.vertexShader.replace('#include <beginnormal_vertex>',`vec3 objectNormal=mat3(n64Matrices[int(n64Bone)])*n64Normal;`);
   shader.vertexShader=shader.vertexShader.replace('#include <begin_vertex>',`vec3 transformed=(n64Matrices[int(n64Bone)]*vec4(n64Local,1.0)).xyz;`);
   shader.fragmentShader='uniform vec3 playerTint;\n'+shader.fragmentShader;
   shader.fragmentShader=shader.fragmentShader.replace('#include <map_fragment>',`#include <map_fragment>
    float redMask = smoothstep(0.02,0.12,diffuseColor.r-max(diffuseColor.g,diffuseColor.b));
    float brightness=max(max(diffuseColor.r,diffuseColor.g),diffuseColor.b);
    diffuseColor.rgb=mix(diffuseColor.rgb,playerTint*brightness,redMask);`);
  };
 });
}
function pose(fish,index,frame){
 const frames=models.magikarp.animations[index]||models.magikarp.animations['0'];
 const matrices=frames[Math.min(frames.length-1,Math.max(0,Math.floor(frame)))];
 const idleRoot=models.magikarp.animations['0'][0][0];
 // Arena physics controls the jump height; retain the source skeletal motion.
 const delta=[matrices[0][12]-idleRoot[12],matrices[0][13]-idleRoot[13],matrices[0][14]-idleRoot[14]];
 fish.userData.poseMatrices.forEach((m,i)=>{
  m.fromArray(matrices[i]);m.elements[12]-=delta[0];m.elements[13]-=delta[1];m.elements[14]-=delta[2];
 });
}
const entities=new Map(),cards=new Map();let state=null,received=performance.now(),round=-1,trophy=null,winnerKey='';
function avatar(player){
 let element;
 if(player.avatar){element=document.createElement('img');element.src=player.avatar;element.referrerPolicy='no-referrer';element.alt=player.name;element.onerror=()=>{element.replaceWith(initial(player));};}
 else return initial(player);
 element.className='avatar';return element;
}
function initial(player){const e=document.createElement('span');e.className='avatar initial';e.textContent=Array.from(player.name)[0]?.toUpperCase()||'?';return e;}
function reset(){
 for(const entity of entities.values()){
  scene.remove(entity.root);
  entity.fish.traverse(m=>{if(m.isMesh)m.material.dispose();});
 }
 entities.clear();cards.clear();$('#cards').replaceChildren();
 for(let i=0;i<12;i++){
  const card=document.createElement('div');card.className='card';card.dataset.slot=i;
  const empty=document.createElement('div');empty.className='empty';empty.innerHTML=`<strong>${String(i+1).padStart(2,'0')}</strong><span>!unir</span>`;
  card.append(empty);$('#cards').append(card);
 }
}
function entityFor(player){
 if(entities.has(player.id))return entities.get(player.id);
 const root=new THREE.Group(),fish=templates.magikarp.clone(true),button=templates.button.clone(true);
 tint(fish,player.color);button.rotation.y=Math.PI;button.position.set(0,100,-10);
 fish.position.set(0,-70,20);root.add(fish,button);
 root.position.set((player.slot%3-1)*347,538-Math.floor(player.slot/3)*358.5,0);scene.add(root);
 const entity={root,fish,button};entities.set(player.id,entity);
 const card=document.querySelector(`[data-slot="${player.slot}"]`);card.classList.add('occupied');card.style.setProperty('--player',player.color);card.replaceChildren();
 const identity=document.createElement('div');identity.className='identity';identity.append(avatar(player));
 const name=document.createElement('span');name.className='name';name.textContent=player.name;identity.append(name);
 const points=document.createElement('div');points.className='points';
 const progress=document.createElement('div');progress.className='progress';
 const bar=document.createElement('div');bar.className='bar';card.append(identity,points,progress,bar);
 cards.set(player.id,{card,points,progress});return entity;
}
function updateWinner(s){
 const key=s.round+':'+s.winners.join(',');if(key===winnerKey)return;winnerKey=key;
 const winners=s.players.filter(p=>s.winners.includes(p.id));
 $('#winner').classList.toggle('multi',winners.length>1);
 const trophyHeight=winners.length>1?400:540;
 trophyRenderer.setSize(930,trophyHeight,false);trophyCamera.aspect=930/trophyHeight;trophyCamera.updateProjectionMatrix();
 $('#winner-title').textContent=winners.length>1?'¡EMPATE!':'¡GANADOR!';
 $('#champions').replaceChildren();
 for(const player of winners){
  const wrap=document.createElement('div');wrap.style.setProperty('--player',player.color);wrap.append(avatar(player));
  const name=document.createElement('div');name.className='name';name.textContent=player.name;wrap.append(name);$('#champions').append(wrap);
 }
 $('#winner-score').textContent=winners.length?`${winners[0].score} golpes al botón`:'';
 if(trophy){trophyScene.remove(trophy);trophy.traverse(m=>{if(m.isMesh)m.material.dispose();});}
 trophy=new THREE.Group();
 winners.forEach((p,i)=>{let fish=templates.magikarp.clone(true);tint(fish,p.color);fish.scale.multiplyScalar(winners.length===1?2:winners.length>4?.85:1.2);const cols=Math.min(4,winners.length),rows=Math.ceil(winners.length/cols);fish.position.x=(i%cols-(cols-1)/2)*170;fish.position.y=((rows-1)/2-Math.floor(i/cols))*115;trophy.add(fish);});
 trophyScene.add(trophy);
 $('#podium').replaceChildren();
 [...s.players].sort((a,b)=>b.score-a.score||a.slot-b.slot).slice(0,5).forEach((p,i)=>{
  const row=document.createElement('div');row.className='rank';const name=document.createElement('span'),score=document.createElement('strong');
  name.textContent=`${i+1}. ${p.name}`;score.textContent=`${p.score} puntos`;row.append(name,score);$('#podium').append(row);
 });
}
function update(s){
 state=s;received=performance.now();
 if(round!==s.round){round=s.round;reset();winnerKey='';}
 $('#phase').textContent={lobby:`SALA ABIERTA · ${s.players.length}/12`,countdown:'¡PREPÁRATE!',playing:'RONDA EN MARCHA',finished:'RONDA TERMINADA'}[s.phase];
 $('#instruction').textContent=s.phase==='lobby'?'Escribe !unir en el chat para jugar':s.phase==='finished'?'¡Gracias por participar!':'¡Toca la pantalla para hacer saltar a tu Magikarp!';
 $('#connection').textContent=s.connection;
 $('#winner').hidden=s.phase!=='finished';
 $('#countdown').hidden=s.phase!=='countdown';
 if(s.phase==='finished')updateWinner(s);
 for(const player of s.players){
  entityFor(player);const c=cards.get(player.id);
  c.points.innerHTML=`<b>${player.score}</b>`;
  c.progress.textContent=`${player.remainder}/10 taps · ${player.pending} en cola`;
  c.card.style.setProperty('--progress',player.remainder*10+'%');
 }
 $('#error').hidden=true;
}
async function poll(){
 try{const r=await fetch('/api/state');if(!r.ok)throw Error();update(await r.json());}
 catch(e){error('Se perdió la conexión con la sala.\nReconectando…');}
 setTimeout(poll,100);
}
poll();
function frame(now){
 requestAnimationFrame(frame);
 if(state){
  const elapsed=(now-received)/1000,remaining=Math.max(0,state.remaining-elapsed);
  $('#timer').textContent=state.phase==='lobby'?'!unir':state.phase==='finished'?'FIN':`${Math.ceil(remaining)}s`;
  if(state.phase==='countdown')$('#countdown').textContent=Math.max(1,Math.ceil(remaining));
  for(const p of state.players){
   const e=entities.get(p.id);if(!e)continue;
   const age=p.jump_age===null?null:p.jump_age+elapsed;
   let height=0;
   if(age!==null&&age<state.jump_seconds){height=Math.sin(Math.PI*age/state.jump_seconds)*65;}
   e.fish.position.y=-70+height;
   if(age!==null&&age<state.jump_seconds)pose(e.fish,'8',age/state.jump_seconds*(models.magikarp.animations['8'].length-1));
   else pose(e.fish,'0',(now*.03+p.slot*3)%models.magikarp.animations['0'].length);
   e.fish.rotation.z=age===null?Math.sin(now*.003+p.slot)*.06:-Math.sin(Math.min(1,age/state.jump_seconds)*Math.PI)*Math.PI/2;
   e.fish.rotation.y=Math.sin(now*.002+p.slot)*.09;
   e.button.position.y=100+(age!==null&&Math.abs(age-state.hit_seconds)<.09?9:0);
  }
  if(trophy){trophy.rotation.y=Math.sin(now*.00065)*.3;trophy.position.y=Math.sin(now*.002)*10;trophy.children.forEach(fish=>pose(fish,'7',now*.03%models.magikarp.animations['7'].length));}
 }
 renderer.render(scene,camera);
 if(state?.phase==='finished')trophyRenderer.render(trophyScene,trophyCamera);
}
requestAnimationFrame(frame);
// Read-only diagnostics for local visual and event verification.
window.magikarpDiagnostics=()=>({state,models:Object.fromEntries(Object.entries(models).map(([k,v])=>[k,{triangles:v.groups.reduce((n,g)=>n+g.position.length/9,0),textures:v.textures.length}])),entities:entities.size});
