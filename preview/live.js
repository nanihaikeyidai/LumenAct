import * as THREE from "three";
import {GLTFLoader} from "./vendor/loaders/GLTFLoader.js";

const canvas=document.querySelector("canvas"), status=document.querySelector("#status");
const play=document.querySelector("#play"), input=document.querySelector("input");
const renderer=new THREE.WebGLRenderer({canvas,antialias:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));
renderer.toneMapping=THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure=.92;
const scene=new THREE.Scene();
scene.background=new THREE.Color(0x293444);
const camera=new THREE.PerspectiveCamera(28,16/9,.01,20);
camera.position.set(.01,.72,1.42);
camera.lookAt(.01,.64,0);
scene.add(new THREE.HemisphereLight(0xfff6ed,0xbecad9,1.35));
const key=new THREE.DirectionalLight(0xffeadc,1.8);
key.position.set(-1,2,2);scene.add(key);
const meshes=[], bones=new Map(), queue=[];
let ctx, analyser, samples, source, active, epoch=0, busy=false, controller;
let jaw=0, smile=0, brow=0, last=0, start=0;
const targets={};
function script(line){
  const prefix=line.match(/^[（(]([^）)]*)[）)]/);
  const text=line.slice(prefix?.[0].length||0).trim();
  const cue=prefix?.[1]||text;
  const gesture=/挥手|欢迎|再见|大家好/.test(cue)?"wave":/摇头|不对/.test(cue)?"shake":/点头|没错|同意/.test(cue)?"nod":/讲解|这里|首先|重点/.test(cue)?"explain":"idle";
  return {text,gesture,smile:/微笑|欢迎|谢谢|大家好/.test(cue),brow:/挑眉|惊讶|真的/.test(cue),blink:/眨眼/.test(cue)};
}
function shape(name,value){
  for(const mesh of meshes){
    const index=mesh.morphTargetDictionary?.[name];
    if(index!==undefined)mesh.morphTargetInfluences[index]=value;
  }
}
function pose(name,axis,angle,dt){
  const bone=bones.get(name);if(!bone)return;
  const id=name+axis;
  targets[id]=THREE.MathUtils.damp(targets[id]||0,angle,12,dt);
  bone.rotation[axis]=bone.userData.rest[axis]+targets[id];
}
function animate(now){
  const dt=Math.min(.1,(now-last)/1000);last=now;
  const t=ctx?ctx.currentTime-start:0, wave=active?.gesture==="wave", nod=active?.gesture==="nod", explain=active?.gesture==="explain";
  let rms=0;
  if(active){analyser.getFloatTimeDomainData(samples);for(const x of samples)rms+=x*x;rms=Math.sqrt(rms/samples.length);}
  jaw=THREE.MathUtils.damp(jaw,Math.min(.94,Math.max(0,(rms-.009)*6)),rms>.015?23:17,dt);
  smile=THREE.MathUtils.damp(smile,active?.smile?.65:0,9,dt);
  brow=THREE.MathUtils.damp(brow,active?.brow?.7:0,9,dt);
  const pulse=phase=>Math.abs(phase)<.115?Math.cos(phase*Math.PI/.23)**2:0;
  shape("mouth_a",jaw);shape("mouth_smile_1",smile);shape("eyebrow_up_L",brow);shape("eyebrow_up_R",brow*.65);
  shape("eye_close",Math.max(pulse((now/1000)%3.83-.45),active?.blink?pulse(t-.32):0));
  pose("Head","x",nod?.13*Math.sin(4*t):0,dt);
  pose("Head","y",active?.gesture==="shake"?.20*Math.sin(4.2*t):.035*Math.sin(now/1600),dt);
  pose("Spine02","z",.017*Math.sin(now/1700)+(explain?.045:0),dt);
  pose("R_Upperarm","z",wave?.38:explain?.19:0,dt);
  pose("R_Forearm","x",wave?-.50:explain?-.27:0,dt);
  pose("R_Hand","z",wave?.28*Math.sin(6*t):0,dt);
  const w=canvas.clientWidth,h=canvas.clientHeight;
  if(renderer.domElement.width!==Math.floor(w*renderer.getPixelRatio())||renderer.domElement.height!==Math.floor(h*renderer.getPixelRatio())){
    renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();
  }
  renderer.render(scene,camera);requestAnimationFrame(animate);
}
async function next(){
  if(busy||!queue.length)return;
  const token=epoch,item=queue.shift();busy=true;
  controller=new AbortController();
  try{
    status.textContent="IndexTTS 正在合成…";
    const res=await fetch("/api/live/speech",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({text:item.text}),signal:controller.signal});
    if(!res.ok)throw Error("合成失败，请检查本地 ComfyUI 和参考音频。");
    const buffer=await ctx.decodeAudioData(await res.arrayBuffer());
    if(token!==epoch)return;
    source=ctx.createBufferSource();source.buffer=buffer;source.connect(analyser);
    active=item;start=ctx.currentTime;status.textContent=item.text;
    await new Promise(resolve=>{source.onended=resolve;source.start();});
  }catch(error){if(token===epoch)status.textContent=error.message;}
  finally{if(token===epoch){if(active)status.textContent="播报结束";source?.disconnect();source=null;active=null;busy=false;next();}}
}
document.querySelector("form").onsubmit=async e=>{
  e.preventDefault();const item=script(input.value.trim());if(!item.text)return;
  if(!ctx){ctx=new AudioContext();analyser=ctx.createAnalyser();analyser.fftSize=1024;samples=new Float32Array(1024);analyser.connect(ctx.destination);}
  await ctx.resume();queue.push(item);next();
};
document.querySelector("#stop").onclick=()=>{
  epoch++;controller?.abort();queue.length=0;source?.stop();source?.disconnect();source=null;active=null;busy=false;status.textContent="已停止";
};
try{
  const {scene:model}=await new GLTFLoader().loadAsync("../assets/character/tripo/lumen-tripo-face-refined.glb");
  model.traverse(o=>{if(o.isBone){bones.set(o.name,o);o.userData.rest=o.rotation.clone();}if(o.isMesh)meshes.push(o);});
  scene.add(model);play.disabled=false;status.textContent="可以播报";requestAnimationFrame(animate);
}catch(error){status.textContent="角色加载失败："+error.message;}
