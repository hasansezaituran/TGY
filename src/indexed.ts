import {assess, location, shipmentWarnings, type Data, type Movement, type Order, type Part, type PreparedLookups, type Shipment} from './domain';

// JSON tuple anahtarları, kodlarda ayraç karakteri bulunduğunda da çakışmaz.
const orderKey=(number:string,material:string,supplier:string)=>JSON.stringify([number,material,supplier]);
const moldKey=(ata:string,material:string)=>JSON.stringify([ata,material]);
type OrderGroup={orders:Order[];byId:Map<string,Order>;ambiguous:Shipment[]};
const append=<T>(map:Map<string,T[]>,key:string,value:T)=>{
 const list=map.get(key);
 if(list)list.push(value);else map.set(key,[value]);
};

/**
 * Değişmez bir Data anlık görüntüsü için oluşturulur; veri değiştiğinde yeniden kurulur.
 * İndeks kurulumu satır sayısına göre doğrusaldır. Kalıp geçmişleri yalnızca ilk
 * istendiğinde kendi grupları içinde sıralanır ve sonuç önbelleğe alınır.
 * Belirsiz sevkiyatlar her aday sipariş için çoğaltılmaz, aday grubunda paylaşılır.
 */
export function createEngine(data:Data){
 const groups=new Map<string,OrderGroup>();
 const parts=new Map<string,Part>();
 const serialCounts=new Map<string,number>();
 const movements=new Map<string,Movement[]>();
 const locations=new Map<string,ReturnType<typeof location>>();
 const linkedShipments=new Map<string,Shipment[]>();
 const warningCache=new WeakMap<Shipment,string[]>();
 const assessmentCache=new WeakMap<Order,ReturnType<typeof assess>>();
 const emptyOrders:Order[]=[],emptyShipments:Shipment[]=[];

 for(const order of data.orders){
  const key=orderKey(order.number,order.material,order.supplier);
  let group=groups.get(key);
  if(!group){group={orders:[],byId:new Map(),ambiguous:[]};groups.set(key,group)}
  group.orders.push(order);
  // Array.find davranışını korumak için ilk kimlik eşleşmesi tutulur.
  if(!group.byId.has(order.id))group.byId.set(order.id,order);
 }
 for(const part of data.parts)if(!parts.has(part.id))parts.set(part.id,part);
 for(const movement of data.movements)append(movements,moldKey(movement.ata,movement.material),movement);
 for(const shipment of data.shipments)serialCounts.set(shipment.serial,(serialCounts.get(shipment.serial)??0)+1);

 const groupFor=(shipment:Shipment)=>groups.get(orderKey(shipment.order,shipment.material,shipment.supplier));
 const candidates=(shipment:Shipment)=>groupFor(shipment)?.orders??emptyOrders;
 const linkedOrder=(shipment:Shipment)=>{
  const group=groupFor(shipment);
  return group?.byId.get(data.links[shipment.id])??(group?.orders.length===1?group.orders[0]:undefined);
 };
 for(const shipment of data.shipments){
  const linked=linkedOrder(shipment);
  if(linked)append(linkedShipments,linked.id,shipment);
  else groupFor(shipment)?.ambiguous.push(shipment);
 }

 const prepared:PreparedLookups={
  part:material=>parts.get(material),
  candidates,
  hasSelectedCandidate:shipment=>groupFor(shipment)?.byId.has(data.links[shipment.id])??false,
  serialCount:serial=>serialCounts.get(serial)??0,
  location:(ata,material)=>{
   const key=moldKey(ata,material);
   let result=locations.get(key);
   if(!result){result=location(movements.get(key)??[],ata,material);locations.set(key,result)}
   return result;
  },
  shipments:order=>linkedShipments.get(order.id)??emptyShipments,
  ambiguous:order=>groups.get(orderKey(order.number,order.material,order.supplier))?.ambiguous??emptyShipments,
  shipmentWarnings:shipment=>{
   let result=warningCache.get(shipment);
   if(!result){result=shipmentWarnings(shipment,data,prepared);warningCache.set(shipment,result)}
   return result;
  }
 };
 return {
  assess:(order:Order)=>{
   let result=assessmentCache.get(order);
   if(!result){result=assess(order,data,prepared);assessmentCache.set(order,result)}
   return result;
  },
  candidates,
  linkedOrder,
  shipmentWarnings:prepared.shipmentWarnings,
  location:prepared.location
 };
}
