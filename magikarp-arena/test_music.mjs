import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';

class Clip {
 constructor(src=''){this.src=src;this.currentTime=0;this.paused=true;this.error=null;}
 getAttribute(name){return name==='src'?this.src:null;}
 removeAttribute(name){if(name==='src')this.src='';}
 addEventListener(){}
 load(){}
 pause(){this.paused=true;}
 async play(){this.paused=false;}
}
const audio=new Clip(),button={addEventListener(){}},volume={addEventListener(){},value:35};
globalThis.document={createElement:()=>audio,body:{append(){}},querySelector:s=>s==='#music-toggle'?button:volume};
globalThis.Audio=Clip;
const code=await readFile(new URL('./music.js',import.meta.url),'utf8');
const {updateMusic}=await import('data:text/javascript;base64,'+Buffer.from(code).toString('base64'));
const state=(phase,remaining,round=1)=>({phase,remaining,round,duration:60,players:[]});
updateMusic(state('lobby',0));assert.match(audio.src,/lobby\.mp3/);
updateMusic(state('countdown',2.7));assert.equal(audio.src,'');
updateMusic(state('countdown',.901));assert.equal(audio.src,'');
updateMusic(state('countdown',.9));assert.match(audio.src,/playing\.mp3/);assert.equal(audio.loop,false);
audio.currentTime=.8;
updateMusic(state('playing',59.9));assert.equal(audio.currentTime,.8,'El inicio de la ronda no debe reiniciar el MP3');
updateMusic(state('ending',0));assert.equal(audio.src,'');
updateMusic(state('finished',0));assert.match(audio.src,/winner\.wav/);assert.equal(audio.loop,false);
updateMusic(state('lobby',0,2));assert.match(audio.src,/lobby\.mp3/);assert.equal(audio.currentTime,0);
console.log('MP3 de inscripción, inicio en Ditto 1, continuidad y victoria: OK');
