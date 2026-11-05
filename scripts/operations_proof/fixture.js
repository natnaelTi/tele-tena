/* Isolated synthetic fixture only. Never imported into the application bundle. */
const stages=['directory','onboarding','requests','document','consultation','reviewer'];
document.querySelectorAll('[data-stage]').forEach(b=>b.onclick=()=>{const stage=b.dataset.stage;if(!stages.includes(stage))return;history.pushState({},'', '/ops-proof-v1/'+stage);document.querySelector('#heading').textContent=b.textContent;document.querySelector('#status').textContent='TT_SECRET_DYNAMIC_71';});
document.querySelector('#open').onclick=()=>document.querySelector('dialog').showModal();document.querySelector('#close').onclick=()=>document.querySelector('dialog').close();document.querySelector('#change').onclick=()=>{const a=document.createElement('article');a.textContent='TT_SECRET_MUTATION_71';document.querySelector('main').append(a)};
window.startProof=function(token,actor,hold=false){
 window.proofState={blocked:0,seen:0};
 posthog.init(token,{api_host:'https://eu.i.posthog.com',opt_out_useragent_filter:true,autocapture:false,capture_pageview:false,capture_pageleave:false,capture_exceptions:false,capture_performance:false,person_profiles:'never',disable_persistence:true,persistence:'memory',advanced_disable_flags:true,advanced_disable_decide:true,disable_compression:true,request_batching:false,enable_recording_console_log:false,disable_external_dependency_loading:true,disable_session_recording:hold,session_recording:{maskAllInputs:true,maskTextSelector:'*',maskAllElementAttributes:true,blockSelector:'script,img,svg,video,audio,canvas,iframe,object,embed,.ph-no-capture,[data-private]',recordCrossOriginIframes:false,captureCanvas:{recordCanvas:false},maskCapturedNetworkRequestFn:()=>({url:'http://proof.invalid/ops-proof-v1/'})},before_send:(event)=>{
  if(event.event!=='$snapshot')return null;
  const p=event.properties;window.proofState.seen++;
  return{event:'$snapshot',timestamp:event.timestamp,uuid:event.uuid,properties:{token:p.token,distinct_id:actor,$session_id:p.$session_id,$window_id:p.$window_id,$snapshot_data:p.$snapshot_data,$snapshot_bytes:p.$snapshot_bytes,$lib:'web',$lib_version:'1.446.0',$snapshot_host:'proof.invalid',environment:'review',synthetic:'yes',$geoip_disable:true}};
 }});
 window.beginProof=function(){ posthog.sessionRecording.onRemoteConfig({ok:true,config:{sessionRecording:{sampleRate:1,minimumDurationMilliseconds:0,endpoint:'/s/',version:'v2'}}});
 posthog.startSessionRecording({sampling:true,linked_flag:true,trigger:'event'});
;setTimeout(()=>posthog.stopSessionRecording(),80000);};if(!hold)window.beginProof();
 return posthog.get_session_id();
};
window.stopProof=function(){posthog.stopSessionRecording();return window.proofState;};
