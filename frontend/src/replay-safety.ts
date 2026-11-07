/** One pinned PostHog recorder; strict projection then same-origin native gateway.
 * Production requires private proof/activation + site flags + explicit preference.
 * No provider/admin credentials, SDK persistence or direct SDK transport.
 */
import {projectSnapshot,REPLAY_POLICY} from './replay-projection';
import {safeRoute} from './operations-telemetry';
export const REPLAY_POLICY_VERSION=REPLAY_POLICY;
type Configuration={subject:string|null;csrf:string;configured:boolean;consented:boolean;role:string;revision:number;locale?:string};
let status='Disabled',failure='',batches=0;export function replayState(){return{status,failure,batches};}
let generation=0,currentScope='',stopCurrent:(()=>void)|null=null;
const channel=typeof BroadcastChannel!=='undefined'?new BroadcastChannel('teletena-replay-scope-v2'):null;
export function stopReplay(broadcast=false){status='Stopped';generation++;stopCurrent?.();stopCurrent=null;currentScope='';if(broadcast)channel?.postMessage({type:'invalidate'});}
channel?.addEventListener('message',e=>{if(e.data?.type==='invalidate')stopReplay()});
window.addEventListener('pagehide',()=>stopReplay());
window.addEventListener('offline',()=>stopReplay(true));
// Sign-out is stopped before the authentication mutation, not after the next poll.
window.addEventListener('teletena-auth-changing',()=>stopReplay(true));
async function command(method:string,body:any,csrf:string,signal?:AbortSignal){const response=await fetch('/api/method/tele_tena.api.operations.'+method,{method:'POST',credentials:'same-origin',cache:'no-store',signal,headers:{'Content-Type':'application/json','X-Frappe-CSRF-Token':csrf,'X-TeleTena-Locale':document.documentElement.lang==='am'?'am':document.documentElement.lang==='om'?'om':'en','X-TeleTena-Device':innerWidth<600?'mobile':innerWidth<1000?'tablet':'desktop'},body:JSON.stringify(body)});if(!response.ok)throw Error('replay_gateway_unavailable');const result=await response.json();return result.message;}
export async function updateReplay(config:Configuration){
 const scope=[config.subject,config.role,config.revision].join(':');
 if(!config.configured||!config.consented||!config.subject||!navigator.onLine||safeRoute(location.pathname)==='/sign-in'){stopReplay();return;}
 if(currentScope===scope)return;
 stopReplay();status='Starting';failure='';currentScope=scope;const run=generation,controller=new AbortController();let sdk:any=null,id='',active=true,timer:ReturnType<typeof setTimeout>|undefined;let queue:any[][]=[],busy=false,total=0,limit=10*1024*1024;let classes=new Set<string>();
 const close=()=>{active=false;queue=[];controller.abort();if(timer)clearTimeout(timer);try{sdk?.sessionRecording?.dispose({discardBufferedEvents:true});void sdk?.shutdown()?.catch(()=>{});}catch{}if(id)void command('replay_close',{id},config.csrf).catch(()=>{});};stopCurrent=close;
 const valid=()=>active&&generation===run;
 const flush=async()=>{if(busy||!valid())return;busy=true;try{while(queue.length&&valid()){const events=queue.shift()!;const value=await command('replay_chunk',{id,chunk_id:crypto.randomUUID(),events,route:safeRoute(location.pathname)},config.csrf,controller.signal);if(value.state!=='Recorded Locally'){stopReplay();return;}}}catch{if(id)void command('replay_loss',{id,reason:'network'},config.csrf).catch(()=>{});stopReplay();}finally{busy=false;}};
 try{
  const {PostHog}=await import('posthog-js/dist/module.full.no-external');if(!valid())return;
  sdk=new PostHog();sdk.init('teletena-native-gateway',{api_host:location.origin,debug:false,autocapture:false,capture_pageview:false,capture_pageleave:false,capture_exceptions:false,capture_performance:false,person_profiles:'never',disable_persistence:true,persistence:'memory',advanced_disable_flags:true,advanced_disable_decide:true,disable_compression:true,request_batching:false,enable_recording_console_log:false,disable_external_dependency_loading:true,disable_session_recording:true,disable_surveys:true,disable_product_tours:true,capture_dead_clicks:false,enable_heatmaps:false,session_recording:{compress_events:false,maskAllInputs:true,maskTextSelector:'*',maskAllElementAttributes:false,blockSelector:'script,img,svg,video,audio,canvas,iframe,object,embed,input[type="file"],input[type="hidden"],.ph-no-capture,[data-private],.attachment-preview,.consultation-room,.room-workspace,.audio-stage,.media-stage,.note-editor,.note-document-panel,.history-documents,textarea,input[type="password"]',recordCrossOriginIframes:false,captureCanvas:{recordCanvas:false},maskCapturedNetworkRequestFn:()=>({url:'https://replay.invalid/unknown'})},before_send:(event:any)=>{
   if(event.event!=='$snapshot'||!valid()||!id)return null;batches++;
   try{const raw=event.properties?.$snapshot_data;if(!Array.isArray(raw)||raw.length>200)throw Error('replay_batch_invalid');const events=raw.map(x=>projectSnapshot(x,classes,safeRoute(location.pathname)));const bytes=JSON.stringify(events).length;if(bytes>1024*1024||queue.length>=3||(total+=bytes)>limit)throw Error('replay_backpressure');queue.push(events);void flush();}catch(error){failure=error instanceof Error&&/^replay_[a-z_]+$/.test(error.message)?error.message:'projection';if(id)void command('replay_loss',{id,reason:'projection'},config.csrf).catch(()=>{});stopReplay();}
   return null;
  }} as any);
  const admission=await command('replay_admit',{provider_id:sdk.get_session_id(),window_id:crypto.randomUUID()},config.csrf,controller.signal);
  if(!valid())return;if(admission.state!=='Active'){stopReplay();return;}
  id=admission.id;limit=Math.min(50*1024*1024,Number(admission.max_bytes)||limit);status='Admitted';classes=new Set(admission.classes);
  sdk.sessionRecording.onRemoteConfig({ok:true,config:{sessionRecording:{sampleRate:1,minimumDurationMilliseconds:0,endpoint:'/s/',version:'v2'}}});
  sdk.startSessionRecording({sampling:true,linked_flag:true,trigger:'event'});status='Recording';
  timer=setTimeout(()=>stopReplay(),15*60*1000);
 }catch{failure='setup_unavailable';if(valid())stopReplay();}
}
export async function preparedReplayVersion(){return{policy:REPLAY_POLICY_VERSION,enabled:false,gate:'Private proof, operator activation, site flags and per-user consent required'};}
