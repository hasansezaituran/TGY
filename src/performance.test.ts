import {describe,expect,it} from 'vitest';
import {assess,candidates,linkedOrder,location,shipmentWarnings,type Data,type Settings} from './domain';
import {createEngine} from './indexed';
import {seed} from './data';

function compare(data:Data){
 const engine=createEngine(data);
 for(const order of data.orders)expect(engine.assess(order)).toEqual(assess(order,data));
 for(const shipment of data.shipments){
  expect(engine.candidates(shipment)).toEqual(candidates(shipment,data));
  expect(engine.linkedOrder(shipment)).toEqual(linkedOrder(shipment,data));
  expect(engine.shipmentWarnings(shipment)).toEqual(shipmentWarnings(shipment,data));
 }
 for(const [material,ids] of Object.entries(data.requirements))for(const id of ids)expect(engine.location(id,material)).toEqual(location(data.movements,id,material));
}

describe('İndeksli motor eşdeğerlik ve hacim kontrolü',()=>{
 it('İndeksli yol demo veride tüm sonuçları referans motorla aynı üretir',()=>{compare(structuredClone(seed))});
 it('İade ve kalıp kurallarının dokuz birleşiminde sonuçlar korunur',()=>{
  for(const returns of ['unknown','net','gross'] as Settings['returns'][])for(const molds of ['unknown','all','any'] as Settings['molds'][]){
   const data=structuredClone(seed);data.settings={...data.settings,returns,molds,shipmentUnits:true};compare(data);
  }
 });
 it('Karma istisnalarda geçerli/bozuk link, tarih ve eksik veriler aynı değerlendirilir',()=>{
  const data=structuredClone(seed);
  data.links.s1=data.orders[0].id;data.links.s2='gecersiz-link';
  data.parts[0].status='Bilinmiyor';delete data.mappings['100487'];
  data.movements.push({...data.movements[0],id:'ayni-tarih',to:'BAŞKA DEPO'});
  data.movements.push({...data.movements[1],id:'bozuk-tarih',date:'2027-02-30'});
  data.shipments.push({...data.shipments[0],id:'eksik-seri',serial:'',note:''});compare(data);
 });
 it('Yeni veri nesnesiyle yeni indeks oluşturulunca eski sonuçlar sızmaz',()=>{
  const original=structuredClone(seed),before=createEngine(original),next=structuredClone(original);
  next.parts[0].status='Pasif';next.movements=[];next.shipments=[];
  const after=createEngine(next);
  expect(before.assess(original.orders[0]).part).toBe('Aktif');
  expect(after.assess(next.orders[0]).part).toBe('Pasif');
  expect(after.assess(next.orders[0]).shipments).toHaveLength(0);compare(next);
 });
 it('40.000 sentetik sevkiyat ve 2.000 siparişin tamamını indeksleyip değerlendirir',()=>{
  const count=40_000,orderCount=2_000,materialCount=100;
  const data:Data={settings:{returns:'gross',molds:'any',shipmentUnits:true,hoursUnit:'piece'},orders:[],parts:[],movements:[],shipments:[],requirements:{},mappings:{A:['DA']},links:{}};
  for(let i=0;i<materialCount;i++){
   const material=`M${i}`,ata=`K${i}`;
   data.parts.push({id:material,old:'',name:'Sentetik parça',status:'Aktif',mrp:'Test',hours:1,trim:.25});
   data.requirements[material]=[ata];
   data.movements.push({id:`m${i}`,material,name:'Sentetik parça',ata,asy:`ASY${i}`,from:'MERKEZ',to:'DA',date:'2026-01-01',reason:'Hacim testi'});
  }
  for(let i=0;i<orderCount;i++)data.orders.push({id:`o${i}`,material:`M${i%materialCount}`,name:'Sentetik parça',project:'HACİM',supplier:'A',supplierName:'A',number:`450026${i}`,line:'10',qty:20,received:20,returned:0,delivery:'Tamamlandı',price:10,deliveryOpen:'Kapalı',requestOpen:'Kapalı',status:'Kapalı',approval:'Onaylandı',currency:'USD'});
  for(let i=0;i<count;i++){
   const order=data.orders[i%orderCount];
   data.shipments.push({id:`s${i}`,supplier:'A',date:'2026-02-10',material:order.material,name:'Sentetik parça',serial:`SN${i}`,fai:'Seri',trim:'Trimli',order:order.number,note:`IRS${i}`});
  }
  const started=performance.now(),engine=createEngine(data),indexedAt=performance.now();
  let warningCount=0,matched=0;
  for(const shipment of data.shipments){
   warningCount+=engine.shipmentWarnings(shipment).length;
   if(engine.candidates(shipment).length===1&&engine.linkedOrder(shipment))matched++;
  }
  let associated=0,productive=0;
  for(const order of data.orders){
   const a=engine.assess(order);
   associated+=a.shipments.length;
   if(a.state==='Üretilebilir'&&a.net===20&&a.remaining===0)productive++;
  }
  const elapsed=performance.now()-started;
  expect(data.shipments).toHaveLength(count);expect(data.orders).toHaveLength(orderCount);
  expect(matched).toBe(count);expect(associated).toBe(count);expect(warningCount).toBe(0);expect(productive).toBe(orderCount);
  console.info(JSON.stringify({kontrol:'sentetik-hacim',sevkiyat:count,siparis:orderCount,indeksMs:Math.round(indexedAt-started),toplamMs:Math.round(elapsed),eslesen:matched,iliskiToplami:associated,uyari:warningCount}));
  // Geniş eşik yalnız belirgin karesel gerilemeyi yakalar; gerçek tarayıcı/ERP yük testi değildir.
  expect(elapsed).toBeLessThan(10_000);
 },20_000);
});
