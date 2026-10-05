const {spawn}=require('node:child_process');
const path=require('node:path');
function accept(req,res){
 if(req.method!=='POST'||!['/battle-reward','/swimming-reward'].includes(req.url))return false;
 if(req.headers.origin&&req.headers.origin!==`http://${req.headers.host}`){res.writeHead(403);res.end();return true}
 let body='';req.on('data',c=>{body+=c;if(body.length>4096)req.destroy()});
 req.on('end',()=>{try{
  const payload=JSON.parse(body);const swimming=req.url==='/swimming-reward';if(swimming)payload.game='swimming';if(!['begin','finish','status'].includes(payload.action))throw Error('Acción inválida');
  const child=spawn(process.env.BATTLE_PYTHON||'C:\\Users\\xkafe\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe',[swimming?path.resolve(__dirname,'../../../Shipwright/tools/magikarp-arena/rewards.py'):path.join(__dirname,'battle_rewards.py')],{windowsHide:true});
  let output='',done=false;const reply=(code,data)=>{if(done)return;done=true;clearTimeout(timer);res.writeHead(code,{'Content-Type':'application/json','Cache-Control':'no-store'});res.end(JSON.stringify(data))};
  const timer=setTimeout(()=>{child.kill();reply(503,{error:'La cartera tardó demasiado; el pago puede reintentarse con la misma ronda'})},35000);
  child.stdout.on('data',c=>output+=c);child.stderr.on('data',()=>{});child.on('error',()=>reply(503,{error:'No se pudo abrir la cartera compartida'}));
  child.on('close',code=>{try{reply(code===0?200:400,JSON.parse(output))}catch{reply(503,{error:'Respuesta de cartera inválida'})}});child.stdin.on('error',()=>{});child.stdin.end(JSON.stringify(payload));
 }catch{res.writeHead(400);res.end('{"error":"Solicitud inválida"}')}});return true;
}
module.exports={accept};
