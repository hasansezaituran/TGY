import {describe,expect,it} from 'vitest';
import {assess,delivery,linkedOrder,shipmentWarnings} from './domain';
import {seed} from './data';

describe('Kullanıcının doğruladığı iş kuralları',()=>{
 it('Örnek veri brüt gelen, alternatif kalıp, seri başına bir adet ve parça başına saat kullanır',()=>{
  expect(seed.settings).toEqual({returns:'gross',molds:'any',shipmentUnits:true,hoursUnit:'piece'});
 });
 it('Sipariş örneklerinin tamamında para birimi USD olarak açıkça belirtilmiştir',()=>{
  expect(seed.orders.length).toBeGreaterThan(0);
  expect([...new Set(seed.orders.map(o=>o.currency))]).toEqual(['USD']);
 });
 it('120 brüt gelen ve 5 iade net 115, kalan 5 sonucunu verir',()=>{
  const order={...seed.orders[0],qty:120,received:120,returned:5};
  expect(delivery(order,seed.settings)).toEqual({net:115,remaining:5,percent:115/120*100});
 });
 it('Ege siparişinde uygun K-006 alternatifi varken K-007 konumu eksik olsa da üretilebilir',()=>{
  const data=structuredClone(seed);
  const order=data.orders.find(o=>o.material==='MLZ-1006'&&o.supplier==='100487');
  expect(order,'Örnek veride Ege Metal için MLZ-1006 siparişi bulunmalı').toBeDefined();
  expect(data.requirements['MLZ-1006']).toContain('K-007');
  expect(data.movements.filter(m=>m.material==='MLZ-1006'&&m.ata==='K-007')).toHaveLength(0);
  const result=assess(order!,data);
  expect(result.mold).toBe('Kalıp uygun');
  expect(result.state).toBe('Üretilebilir');
 });
 it('Bir sevkiyat bir adettir; sevkiyat oluşturmak teslim alınan miktarı değiştirmez',()=>{
  const data=structuredClone(seed),order={...data.orders[0],id:'tek-siparis',number:'4500999',line:'10',qty:120,received:120,returned:5};
  data.orders=[order];
  data.shipments=[{...data.shipments[0],id:'tek-sevkiyat',serial:'SN-TEK',order:order.number,material:order.material,supplier:order.supplier}];
  const result=assess(order,data);
  expect(linkedOrder(data.shipments[0],data)?.id).toBe(order.id);
  expect(result.shipments).toHaveLength(1);
  expect(shipmentWarnings(data.shipments[0],data)).not.toContain('Mükerrer seri numarası');
  expect(result.net).toBe(115);
  expect(result.remaining).toBe(5);
  expect(result.warnings).toContain('Sevk / teslim miktarı farklı; sevk teslim alım değildir');
  expect(order.received).toBe(120);
  expect(order.returned).toBe(5);
 });
});
