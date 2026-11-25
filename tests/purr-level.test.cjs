const fs=require('node:fs');const path=require('node:path');
function checkRecordingLevel(html){
const code=html.slice(html.indexOf('function recordingLevel(buffer){'),html.indexOf('async function loadRecording(a,synthetic){'));
const level=new Function(code+';return recordingLevel')();
const mk=(...channels)=>({numberOfChannels:channels.length,getChannelData:i=>Float32Array.from(channels[i])});
const results=[];function check(ok,label){if(!ok)throw Error(label);results.push(label)}
check(level(mk([0,0,0]))===null,'silent recording rejected');
check(level(mk([.001,-.001]))===null,'nearly silent recording rejected');
check(level(mk([NaN,0]))===null,'invalid decoded samples rejected');
check(level(mk([]))===null,'empty recording rejected');
check(level(mk([.005,-.005]))===null,'unrecoverably quiet audio rejected');
check(Math.abs(level(mk([.04,-.04]))-2.125)<.00001,'quiet usable recording normalized');
check(Math.abs(level(mk([.4,-.4]))-.2125)<.00001,'loud recording attenuated');
const transient=Array(100).fill(.03);transient[0]=1;
check(level(mk(transient))<=.7,'peak limit enforced');
check(Math.abs(level(mk([.04,-.04],[.04,-.04]))-2.125)<.00001,'stereo accounted for');
check(html.includes('const level=recordingLevel(b);if(level===null)return;'),'silence rejected before crossfade');
check(html.includes('g.gain.setTargetAtTime(level,now,.28);synthetic.gain.setTargetAtTime(0,now,.28);'),'accepted recording crossfades with measured gain');
return results;
}
const results=checkRecordingLevel(fs.readFileSync(path.join(__dirname,'..','room.html'),'utf8'));console.log(results.join('\n'));console.log(results.length+' passed');
