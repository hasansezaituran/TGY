# Python iş kuralı motoru — Aşama 2

`backend/rules.py`, onaylanan web prototipinin üretilebilirlik, teslimat, kalıp konumu ve sevkiyat eşleştirme kurallarını Python'a taşır. Bu modül dosya yükleme veya veri tabanı yazma işlemi yapmaz; bu görevler API ve aktarım katmanındadır.

## Kullanım sözleşmesi

```python
from backend.rules import build_engine

engine = build_engine(data)
result = engine.assess(data['orders'][0])
```

`data`, React uygulamasındaki `Data` alanlarını aynı adlarla taşır: `orders`, `parts`, `movements`, `shipments`, `requirements`, `mappings`, `links`, `settings`.

Motorun metotları:

- `assess(order)`: `state`, `mold`, `part`, `reasons`, `warnings`, `shipments`, `ambiguous`, `net`, `remaining`, `percent`, `total` döndürür.
- `candidates(shipment)`: sipariş numarası, malzeme ve tedarikçi kimliği aynı adayları verir.
- `linked_order(shipment)`: tek adayı veya geçerli açık seçimi verir; belirsizliği rastgele çözmez.
- `shipment_warnings(shipment)`: eksik sipariş/seri/irsaliye, belirsiz eşleşme, mükerrer seri ve pasif parça uyarılarını verir.
- `location(ata, material)`: tarih sıralı `rows`, `place` ve `reason` verir. Geçersiz tarih, aynı tarihli hareket veya kopuk zincir kesin konum üretmez.

Her motor girişin ayrı bir kopyasıyla çalışır. Kaynak veri değiştiğinde yeni motor oluşturulmalıdır. Süreç veya istekler arasında paylaşılan global önbellek yoktur. Dönen kayıtlar ve sonuçlar salt okunur kabul edilmelidir. Model/API doğrulaması motor çağrısından önce yapılır.

## Korunan kurallar

- Gelen miktar brüttür; net teslim alınan = gelen − iade. Kullanıcının bilerek başka kuralı seçebilmesi için prototipteki `unknown` ve `net` seçenekleri de korunur.
- Tanımlı alternatif kalıplardan birinin uygun konumda olması yeterlidir. Eksik alternatif, mevcut uygun alternatifi geçersiz kılmaz.
- Pasif parça her durumda üretilemez. Eksik parça otomatik üretilemez sayılmaz.
- Sipariş onayı fiziksel üretilebilirlikten ayrıdır.
- Tedarikçi–depo kimlik eşleştirmesi açıktır; isim benzerliği veya eski malzeme kodu otomatik eşdeğerlik oluşturmaz.
- Her sevkiyat satırı bir parça olarak karşılaştırılır; sevkiyat kaydı teslim alınan miktarı değiştirmez. Mükerrer seri kayıtları sessizce silinmez.
- Kaynak miktarlar ve hesaplanan miktarlar ayrı kalır. Miktar ve finansal çarpım Python `Decimal` ile hesaplanır; API sözleşmesi için sonuç JSON sayısına dönüştürülür. Alt sent tutarlar zorla iki haneye yuvarlanmaz; görüntüleme katmanındaki biçimlendirme ayrı bir sorumluluktur.

## Çalıştırılan geliştirici kontrolleri

```sh
cd /workspace/TGY
python -m unittest backend.tests.test_rules -v
```

**21 test başarılı, 0 başarısız.** İlk 12 test; pasif parça, yanlış depo, uygun kalıp/aktif parça, eksik kalıp, transfer, eksik parça, mükerrer seri, sevkiyatın teslim alımdan ayrılığı, belirsiz eşleşme, parça güncellemesi, iade ve geçmiş tarihli hareket senaryolarını kapsar. Parça güncellemesi testi gerçek Excel aktarımı testi olarak sunulmaz.

Ek testler alternatif kalıp kuralları, tüm alternatiflerin yanlış konumu, birden fazla olumsuz neden, çelişkili hareket/tarih, eski kod ve açık depo eşleştirmesi, onay ayrımı, ondalık hassasiyet ve sıfır miktar davranışını doğrular.

Sentetik hacim testi **40.000 sevkiyat ve 2.000 siparişin tamamını** gezer. 40.000 kesin eşleşme, toplam 40.000 ilişki, 2.000 doğru üretilebilirlik/net/kalan sonucu ve sıfır sevkiyat veri uyarısı doğrulandı. Son bu makine koşumunda indeks hazırlığı yaklaşık **203 ms**, tüm kontrol yaklaşık **329 ms** sürdü. Süre tek geliştirici koşumunun gözlemidir; gerçek ERP, Excel, veri tabanı, ağ, tarayıcı veya çok kullanıcılı yük garantisi değildir.

Bu belge geliştirici kontrolünü raporlar. Bağımsız QA sonuçları ve API/Excel/veri tabanı entegrasyon sonuçları ayrıca değerlendirilmelidir.
