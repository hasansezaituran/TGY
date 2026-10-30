import {describe, expect, it} from 'vitest';
import {assess, candidates, delivery, linkedOrder, location, shipmentWarnings, type Data, type Movement, type Order, type Shipment} from './domain';

function fixture():Data {
 const order:Order={id:'o1',material:'M1',name:'Bağlantı braketi',project:'P1',supplier:'A',supplierName:'A Firması',number:'45001',line:'10',qty:100,received:40,returned:0,delivery:'Kısmi',price:5,deliveryOpen:'Açık',requestOpen:'Açık',status:'Açık',approval:'Onaylandı',currency:'TRY'};
 return {orders:[order],parts:[{id:'M1',old:'ESK1',name:'Bağlantı braketi',status:'Aktif',mrp:'Deniz',hours:1,trim:.5}],movements:[movement('m1','2027-01-10','MERKEZ','DA')],shipments:[],requirements:{M1:['K1']},mappings:{A:['DA'],B:['DB']},links:{},settings:{returns:'unknown',molds:'unknown',shipmentUnits:false,hoursUnit:'unknown'}};
}
function movement(id:string,date:string,from:string,to:string):Movement{return {id,material:'M1',name:'Bağlantı braketi',ata:'K1',asy:'ASY1',from,to,date,reason:'Üretim'}}
function shipment(id='s1'):Shipment{return {id,supplier:'A',date:'2027-02-10',material:'M1',name:'Bağlantı braketi',serial:'SN1',fai:'Seri',trim:'Trimli',order:'45001',note:'IRS1'}}

describe('Gereksinimlerden bağımsız iş kuralı senaryoları',()=>{
 it('01 — Pasif parça üretilemez ve neden açıklanır',()=>{const d=fixture();d.parts[0].status='Pasif';const a=assess(d.orders[0],d);expect(a.state).toBe('Üretilemez');expect(a.reasons).toContain('Parça üretim durumu pasif')});
 it('02 — Gerekli kalıp başka depodaysa üretilemez',()=>{const d=fixture();d.movements[0].to='DB';const a=assess(d.orders[0],d);expect(a.state).toBe('Üretilemez');expect(a.mold).toBe('Kalıp uygun değil')});
 it('03 — Aktif parça ve doğru kalıp üretilebilir',()=>{const d=fixture();expect(assess(d.orders[0],d).state).toBe('Üretilebilir')});
 it('04 — Konumu bilinmeyen kalıp kontrol gerektirir',()=>{const d=fixture();d.movements=[];const a=assess(d.orders[0],d);expect(a.state).toBe('Kontrol gerekli');expect(a.mold).toBe('Belirlenemedi')});
 it('05 — Kalıp transferi A ve B siparişlerini yeniden hesaplatır',()=>{const d=fixture();d.orders.push({...d.orders[0],id:'oB',supplier:'B',line:'20'});expect(assess(d.orders[0],d).state).toBe('Üretilebilir');d.movements.push(movement('m2','2027-02-20','DA','DB'));expect(assess(d.orders[0],d).state).toBe('Üretilemez');expect(assess(d.orders[1],d).state).toBe('Üretilebilir')});
 it('06 — Eksik parça kaydı otomatik üretilemez sayılmaz',()=>{const d=fixture();d.parts=[];const a=assess(d.orders[0],d);expect(a.state).toBe('Kontrol gerekli');expect(a.reasons).toContain('Parça kaydı eksik')});
 it('07 — Mükerrer seri iki kayıtta da uyarı üretir',()=>{const d=fixture();d.shipments=[shipment('s1'),shipment('s2')];for(const s of d.shipments)expect(shipmentWarnings(s,d)).toContain('Mükerrer seri numarası')});
 it('08 — Tek aday sevkiyat siparişe bağlanır, teslimatı değiştirmez',()=>{const d=fixture();d.shipments=[shipment()];const a=assess(d.orders[0],d);expect(linkedOrder(d.shipments[0],d)?.id).toBe('o1');expect(a.shipments).toHaveLength(1);expect(a.net).toBe(40);expect(d.orders[0].received).toBe(40)});
 it('09 — İki adayda rastgele bağlantı kurulmaz, kullanıcı seçimi sınırlandırılır',()=>{const d=fixture();d.orders.push({...d.orders[0],id:'o2',line:'20'});const s=shipment();d.shipments=[s];expect(candidates(s,d)).toHaveLength(2);expect(linkedOrder(s,d)).toBeUndefined();expect(shipmentWarnings(s,d)).toContain('Belirsiz sipariş kalemi eşleşmesi');d.links.s1='o2';expect(linkedOrder(s,d)?.id).toBe('o2');d.links.s1='olmayan';expect(linkedOrder(s,d)).toBeUndefined()});
 it('10 — Parça verisi güncellenince üretilebilirlik değişir (Excel içe aktarma testi değildir)',()=>{const d=fixture();expect(assess(d.orders[0],d).state).toBe('Üretilebilir');d.parts=d.parts.map(p=>({...p,status:'Pasif' as const}));expect(assess(d.orders[0],d).state).toBe('Üretilemez')});
 it('11 — İade belirsizken hesap yok, net ve brüt kurallarda çift düşüm önlenir',()=>{const d=fixture(),o={...d.orders[0],returned:5};expect(delivery(o,d.settings)).toEqual({net:null,remaining:null,percent:null});expect(delivery(o,{...d.settings,returns:'net'})).toEqual({net:40,remaining:60,percent:40});expect(delivery(o,{...d.settings,returns:'gross'})).toEqual({net:35,remaining:65,percent:35})});
 it('12 — Sonradan eklenen geçmiş hareket güncel kronolojik konumu bozmaz',()=>{const d=fixture();d.movements=[movement('m2','2027-02-20','DA','DB'),movement('m1','2027-01-10','MERKEZ','DA')];expect(location(d.movements,'K1','M1').place).toBe('DB');d.movements.push(movement('m0','2027-01-01','X','MERKEZ'));expect(location(d.movements,'K1','M1').place).toBe('DB')});
});

describe('Ek veri bütünlüğü ve sınır koşulları',()=>{
 it('Aynı tarihli iki hareket lokasyonu belirsiz bırakır',()=>{const d=fixture();d.movements.push(movement('m2','2027-01-10','DA','DB'));expect(location(d.movements,'K1','M1').place).toBeNull();expect(assess(d.orders[0],d).state).toBe('Kontrol gerekli')});
 it('Hareket zinciri kopuksa kesin lokasyon verilmez',()=>{const d=fixture();d.movements.push(movement('m2','2027-02-10','BAŞKA','DB'));expect(location(d.movements,'K1','M1').place).toBeNull()});
 it('Kalıp hesabı orijinal hareket dizisini sıralayıp değiştirmez',()=>{const d=fixture();d.movements.unshift(movement('m2','2027-02-10','DA','DB'));const ids=d.movements.map(x=>x.id);location(d.movements,'K1','M1');expect(d.movements.map(x=>x.id)).toEqual(ids)});
 it('Çoklu kalıp kuralı bilinmiyorsa uygun kalıp olsa bile kontrol gerekir',()=>{const d=fixture();d.requirements.M1=['K1','K2'];expect(assess(d.orders[0],d).state).toBe('Kontrol gerekli')});
 it('Alternatif kalıplarda bir doğru kalıp yeterlidir',()=>{const d=fixture();d.requirements.M1=['K1','K2'];d.settings.molds='any';expect(assess(d.orders[0],d).state).toBe('Üretilebilir')});
 it('Tüm kalıplar gerekli olduğunda bir bilinmeyen kalıp kontrol gerektirir',()=>{const d=fixture();d.requirements.M1=['K1','K2'];d.settings.molds='all';expect(assess(d.orders[0],d).state).toBe('Kontrol gerekli')});
 it('Tüm kalıplar gerekliyse bir yanlış lokasyon üretimi engeller',()=>{const d=fixture();d.requirements.M1=['K1','K2'];d.settings.molds='all';d.movements.push({...movement('m2','2027-01-10','MERKEZ','DB'),ata:'K2'});expect(assess(d.orders[0],d).state).toBe('Üretilemez')});
 it('Pasif parça ve yanlış kalıp nedenlerinin ikisi de korunur',()=>{const d=fixture();d.parts[0].status='Pasif';d.movements[0].to='DB';const a=assess(d.orders[0],d);expect(a.reasons).toContain('Parça üretim durumu pasif');expect(a.reasons).toContain('Gerekli kalıp tedarikçide bulunmuyor')});
 it('Onay bekleyen sipariş fiziksel olarak üretilebilir kalır',()=>{const d=fixture();d.orders[0].approval='Bekliyor';const a=assess(d.orders[0],d);expect(a.state).toBe('Üretilebilir');expect(a.warnings.some(w=>w.includes('Sipariş onayı bekleniyor'))).toBe(true)});
 it('Tedarikçi adı benzer olsa da eşleştirme yoksa kontrol gerekir',()=>{const d=fixture();d.mappings={};expect(assess(d.orders[0],d).state).toBe('Kontrol gerekli')});
 it('Malzeme eski kodu kendiliğinden eşdeğer sayılmaz',()=>{const d=fixture();d.orders[0].material='ESK1';expect(assess(d.orders[0],d).part).toBe('Veri eksik')});
 it('Farklı tedarikçi sevkiyat adayı sayılmaz',()=>{const d=fixture();const s={...shipment(),supplier:'B'};expect(candidates(s,d)).toHaveLength(0);expect(shipmentWarnings(s,d)).toContain('Sipariş kaydı bulunamadı')});
 it('Eksik irsaliye ve pasif parça sevkiyat uyarıları birlikte gösterilir',()=>{const d=fixture();d.parts[0].status='Pasif';const s={...shipment(),note:''};expect(shipmentWarnings(s,d)).toContain('İrsaliye numarası eksik');expect(shipmentWarnings(s,d)).toContain('Pasif parçaya ait sevkiyat')});
 it('Sevkiyat birim kuralı doğrulanmadan miktar farkı iddia edilmez',()=>{const d=fixture();d.shipments=[shipment()];expect(assess(d.orders[0],d).warnings.some(w=>w.includes('Sevk / teslim miktarı farklı'))).toBe(false);d.settings.shipmentUnits=true;expect(assess(d.orders[0],d).warnings.some(w=>w.includes('Sevk / teslim miktarı farklı'))).toBe(true)});
 it('Sıfır sipariş miktarında yüzde hesaplanmaz',()=>{const d=fixture();expect(delivery({...d.orders[0],qty:0},d.settings).percent).toBeNull()});
});

describe('Hatalı tarih kontrolü',()=>{
 it.each(['tarih-yok','2027-02-30','2027-13-01'])('Geçersiz tarih %s kesin kalıp konumu üretmez',date=>{const d=fixture();d.movements[0].date=date;expect(location(d.movements,'K1','M1').place).toBeNull();expect(assess(d.orders[0],d).state).toBe('Kontrol gerekli')});
});
