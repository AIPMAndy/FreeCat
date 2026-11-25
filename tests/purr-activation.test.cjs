const fs=require('node:fs');const path=require('node:path');

const checks=[];
function assert(ok,label){if(!ok)throw Error(label);checks.push(label)}
function fixture(html){
  const script=html.match(/<script>([\s\S]*?)<\/script>/)[1];
  const audioCode=script.slice(script.indexOf('// Audio starts'),script.indexOf('// Bounded, temporary stroke memory'));
  const pointerCode=script.slice(script.indexOf("cv.addEventListener('pointerdown'"),script.indexOf("cv.addEventListener('keydown'"));
  const factory=new Function('env','with(env){'+audioCode+'\n'+pointerCode+'\nreturn {state:()=>({audio,purring,previewUntil,soundMuted}), disablePurr, button:soundButton};}');
  const listeners={},attrs={};let clock=100,contexts=[];
  const button={setAttribute:(k,v)=>attrs[k]=v,disabled:false};
  class AudioMock{
    constructor(){this.state='suspended';this.sampleRate=1000;this.currentTime=0;this.waiters=[];contexts.push(this)}
    createBuffer(c,n){const data=new Float32Array(n);return {getChannelData:()=>data}}
    createBufferSource(){return {connect(){},start(){}}}
    createGain(){return {gain:{value:0,cancelScheduledValues(){},setTargetAtTime(){}},connect(){}}}
    get destination(){return {}}
    addEventListener(){}
    resume(){return new Promise(resolve=>this.waiters.push(resolve))}
    activate(){this.state='running';for(const fn of this.waiters.splice(0))fn()}
    close(){this.state='closed';return Promise.resolve()}
  }
  const env={$:id=>id==='sound'?button:null,window:{AudioContext:AudioMock},document:{hidden:false},performance:{now:()=>clock},setTimeout:()=>1,clearTimeout(){},fetch:async()=>({ok:false}),visible:true,failed:false,pressed:false,activeId:null,point:[0,0],target:[0,0],cv:{addEventListener:(k,fn)=>listeners[k]=fn,setPointerCapture(){}},uv:()=>[.5,.5],hit:()=>true,stroke(){},endGesture(){env.activeId=null;env.pressed=false},wake(){},roomSave(){},say(){}};
  const f=factory(env);
  return {...f,contexts,env,advance:ms=>clock+=ms,now:()=>clock,event:(name,type='touch')=>listeners[name]({pointerType:type,pointerId:7,button:0,detail:1,isTrusted:true})};
}
async function run(html){
  let f=fixture(html);
  f.event('pointerdown');assert(f.contexts.length===0,'cold touch does not start audio on pointerdown');
  f.event('pointerup');assert(f.contexts.length===1,'touch release requests audio');
  f.advance(2200);assert(f.state().previewUntil===0,'preview clock waits for actual audio start');
  f.contexts[0].activate();await Promise.resolve();
  assert(f.state().previewUntil===f.now()+1400&&f.state().purring,'delayed resume still gets full audible preview window');
  f.button.onclick();assert(f.state().soundMuted&&!f.state().audio,'mute closes audio');
  f.event('pointerdown');f.event('pointerup');assert(f.contexts.length===1,'mute remains respected');
  f=fixture(html);f.event('pointerdown');f.event('pointercancel');assert(f.contexts.length===0,'cancel cannot activate audio');
  f=fixture(html);f.event('pointerdown','mouse');assert(f.contexts.length===1,'mouse starts audio on down');
  f=fixture(html);f.button.onclick();assert(f.contexts.length===1,'explicit sound button can unlock');
  f.advance(3000);f.contexts[0].activate();await Promise.resolve();assert(f.state().purring,'explicit preview survives delayed activation');
  f=fixture(html);f.event('pointerdown');f.event('pointerup');const old=f.contexts[0];f.disablePurr();old.activate();await Promise.resolve();assert(!f.state().purring&&f.state().previewUntil===0,'stale activation cannot restart disabled sound');
  return checks;
}
run(fs.readFileSync(path.join(__dirname,'..','room.html'),'utf8')).then(checks=>{console.log(checks.join('\n'));console.log(checks.length+' passed')}).catch(e=>{console.error(e);process.exitCode=1});
