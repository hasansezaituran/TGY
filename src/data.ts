import type {Data} from './domain';
export const seed:Data={
 settings:{returns:'gross',molds:'any',shipmentUnits:true,hoursUnit:'piece'},links:{},
 mappings:{'100245':['ABC KOMPOZİT DEPOSU'],'100312':['ANADOLU DÖKÜM'],'100487':['EGE METAL DEPOSU']},
 requirements:{'MLZ-1001':['K-001'],'MLZ-1002':['K-002'],'MLZ-1003':['K-003'],'MLZ-1004':['K-004'],'MLZ-1005':['K-005'],'MLZ-1006':['K-006','K-007']},
 parts:[
 {id:'MLZ-1001',old:'ESK-401',name:'Türbin bağlantı braketi',status:'Aktif',mrp:'Deniz Yılmaz',hours:1.8,trim:.4},
 {id:'MLZ-1002',old:'ESK-402',name:'Motor taşıyıcı gövde',status:'Aktif',mrp:'Elif Demir',hours:3.2,trim:.8},
 {id:'MLZ-1003',old:'ESK-403',name:'Hidrolik kapak',status:'Pasif',mrp:'Deniz Yılmaz',hours:1.2,trim:.3},
 {id:'MLZ-1004',old:'',name:'Kompresör flanşı',status:'Aktif',mrp:'Mert Kaya',hours:2.4,trim:.6},
 {id:'MLZ-1005',old:'ESK-405',name:'Bağlantı adaptörü',status:'Aktif',mrp:'Elif Demir',hours:.9,trim:.2},
 {id:'MLZ-1006',old:'',name:'Soğutma kanalı',status:'Aktif',mrp:'Mert Kaya',hours:2.1,trim:.5}],
 orders:[],movements:[],shipments:[]
};
const suppliers=[['100245','ABC Kompozit'],['100312','Anadolu Döküm'],['100487','Ege Metal']];
seed.orders=Array.from({length:18},(_,i)=>{
 const material=`MLZ-100${i%7+1}`,part=seed.parts.find(p=>p.id===material),s=suppliers[i%3];
 return {id:`o${i+1}`,material,name:part?.name??'Kontrol valfi muhafazası',project:['TF-2027','GÖKBEY','HÜRJET'][i%3],supplier:s[0],supplierName:s[1],number:`4500027${String(Math.floor(i/2)+1).padStart(3,'0')}`,line:i%2?'20':'10',qty:[120,80,240,60][i%4],received:i%5===0?120:i%3===0?20:0,returned:i===0?5:0,delivery:i%5===0?'Tamamlandı':i%3===0?'Kısmi teslimat':'Teslimat bekliyor',price:[1850,3200,760,2400][i%4],deliveryOpen:'Açık',requestOpen:'Açık',status:'Açık',approval:i%4?'Onaylandı':'Onay bekliyor',currency:'USD'};
});
// Aynı sipariş / malzeme / tedarikçi için iki aday: rastgele eşleştirilmez.
seed.orders[1]={...seed.orders[0],id:'o2',line:'20',returned:0,received:0};
seed.movements=[
 {id:'m1',material:'MLZ-1001',name:'Türbin bağlantı braketi',ata:'K-001',asy:'ASY-101',from:'MERKEZ DEPO',to:'ABC KOMPOZİT DEPOSU',date:'2027-01-08',reason:'Üretime hazırlık'},
 {id:'m2',material:'MLZ-1002',name:'Motor taşıyıcı gövde',ata:'K-002',asy:'ASY-102',from:'MERKEZ DEPO',to:'EGE METAL DEPOSU',date:'2027-01-10',reason:'Planlı üretim'},
 {id:'m3',material:'MLZ-1003',name:'Hidrolik kapak',ata:'K-003',asy:'ASY-103',from:'MERKEZ DEPO',to:'ABC KOMPOZİT DEPOSU',date:'2027-01-12',reason:'Numune üretimi'},
 {id:'m4',material:'MLZ-1005',name:'Bağlantı adaptörü',ata:'K-005',asy:'ASY-105',from:'MERKEZ DEPO',to:'ANADOLU DÖKÜM',date:'2027-01-14',reason:'Üretime hazırlık'},
 {id:'m5',material:'MLZ-1005',name:'Bağlantı adaptörü',ata:'K-005',asy:'ASY-105',from:'ANADOLU DÖKÜM',to:'ABC KOMPOZİT DEPOSU',date:'2027-02-03',reason:'Tedarikçi transferi'},
 {id:'m6',material:'MLZ-1006',name:'Soğutma kanalı',ata:'K-006',asy:'ASY-106',from:'MERKEZ DEPO',to:'EGE METAL DEPOSU',date:'2027-02-01',reason:'Üretime hazırlık'}];
seed.shipments=[
 {id:'s1',supplier:'100245',date:'2027-02-08',material:'MLZ-1001',name:'Türbin bağlantı braketi',serial:'SN-27001',fai:'Seri',trim:'Trimli',order:seed.orders[0].number,note:'IRS-27001'},
 {id:'s2',supplier:'100245',date:'2027-02-09',material:'MLZ-1001',name:'Türbin bağlantı braketi',serial:'SN-27001',fai:'Seri',trim:'Trimli',order:seed.orders[0].number,note:'IRS-27002'},
 {id:'s3',supplier:'100487',date:'2027-02-10',material:'MLZ-1003',name:'Hidrolik kapak',serial:'SN-27003',fai:'FAİ',trim:'Trimsiz',order:seed.orders[2].number,note:''},
 {id:'s4',supplier:'100312',date:'2027-01-22',material:'MLZ-1002',name:'Motor taşıyıcı gövde',serial:'SN-27004',fai:'Seri',trim:'Trimli',order:'4500099999',note:'IRS-27004'}];

/** 2026 hacmini referans alan, 2027 için sentetik test verisi; gerçek geçmiş kayıt değildir. */
export function addVolumeDemo(data:Data):Data {
 const shipments=[...data.shipments];
 for(let i=shipments.length;i<40000;i++){
  const o=data.orders[i%data.orders.length];
  shipments.push({id:`hacim-${i}`,supplier:o.supplier,date:'2027-02-12',material:o.material,name:o.name,serial:`HACIM-${i}`,fai:'Seri',trim:'Trimli',order:o.number,note:`TEST-IRS-${i}`});
 }
 return {...data,shipments};
}
