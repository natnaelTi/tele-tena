/** Pinned PostHog policy. Runtime remains gated until project proof is recorded. */
import type {PostHogConfig} from 'posthog-js';
export const REPLAY_POLICY_VERSION='teletena-masked-web-v1';
export const replayPolicy:Partial<PostHogConfig>={autocapture:false,capture_pageview:false,capture_pageleave:false,capture_exceptions:false,disable_session_recording:true,disable_persistence:true,persistence:'memory',person_profiles:'never',enable_recording_console_log:false,capture_performance:false,disable_external_dependency_loading:true,session_recording:{maskAllInputs:true,maskTextSelector:'*',maskAllElementAttributes:true,captureCanvas:{recordCanvas:false},blockSelector:'img,svg,video,audio,canvas,iframe,object,embed,input[type="file"],input[type="hidden"],.attachment-preview,.ph-no-capture,[data-private],.consultation-room'},before_send:()=>null};
// No snapshot is transmitted under this quarantined policy. It is deliberately
// unavailable, rather than a false claim of useful verified replay. Actual project
// and canary/export/player validation must replace the gate in a reviewed change.
export async function preparedReplayVersion(){const{PostHog}=await import('posthog-js');return {sdkAvailable:typeof PostHog==='function',policy:REPLAY_POLICY_VERSION,enabled:false};}
