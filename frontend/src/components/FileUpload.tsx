import {useId,useRef,useState} from 'react';
import {UploadCloud} from 'lucide-react';
import {useLocale} from '../hooks/useLocale';
import {Button} from './ui';
import './FileUpload.css';

export function FileUpload({label,accept,multiple=false,disabled=false,maxBytes,compact=false,description,emptyText,actionLabel,progressLabel,onFiles}:{label:string;accept:string;multiple?:boolean;disabled?:boolean;maxBytes?:number;compact?:boolean;description?:string;emptyText?:string;actionLabel?:string;progressLabel?:string;onFiles:(files:File[])=>void|Promise<void>}){
 const id=useId(),input=useRef<HTMLInputElement>(null),active=useRef(false),depth=useRef(0),{w}=useLocale();
 const [dragging,setDragging]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState('');
 async function receive(files:File[]){
  if(disabled||active.current||!files.length)return;
  setError('');
  if(!multiple&&files.length>1){setError(w('Choose one file for this upload.'));return;}
  if(maxBytes&&files.some(file=>file.size>maxBytes)){setError(w('A selected file is too large. Check the size limit and try again.'));return;}
  active.current=true;setBusy(true);
  try{await onFiles(files);}catch{setError(w('Upload failed. Your saved files are unchanged. Try again.'));}
  finally{active.current=false;setBusy(false);if(input.current)input.current.value='';}
 }
 return <div className={'upload-field'+(compact?' is-compact':'')+(dragging?' is-dragging':'')+(disabled||busy?' is-disabled':'')} onDragEnter={event=>{event.preventDefault();depth.current++;if(!disabled&&!busy)setDragging(true);}} onDragOver={event=>{event.preventDefault();event.dataTransfer.dropEffect=disabled||busy?'none':'copy';}} onDragLeave={event=>{event.preventDefault();depth.current=Math.max(0,depth.current-1);if(!depth.current)setDragging(false);}} onDrop={event=>{event.preventDefault();depth.current=0;setDragging(false);void receive(Array.from(event.dataTransfer.files));}}>
  <label id={id+'-label'} htmlFor={id}>{label}</label>
  <div className="upload-dropzone" aria-busy={busy}>
   <UploadCloud size={28} aria-hidden="true"/><p>{emptyText||w(compact?'Drop here, or':multiple?'Drop files here, or choose files':'Drop a file here, or choose a file')}</p>
   <input ref={input} id={id} className="upload-native" tabIndex={-1} type="file" accept={accept} multiple={multiple} disabled={disabled||busy} aria-describedby={id+'-help'} onChange={event=>void receive(Array.from(event.currentTarget.files||[]))}/>
   <Button type="button" variant="secondary" disabled={disabled||busy} loading={busy} onClick={()=>input.current?.click()}>{busy?(progressLabel||w('Uploading…')):(actionLabel||w(multiple?'Choose files':'Choose a file'))}</Button>
   <p className="supporting" id={id+'-help'}>{description|| (maxBytes?w('Maximum file size')+': '+Math.round(maxBytes/1024/1024)+' MB':w('Files are checked before saving.'))}</p>
  </div>{error&&<p className="field-error" role="alert">{error}</p>}
 </div>;
}
export function encodeUpload(file:File):Promise<string>{return new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(String(reader.result).split(',')[1]||'');reader.onerror=()=>reject(new Error('File could not be read'));reader.readAsDataURL(file);});}
