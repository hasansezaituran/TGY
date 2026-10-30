// İzole geçici SQLite üzerinde gerçek tarayıcı + API + Excel testi.
import {chromium} from '@playwright/test';
import {spawn} from 'node:child_process';
import {mkdtemp,writeFile,readFile} from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import assert from 'node:assert/strict';
import ExcelJS from 'exceljs';
import {seed} from '../src/data.ts';
const root=process.cwd(),temp=await mkdtemp(path.join(os.tmpdir(),'tgy-fullstack-'));
const base='http://127.0.0.1:5174',api='http://127.0.0.1:8001';
const children=[];let browser;
function launch(command,args,env={}){const child=spawn(command,args,{cwd:root,env:{...process.env,...env},stdio:['ignore','pipe','pipe']});let output='';child.stdout.on('data',x=>output+=x);child.stderr.on('data',x=>output+=x);child.on('error',e=>output+=e.message);children.push(child);return {child,output:()=>output}}
async function ready(url,process){for(let i=0;i<150;i++){if(process.child.exitCode!==null)throw Error(process.output());try{if((await fetch(url)).ok)return}catch{}await new Promise(r=>setTimeout(r,100))}throw Error('Sunucu hazır olmadı: '+process.output())}
try{
 const backend=launch(path.join(root,'.venv/bin/python'),['-m','uvicorn','backend.main:app','--host','127.0.0.1','--port','8001'],{DATABASE_URL:`sqlite:///${temp}/test.db`});await ready(api+'/api/health',backend);
 const frontend=launch(process.execPath,['node_modules/vite/bin/vite.js','--host','127.0.0.1','--port','5174','--strictPort'],{TGY_API_TARGET:api});await ready(base,frontend);
 const template=await fetch(api+'/api/template');const book=new ExcelJS.Workbook();await book.xlsx.load(await template.arrayBuffer());
 const fields={orders:['material','name','project','supplier','supplierName','number','line','qty','received','returned','delivery','price','deliveryOpen','requestOpen','status','approval','currency'],parts:['id','old','name','status','mrp','hours','trim'],movements:['material','name','ata','asy','from','to','date','reason'],shipments:['supplier','date','material','name','serial','fai','trim','order','note']};
 const names={orders:'Sipariş Kalemleri',parts:'Parça Bilgileri',movements:'Kalıp Bilgileri',shipments:'Sevkiyat Listesi'};
 for(const [entity,cols] of Object.entries(fields))for(const row of seed[entity])book.getWorksheet(names[entity]).addRow(cols.map(key=>row[key]));
 const filename=path.join(temp,'veri.xlsx');await book.xlsx.writeFile(filename);
 browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox']});const page=await browser.newPage({viewport:{width:1440,height:1000}});const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(base);await page.getByRole('button',{name:'Veriyi yenile',exact:true}).waitFor();await page.locator('.saving-overlay').waitFor({state:'hidden'});
 assert.equal(await page.getByLabel('Çalışma alanı').inputValue(),'real');assert.equal(await page.locator('tbody tr').count(),0);
 await page.locator('nav').getByRole('button',{name:'Veri Aktarımı',exact:true}).click();
 await page.locator('input[type=file]').setInputFiles(filename);await page.getByRole('button',{name:'Dosyayı doğrula ve önizle'}).click();await page.getByRole('heading',{name:'Aktarım önizlemesi'}).waitFor();
 let state=await (await fetch(api+'/api/state')).json();assert.equal(state.data.orders.length,0);
 assert.equal(await page.getByRole('button',{name:'Onaylanan aktarımı uygula'}).isDisabled(),true);
 await page.getByLabel('Önizlemeyi ve uyarıları inceledim; belirtilen aktarımı onaylıyorum.').check();await page.getByRole('button',{name:'Onaylanan aktarımı uygula'}).click();await page.getByText(/34 yeni kayıt eklendi/).waitFor();await page.locator('.saving-overlay').waitFor({state:'hidden'});
 state=await (await fetch(api+'/api/state')).json();assert.equal(state.data.orders.length,18);assert.equal(state.data.shipments.length,4);
 console.log('BAŞARILI: Gerçek XLSX dosyası önizleme, onay ve kalıcı aktarım; onaysız kaynak yazılmadı.');
 await page.locator('nav').getByRole('button',{name:'Ayarlar',exact:true}).click();let mapping=page.locator('label').filter({hasText:'100245 · ABC Kompozit'});await mapping.locator('input').fill('ABC KOMPOZİT DEPOSU');await mapping.getByRole('button',{name:'Uygula',exact:true}).click();await page.locator('.saving-overlay').waitFor({state:'hidden'});
 await page.locator('nav').getByRole('button',{name:'Parça Bilgileri',exact:true}).click();await page.getByLabel('Satır detayını aç').first().click();let requirement=page.locator('label').filter({hasText:'Alternatif Kalıp ATA Kodları'});await requirement.locator('input').fill('K-001');await requirement.getByRole('button',{name:'Uygula',exact:true}).click();await page.locator('.saving-overlay').waitFor({state:'hidden'});
 let computed=await (await fetch(api+'/api/assessments')).json();let first=Object.values(computed.items).find(a=>a.state==='Üretilebilir');assert.ok(first);
 await page.getByLabel('Parça üretim durumu').selectOption('Pasif');await page.locator('.saving-overlay').waitFor({state:'hidden'});
 assert.equal(await page.locator('.drawer .badge.bad').count(),4);
 await page.reload();await page.locator('.saving-overlay').waitFor({state:'hidden'});await page.locator('nav').getByRole('button',{name:'Parça Bilgileri',exact:true}).click();await page.getByLabel('Satır detayını aç').first().click();assert.equal(await page.getByLabel('Parça üretim durumu').inputValue(),'Pasif');
 state=await (await fetch(api+'/api/state')).json();assert.equal(state.data.settings.returns,'gross');assert.equal(state.data.requirements['MLZ-1001'][0],'K-001');
 const orders=await (await fetch(api+'/api/orders?page_size=500')).json();const order=orders.items.find(o=>o.material==='MLZ-1001'&&o.line==='10');assert.equal(order.computed.net,115);assert.equal(order.computed.remaining,5);assert.equal(order.computed.state,'Üretilemez');
 console.log('BAŞARILI: Depo/kalıp ilişkisi, Python hesaplaması115/5, parça düzenleme ve yenilemede kalıcılık.');
 await page.getByLabel('Detayı kapat').click();await page.locator('nav').getByRole('button',{name:'Sipariş Kalemleri'}).click();await page.getByRole('button',{name:'Kayıt ekle',exact:true}).click();await page.getByLabel('Kayıt formunu kapat').click();
 await page.locator('nav').getByRole('button',{name:'Veri Aktarımı',exact:true}).click();const download=page.waitForEvent('download');await page.getByRole('link',{name:'Tüm kaynak verileri yedekle'}).click();const f=await download;const saved=path.join(temp,'yedek.xlsx');await f.saveAs(saved);const backup=new ExcelJS.Workbook();await backup.xlsx.readFile(saved);assert.equal(backup.getWorksheet('Sipariş Kalemleri').rowCount,19);
 await page.locator('nav').getByRole('button',{name:'Raporlar',exact:true}).click();await page.getByRole('heading',{name:'İşlem geçmişi'}).waitFor();await page.getByText('Excel aktarımı · Sürüm 1',{exact:true}).waitFor();
 const bad=await fetch(api+'/api/changes',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({expected_revision:0,changes:[]})});assert.equal(bad.status,409);
 await page.getByLabel('Çalışma alanı').selectOption('demo');await page.locator('nav').getByRole('button',{name:'Parça Bilgileri',exact:true}).click();await page.getByLabel('Satır detayını aç').first().click();assert.equal(await page.getByLabel('Parça üretim durumu').inputValue(),'Aktif');
 assert.equal((await (await fetch(api+'/api/state')).json()).data.parts[0].status,'Pasif');
 assert.deepEqual(errors,[]);await page.screenshot({path:path.join(temp,'asama2.png'),fullPage:true});console.log('BAŞARILI: Excel yedekleme, işlem geçmişi, eski sürüm409 ve demo/gerçek veri izolasyonu.');
 console.log('Test çıktıları: '+temp);
}finally{if(browser)await browser.close();for(const child of children.reverse())child.kill('SIGTERM');}
