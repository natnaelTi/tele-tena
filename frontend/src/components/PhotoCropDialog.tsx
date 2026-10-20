import {useEffect,useRef,useState} from 'react';
import {useLocale} from '../hooks/useLocale';
import {Button,Dialog,InlineNotice} from './ui';

type Draft={url:string;image:HTMLImageElement};
export default function PhotoCropDialog({draft,busy,error,onCancel,onSave}:{draft:Draft;busy:boolean;error:string;onCancel:()=>void;onSave:(content:string)=>Promise<void>}){
 const {w}=useLocale(),canvas=useRef<HTMLCanvasElement>(null),drag=useRef<{x:number;y:number}|null>(null);
 const [zoom,setZoom]=useState(1),[x,setX]=useState(50),[y,setY]=useState(50);
 const side=Math.min(draft.image.naturalWidth,draft.image.naturalHeight)/zoom;
 useEffect(()=>{const c=canvas.current,ctx=c?.getContext('2d');if(!c||!ctx)return;ctx.clearRect(0,0,512,512);ctx.fillStyle='#fff';ctx.fillRect(0,0,512,512);ctx.drawImage(draft.image,(draft.image.naturalWidth-side)*x/100,(draft.image.naturalHeight-side)*y/100,side,side,0,0,512,512);},[draft,side,x,y]);
 return <Dialog open onOpenChange={open=>{if(!open&&!busy)onCancel();}} title={w('Adjust your photo')} description={w('Drag to position your photo, or use the sliders. Nothing uploads until you save.')} className="photo-crop-dialog">
 <div className="photo-crop-preview"><canvas ref={canvas} width={512} height={512} aria-label={w('Profile photo crop preview')} onPointerDown={e=>{if(busy)return;e.currentTarget.setPointerCapture(e.pointerId);drag.current={x:e.clientX,y:e.clientY};}} onPointerMove={e=>{if(!drag.current||busy)return;const width=e.currentTarget.getBoundingClientRect().width,dx=e.clientX-drag.current.x,dy=e.clientY-drag.current.y;drag.current={x:e.clientX,y:e.clientY};const horizontal=draft.image.naturalWidth-side,vertical=draft.image.naturalHeight-side;setX(v=>horizontal?Math.max(0,Math.min(100,v-dx*side/width/horizontal*100)):50);setY(v=>vertical?Math.max(0,Math.min(100,v-dy*side/width/vertical*100)):50);}} onPointerUp={()=>{drag.current=null;}} onPointerCancel={()=>{drag.current=null;}}/><span aria-hidden="true"/></div>
 <div className="photo-crop-sliders">{[{label:'Zoom',min:1,max:3,step:.01,value:zoom,set:setZoom,disabled:false},{label:'Horizontal position',min:0,max:100,step:1,value:x,set:setX,disabled:draft.image.naturalWidth===side},{label:'Vertical position',min:0,max:100,step:1,value:y,set:setY,disabled:draft.image.naturalHeight===side}].map(field=><label key={field.label}>{w(field.label)}<input type="range" min={field.min} max={field.max} step={field.step} value={field.value} onChange={e=>field.set(Number(e.target.value))} disabled={busy||field.disabled} aria-valuetext={field.label==='Zoom'?Math.round(zoom*100)+'%':Math.round(field.value)+'%'}/></label>)}</div>
 {error&&<InlineNotice tone="danger">{w(error)}</InlineNotice>}
 <div className="dialog-actions"><Button loading={busy} onClick={()=>{const c=canvas.current;if(c)void onSave(c.toDataURL('image/jpeg',.9).split(',')[1]);}}>{w('Save photo')}</Button><Button variant="secondary" disabled={busy} onClick={()=>{setZoom(1);setX(50);setY(50);}}>{w('Reset crop')}</Button><Button variant="quiet" disabled={busy} onClick={onCancel}>{w('Cancel')}</Button></div>
 </Dialog>;
}
export type {Draft as PhotoDraft};
