export type Part={id:string;old:string;name:string;status:'Aktif'|'Pasif'|'Bilinmiyor';mrp:string;hours:number;trim:number};
export type Order={id:string;material:string;name:string;project:string;supplier:string;supplierName:string;number:string;line:string;qty:number;received:number;returned:number;delivery:string;price:number;deliveryOpen:string;requestOpen:string;status:string;approval:string;currency?:string};
export type Movement={id:string;material:string;name:string;ata:string;asy:string;from:string;to:string;date:string;reason:string};
export type Shipment={id:string;supplier:string;date:string;material:string;name:string;serial:string;fai:string;trim:string;order:string;note:string};
export type Settings={returns:'unknown'|'net'|'gross';molds:'unknown'|'all'|'any';shipmentUnits:boolean;hoursUnit:'unknown'|'piece'|'batch'};
export type Data={orders:Order[];parts:Part[];movements:Movement[];shipments:Shipment[];requirements:Record<string,string[]>;mappings:Record<string,string[]>;links:Record<string,string>;settings:Settings};
/** Aynı veri anlık görüntüsü için hazırlanan, iş kurallarını değiştirmeyen arama dizinleri. */
export type PreparedLookups={
 part:(material:string)=>Part|undefined;
 candidates:(shipment:Shipment)=>Order[];
 hasSelectedCandidate:(shipment:Shipment)=>boolean;
 serialCount:(serial:string)=>number;
 location:(ata:string,material:string)=>ReturnType<typeof location>;
 shipments:(order:Order)=>Shipment[];
 ambiguous:(order:Order)=>Shipment[];
 shipmentWarnings:(shipment:Shipment)=>string[];
};
export function location(movements:Movement[],ata:string,material:string){
 const rows=movements.filter(m=>m.ata===ata&&m.material===material).sort((a,b)=>a.date.localeCompare(b.date));
 if(!rows.length)return {place:null,reason:'Kalıp hareketi / başlangıç konumu eksik',rows};
 if(rows.some((r,i)=>!/^\d{4}-\d{2}-\d{2}$/.test(r.date)||!Number.isFinite(Date.parse(r.date))||new Date(r.date).toISOString().slice(0,10)!==r.date||!r.to||(i>0&&(r.date===rows[i-1].date||r.from!==rows[i-1].to))))return {place:null,reason:'Aynı tarihli veya zinciri çelişen kalıp hareketi',rows};
 return {place:rows.at(-1)!.to,reason:'Kronolojik hareket zinciri doğrulandı',rows};
}
export function delivery(o:Order,s:Settings){
 if(o.returned>0&&s.returns==='unknown')return {net:null,remaining:null,percent:null};
 const net=o.received-(s.returns==='gross'?o.returned:0);
 return {net,remaining:o.qty-net,percent:o.qty>0?net/o.qty*100:null};
}
export function candidates(s:Shipment,d:Data){return d.orders.filter(o=>o.number===s.order&&o.material===s.material&&o.supplier===s.supplier)}
export function linkedOrder(s:Shipment,d:Data){const c=candidates(s,d);return c.find(o=>o.id===d.links[s.id])??(c.length===1?c[0]:undefined)}
export function shipmentWarnings(s:Shipment,d:Data,prepared?:PreparedLookups){
 const c=prepared?prepared.candidates(s):candidates(s,d),warnings:string[]=[];
 if(!c.length)warnings.push('Sipariş kaydı bulunamadı');
 if(c.length>1&&!(prepared?prepared.hasSelectedCandidate(s):c.some(o=>o.id===d.links[s.id])))warnings.push('Belirsiz sipariş kalemi eşleşmesi');
 if(!s.serial)warnings.push('Seri numarası eksik');
 if(s.serial&&(prepared?prepared.serialCount(s.serial):d.shipments.filter(x=>x.serial===s.serial).length)>1)warnings.push('Mükerrer seri numarası');
 if(!s.note)warnings.push('İrsaliye numarası eksik');
 if((prepared?prepared.part(s.material):d.parts.find(p=>p.id===s.material))?.status==='Pasif')warnings.push('Pasif parçaya ait sevkiyat');
 return warnings;
}
export function assess(o:Order,d:Data,prepared?:PreparedLookups){
 const part=prepared?prepared.part(o.material):d.parts.find(p=>p.id===o.material), reasons:string[]=[], blocks:string[]=[],missing:string[]=[];
 if(!part)missing.push('Parça kaydı eksik');else if(part.status==='Pasif')blocks.push('Parça üretim durumu pasif');else if(part.status!=='Aktif')missing.push('Parça üretim durumu bilinmiyor');
 const req=d.requirements[o.material], mapped=d.mappings[o.supplier];
 let mold='Belirlenemedi';
 if(!req?.length)missing.push('Gerekli kalıplar tanımlanmamış');
 else if(!mapped?.length)missing.push('Tedarikçi–depo eşleştirmesi eksik');
 else {
 const locs=req.map(id=>prepared?prepared.location(id,o.material):location(d.movements,id,o.material));
 const ok=locs.filter(l=>l.place&&mapped.includes(l.place)).length;
 const wrong=locs.filter(l=>l.place&&!mapped.includes(l.place)).length;
 if(req.length>1&&d.settings.molds==='unknown')missing.push('Birden fazla kalıbın birlikte / alternatif kullanımı tanımlanmadı');
 else if(d.settings.molds==='any'&&ok>0||ok===req.length)mold='Kalıp uygun';
 else if(d.settings.molds==='any'?wrong===req.length:wrong>0){mold='Kalıp uygun değil';blocks.push('Gerekli kalıp tedarikçide bulunmuyor')}
 else missing.push('Kalıp hareket geçmişi yetersiz veya çelişkili');
 }
 reasons.push(...blocks,...missing);
 const state=blocks.length?'Üretilemez':missing.length?'Kontrol gerekli':'Üretilebilir';
 const shipments=prepared?prepared.shipments(o):d.shipments.filter(s=>linkedOrder(s,d)?.id===o.id), ambiguous=prepared?prepared.ambiguous(o):d.shipments.filter(s=>candidates(s,d).some(x=>x.id===o.id)&&!linkedOrder(s,d));
 const warnings=[...reasons];
 if(o.approval!=='Onaylandı')warnings.push('Sipariş onayı bekleniyor (fiziksel üretilebilirlikten bağımsız)');
 const amounts=delivery(o,d.settings);
 if(amounts.net===null)warnings.push('İade hesaplama kuralı tanımlanmadı');
 if(amounts.net!==null&&(amounts.net<0||amounts.net>o.qty))warnings.push('Net teslimat miktarı sipariş sınırları dışında');
 if(ambiguous.length)warnings.push('Belirsiz sevkiyat eşleşmesi');
 if(shipments.length>1)warnings.push('Birden fazla sevkiyat kaydı');
 if(shipments.some(s=>(prepared?prepared.shipmentWarnings(s):shipmentWarnings(s,d)).length))warnings.push('Sevkiyat kayıtlarında veri uyarısı');
 if(d.settings.shipmentUnits&&amounts.net!==null&&shipments.length!==amounts.net)warnings.push('Sevk / teslim miktarı farklı; sevk teslim alım değildir');
 return {state,mold,part:part?.status??'Veri eksik',reasons:reasons.length?reasons:['Aktif parça ve gerekli kalıp konumu uygun'],warnings,shipments,ambiguous,...amounts,total:o.qty*o.price};
}
