import {useEffect,useState} from 'react';
import {api} from '../api';
import {Button,InlineNotice} from './ui';
import {FileUpload,encodeUpload} from './FileUpload';
import {useLocale} from '../hooks/useLocale';
type Document={id:string;filename:string;content_size:number;created:string};
const endpoint='tele_tena.api.history_documents.';
export default function HistoryDocuments(){
 const {w}=useLocale(),[documents,setDocuments]=useState<Document[]|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState(''),[message,setMessage]=useState(''),[queue,setQueue]=useState<{file:File;key:string;state:'queued'|'uploading'|'saved'|'failed'}[]>([]);
 async function load(){try{const result=await api<{documents:Document[]}>(endpoint+'list_documents');setDocuments(result.documents);setError('');}catch{setError(w('Your documents could not be loaded. Try again.'));}}
 useEffect(()=>{void load();},[]);
 async function upload(files:File[]){setBusy(true);setError('');setMessage('');let saved=0,failed=0;
  const key=(file:File)=>file.name+':'+file.size+':'+file.lastModified;
  setQueue(previous=>[...previous.filter(item=>!files.some(file=>key(file)===item.key)),...files.map(file=>({file,key:key(file),state:'queued' as const}))]);
  for(const file of files){const update=(state:'uploading'|'saved'|'failed')=>setQueue(previous=>previous.map(item=>item.key===key(file)?{...item,state}:item));update('uploading');
   try{await api(endpoint+'upload',{filename:file.name,content_base64:await encodeUpload(file)},true);saved++;update('saved');}
   catch{failed++;update('failed');}
  }
  setBusy(false);if(saved)setMessage(w('Your documents are saved.'));if(failed)setError(w('Some files could not be uploaded. Retry those files individually.'));
  const result=await api<{documents:Document[]}>(endpoint+'list_documents').catch(()=>null);if(result)setDocuments(result.documents);
 }

 return <section data-tour-unsaved={queue.some(item=>item.state==='failed'||item.state==='uploading')||undefined} aria-label={w('Medical history documents')}><h3>{w('Medical history documents')}</h3><p className="supporting">{w('Uploading keeps files private. Choose individual files later in the encounter sharing preview. Removing your copy revokes future access;previously shared snapshots are retained for governance review.')}</p><FileUpload label={w('Add medical history files')} accept="application/pdf,image/jpeg,image/png,.pdf,.jpg,.jpeg,.png" multiple maxBytes={5*1024*1024} disabled={busy} onFiles={upload}/><p className="supporting">{w('PDF, JPEG or PNG. Up to 5 MB per file.')}</p>{queue.length>0&&<div className="upload-progress" role="status"><progress max={queue.length} value={queue.filter(item=>item.state==='saved').length}/><ul>{queue.map(item=><li key={item.key}><span>{item.file.name} · {Math.ceil(item.file.size/1024)} KB · {w(item.state==='saved'?'Saved':item.state==='failed'?'Upload failed':item.state==='uploading'?'Uploading…':'Waiting')}</span>{item.state==='failed'&&<Button variant="quiet" disabled={busy} onClick={()=>void upload([item.file])}>{w('Retry')}</Button>}</li>)}</ul></div>}{!documents&&!error&&<p role="status">{w('Loading documents…')}</p>}{documents?.length===0&&<p>{w('No documents uploaded yet.')}</p>}<ul className="history-document-list">{documents?.map(document=><li key={document.id}><div><strong>{document.filename}</strong><p className="supporting">{Math.ceil(document.content_size/1024)} KB</p></div><div className="actions"><a className="text-link" href={'/api/method/'+endpoint+'download?id='+encodeURIComponent(document.id)}>{w('Download')}</a><Button type="button" variant="quiet" disabled={busy} aria-label={w('Remove')+' '+document.filename} onClick={async()=>{setBusy(true);setError('');try{await api(endpoint+'remove',{id:document.id},true);await load();setMessage(w('Document removed.'));}catch{setError(w('Document could not be removed. Try again.'));}finally{setBusy(false);}}}>{w('Remove')}</Button></div></li>)}</ul>{error&&<InlineNotice tone="danger">{error} {!documents&&<Button type="button" variant="quiet" onClick={()=>void load()}>{w('Try again')}</Button>}</InlineNotice>}{message&&<p role="status">{message}</p>}</section>;
}
