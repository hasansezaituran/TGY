import {useEffect,useRef,useState} from 'react';
import {seed} from './data';
import type {Data} from './domain';
import type {createEngine} from './indexed';
export type Assessment=Omit<ReturnType<ReturnType<typeof createEngine>['assess']>,'net'|'remaining'|'percent'>&{net:number|null;remaining:number|null;percent:number|null};
export type Mode='real'|'demo';
const empty=():Data=>({orders:[],parts:[],movements:[],shipments:[],requirements:{},mappings:{},links:{},settings:{...seed.settings}});
export async function request<T>(url:string,options:RequestInit={}):Promise<T>{
 const response=await fetch(url,options);
 if(!response.ok){let message=`Sunucu isteği tamamlanamadı (${response.status}).`;try{const body=await response.json();message=typeof body.detail==='string'?body.detail:JSON.stringify(body.detail??body)}catch{/* Yanıt JSON olmayabilir. */}throw new Error(message)}
 return response.json();
}
export function useWorkspace(){
 const [mode,selectMode]=useState<Mode>(()=>localStorage.getItem('tgy-mode')==='demo'?'demo':'real');
 const [data,update]=useState<Data>(()=>mode==='demo'?structuredClone(seed):empty());
 const [computed,setComputed]=useState<Record<string,Assessment>>({}),[revision,setRevision]=useState(0),[busy,setBusy]=useState(false),[error,setError]=useState(''),[saved,setSaved]=useState('');
 const generation=useRef(0),locked=useRef(false);
 async function load(gen=generation.current){
  const state=await request<{data:Data;revision:number}>('/api/state');
  const assessments=await request<{items:Record<string,Omit<Assessment,'shipments'|'ambiguous'>&{shipments:string[];ambiguous:string[]}>;revision:number}>('/api/assessments');
  if(state.revision!==assessments.revision)throw new Error('Veriler yüklenirken başka bir işlem yapıldı. Yenileyerek tekrar deneyin.');
  if(gen!==generation.current)return;
  const shipments=new Map(state.data.shipments.map(s=>[s.id,s]));
  const items=Object.fromEntries(Object.entries(assessments.items).map(([id,a])=>[id,{...a,shipments:a.shipments.map(id=>shipments.get(id)!).filter(Boolean),ambiguous:a.ambiguous.map(id=>shipments.get(id)!).filter(Boolean)}]));
  update(state.data);setComputed(items);setRevision(state.revision);
 }
 async function reload(){if(locked.current)return;locked.current=true;setBusy(true);setError('');try{await load()}catch(e){setError(e instanceof Error?e.message:'Veriler yüklenemedi.')}finally{locked.current=false;setBusy(false)}}
 useEffect(()=>{const gen=++generation.current;setError('');setSaved('');if(mode==='demo'){update(structuredClone(seed));setComputed({});return}update(empty());setComputed({});locked.current=true;setBusy(true);load(gen).catch(e=>{if(gen===generation.current)setError('Sunucu bağlantısı kurulamadı: '+e.message)}).finally(()=>{if(gen===generation.current){locked.current=false;setBusy(false)}})},[mode]);
 function setMode(next:Mode){if(locked.current)return;localStorage.setItem('tgy-mode',next);selectMode(next)}
 async function setData(next:Data):Promise<boolean>{
  if(mode==='demo'){update(next);return true}
  if(locked.current)return false;
  const changes:{entity:string;id?:string;value:unknown}[]=[];
  for(const entity of ['orders','parts','movements','shipments'] as const){const before=new Map(data[entity].map(row=>[row.id,row]));for(const row of next[entity])if(JSON.stringify(before.get(row.id))!==JSON.stringify(row))changes.push({entity,id:row.id,value:row})}
  for(const entity of ['requirements','mappings','links'] as const)for(const [id,value] of Object.entries(next[entity]))if(JSON.stringify(data[entity][id])!==JSON.stringify(value))changes.push({entity,id,value});
  if(JSON.stringify(next.settings)!==JSON.stringify(data.settings))changes.push({entity:'settings',value:next.settings});
  if(!changes.length)return true;
  locked.current=true;setBusy(true);setError('');setSaved('');
  try{await request('/api/changes',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({expected_revision:revision,changes})});await load();setSaved('Değişiklik veri tabanına kaydedildi.');return true}catch(e){setError((e as Error).message+' İşlem sonucunu doğrulamak için güncel veriyi yenileyin.');return false}finally{locked.current=false;setBusy(false)}
 }
 return {data,setData,mode,setMode,busy,error,saved,revision,reload,computed};
}
