# Aşama 2 — Bağımsız API ve Excel test raporu

## Yalnız Python dağıtımı — güncel sonuç

Dağıtım değişikliği sonrasında bağımsız QA tam backend grubunu yeniden çalıştırdı: **53/53 başarılı** (26 API, 6 dağıtım ve 21 Python iş kuralı testi). Ek dağıtım testleri Python sunucusundan derlenmiş HTML/JS/CSS erişimini, API önceliğini, boş gerçek çalışma alanını, API belgesini ve kaynak dosyalarının sunulmamasını doğruladı. Windows/macOS üzerinde doğrudan çalıştırma testi yapılmadı.

Geliştirici ayrıca `TGY-Python-Tam-Paket.zip` dosyasını temiz bir geçici klasöre açtı. PATH boş bırakılarak Node/npm erişimi olmadan `baslat.py` çalıştırıldı; sıfırdan venv ve runtime bağımlılıkları kuruldu. Tek Python sunucusu 8765 portunda açıldı. Chromium ile demo, JS/CSS, dinamik Excel indirme, gerçek modda yeni parça kaydı ve SQLite kaydı doğrulandı; tarayıcı hatası yoktu. Ctrl+C benzeri SIGINT ile servis temiz kapandı. Bu, Linux/Python 3.12 üzerinde geliştirici paket testidir; bağımsız QA veya Windows testi olarak sunulmaz.

## Güncel bağımsız sonuç

Kalite güvence ajanı, geliştirme ajanının yazdığı üretim kodunu değiştirmeden `backend/tests/test_api.py` içinde bağımsız kabul testleri oluşturdu. İlk bağımsız API kabul grubunda **25 test başarılı, 0 başarısız**; süre **15,68 saniye**. Kaynak arşivi regresyonuyla güncel bağımsız API test sayısı **26** oldu; son birlikte koşum aşağıda kayıtlıdır. Testler gerçek `.xlsx` dosyaları ve her senaryo için izole, geçici dosya SQLite veritabanı kullanır. Kullanıcının gerçek çalışma veritabanına örnek/test verisi yazılmaz.

Çalıştırma komutu, `/workspace/TGY` dizininde:

```bash
.venv/bin/python -m pytest backend/tests/test_api.py -q -s
```

Bulut sandbox'ı FastAPI TestClient'ın yerel thread/IPC işlemlerinde beklemeye yol açtığı için koşum genişletilmiş yerel yürütme izniyle yapılmıştır. Ağ servisine veya gerçek ERP'ye bağlanılmamıştır. Starlette/AnyIO geçişine ilişkin bir bağımlılık `DeprecationWarning` bildirimi oluşmuştur; test hatası yoktur.

## Birlikte son regresyon koşumu

Kalite güvence ajanı daha sonra `.venv/bin/python -m pytest backend/tests -q -s` ile tüm backend grubunu bağımsız olarak yeniden çalıştırdı: **47 test başarılı, 0 başarısız**, **15,77 saniye**. Bunların **26'sı bağımsız API kabul testi**, **21'i iş kuralı geliştiricisinin yazdığı Python regresyon testidir**. Geliştirici testlerinin yeniden çalıştırılması bağımsız test tasarımı anlamına gelmez.

Bu son birleşik koşumda 40.000 satırlık gerçek xlsx dosyası 1.340.430 bayttı; önizleme 5,445 saniye, commit ve yeniden açma dahil toplam 11,063 saniye gözlendi. Geliştirici tarafından yazılan Python motor hacim testi de bu bağımsız koşumda geçti: 40.000 sevkiyat / 2.000 sipariş için indeks 224 ms, toplam 377 ms.

## Gerçekleşen kabul kontrolleri

| Test grubu | Test verisi / Beklenen sonuç | Gerçekleşen sonuç | Durum |
|---|---|---|---|
| Boş gerçek veri alanı | Yeni DB'de demo kaynak yok; gross/any/tek parça/parça başına saat ayarları | Dört kaynak listesi boş, sürüm 0 ve ayarlar doğru | Başarılı |
| Atomik kayıt ve kalıcılık | Dört kaynak liste ve eşleştirmeleri tek işlemde yaz; istemci ve DB bağlantısını yeniden aç | Revizyon tek artar; dosyadan aynı kayıtlar/sürüm geri okunur | Başarılı |
| Kısmi güncellemede koruma | Yalnız parçayı pasifleştir | Sipariş, sevkiyat ve kalıp kayıtları aynen korunur | Başarılı |
| Eşzamanlılık | Eski revizyonla ikinci yazma | 409; önceden kaydedilen kayıt ve revizyon değişmez | Başarılı |
| Hatalı işlem geri alma | Geçerli diğer kaynaklarla negatif sipariş miktarı gönder | Hata; hiçbir kısmi kaynak kaydı veya sürüm artışı yok | Başarılı |
| Doğal sipariş kimliği | Aynı sipariş no+kalem için iki farklı kayıt kimliği | Çakışma reddedilir; işlem bütünüyle geri alınır | Başarılı |
| Önizleme kaynaklara yazmaz | Dört sayfalı gerçek xlsx önizlemesi | Kaynak listeleri ve revizyon değişmez; yeni kayıt raporu doğru | Başarılı |
| Onaylanan aktarım | Geçerli önizlemeyi commit et | Dört kaynak grubu kalıcı kaydedilir; sürüm artar | Başarılı |
| Baştaki sıfırlar ve geçmiş tarih | 0001 malzeme, 010 kalem, 2026-12-31 sevkiyat | Metin kimlikler ve geçmiş tarih aynen korunur | Başarılı |
| Varsayılan veri koruma | Mevcut parçayı farklı durumla yükle; update_existing gönderme | Mevcut Aktif durumu korunur | Başarılı |
| Açık güncelleme onayı | Aynı parçayı update_existing=true ile yükle | Yalnız hedef parça Pasif olur; diğer kaynaklar korunur | Başarılı |
| Bayat önizleme | Önizleme sonrası API ile kaynak değiştir; eski aktarımı onayla | 409; yeni kaynak korunur | Başarılı |
| Aynı mükerrer satırlar | Dosyada aynı parçayı iki kez yaz | Mükerrer raporlanır; bir kez kaydedilir | Başarılı |
| Çelişkili mükerrer satırlar | Aynı parçanın Aktif ve Pasif sürümleri aynı dosyada | can_commit=false; onay reddedilir; kaynaklara yazılmaz | Başarılı |
| Geçersiz tarihler — üç test | 2027-02-30, 2027-13-01, tarih-yok | Satır 2 / Sevk Tarihi hatası; kısmi kaynak kaydı yok | Başarılı |
| Excel tarih hücresi | Yerel datetime hücresinde 31.12.2026 | ISO 2026-12-31 olarak kabul ve kayıt | Başarılı |
| Başlık ve sayı doğrulama | Eksik Malzeme İsmi başlığı; Miktar alanında metin | Alan/satır bazlı hatalar; revizyon değişmez | Başarılı |
| Bozuk dosya | .xlsx adıyla geçersiz baytlar | 4xx; kaynaklar korunur; sunucu hatası yok | Başarılı |
| Şablon ve dışa/içe aktarım turu | Dört tabloyu export et; ayrı boş DB'ye preview+commit | Şablon başlıkları/sırası ve kaynak değerleri korunur | Başarılı |
| 40.000 satır ve yeniden açma | Gerçek xlsx içinde 40.000 benzersiz sevkiyat | Tamamı önizlenir, aktarılır ve bağlantı yeniden açılınca okunur | Başarılı |
| Geçersiz manuel bağlantı | Sevkiyatı olmayan sipariş kimliğine bağla | 422; revizyon ve kaynaklar değişmez | Başarılı |
| Aktarım mevcut bağlantıyı bozmaz | Bağlı siparişin malzemesini Excel güncellemesiyle farklılaştır | 422; kaynak, revizyon, audit ve aktarım durumu geri alınır | Başarılı |
| ZIP içindeki bozuk XML | Geçerli xlsx arşivinin workbook XML'ini boz | 4xx; sunucu hatası ve kaynak değişimi yok | Başarılı |
| Hesaplanan alan yazımı | Sipariş kaynağına state/net alanları ekle | 422; hesaplanan alan kaynak veri olarak saklanmaz | Başarılı |
| Python hesapları ve sayfalı API | Alternatif kalıp, 120 gelen/5 iade, kesin bağlı sevkiyat | Üretilebilir, 115 net, 5 kalan; /orders sayfasında aynı hesap | Başarılı |
| Orijinal Excel kaynak arşivi | Önizlenen gerçek xlsx baytlarını onay öncesi/sonrası ve yeni DB bağlantısında indir; bilinmeyen batch iste | Üç indirmede birebir bayt eşitliği; doğru xlsx içerik türü; bilinmeyen batch için 404 | Başarılı |
| Tekrar commit | Aynı önizlemeyi iki kez onayla | İkinci işlem 409; kayıt çoğalmaz | Başarılı |
| Silme isteği | Desteklenmeyen delete alanı gönder | 422; hiçbir kaynak silinmez | Başarılı |

Tablodaki bazı satırlar aynı testin birden fazla kabul koşulunu açıklar; güncel bağımsız otomatik API test sayısı 26'dır.

## 40.000 satırlık gerçek Excel ölçümü

Son bağımsız koşumda sentetik kayıtlar içeren gerçek `.xlsx` dosyası **1.340.427 bayt** boyutundaydı. Dosya 2026-12-31 tarihli 40.000 sevkiyat içerir; gerçek kullanıcı verisi değildir. Önizleme toplamı ve yeni kayıt sayısı **40.000**; ekranda gösterilecek önizleme örneği en fazla 20 satırdır. Bu örnek sınırı kaynakların kesilmesi anlamına gelmez.

- Veritabanı hazırlama + HTTP önizleme: **5,487 saniye**.
- Hazırlama, önizleme, commit, tüm kaydı okuma ve yeni DB bağlantısıyla tekrar okuma toplamı: **11,427 saniye**.
- Yeniden açılan DB'de satır sayısı: **40.000**; `SN-39999` kaydı bulundu.

Dosya üretme süresi bu ölçümlere dahil değildir. Bu tek makine/tek koşum gözlemidir; tarayıcı çizimi, ağ yükü, PostgreSQL veya çok kullanıcılı performans garantisi değildir.

## Bulgu, düzeltme ve yeniden test

1. **Sevkiyat Trimli/Trimsiz alanı sayı sayılıyordu.** İlk bağımsız koşum 13 başarılı / 5 başarısız sonuç verdi. Parça trim saatiyle sevkiyatın metin trim durumunun aynı teknik anahtarı kullanması nedeniyle geçerli sevkiyat Excel'i reddediliyordu; 40.000 satırlık dosyada 40.000 hata oluştu. Geliştirme ajanı sayı doğrulamasını varlık türüne göre ayırdı. Gerçek dört sayfalı Excel turu ve 40.000 sevkiyat testi sonraki koşumlarda başarılı oldu.
2. **Excel güncellemesi mevcut kesin bağlantıyı geçersiz kılabiliyordu.** Kod incelemesinde API değişikliklerinde var olan link denetiminin commit yolunda eksik olduğu görüldü. Geliştirme ajanı ortak link doğrulaması ekledi. Bağımsız regresyon testi 422 sonucunu; kaynakların, revizyonun, audit kayıtlarının ve batch durumunun tamamen geri alınmasını doğruladı.
3. **Önizleme sırasında dosya/tür değişimi yarışı.** Bağımsız arayüz kod incelemesinde, bekleyen A dosyası isteğinin B seçildikten sonra eski raporu gösterebileceği bildirildi. Geliştirme ajanı dosya, liste türü ve onay kutularını işlem sırasında devre dışı bıraktı. Kod düzeltmesi bağımsız incelendi; bu yarış için bağımsız tarayıcı otomasyonu henüz çalıştırılmadı.
4. **Kaydetmeden başarı bildirimi.** Tedarikçi–depo eşleştirmesinde Promise sonucu beklenmeden başarı bildirimi gösterilmesi geliştiriciye bildirildi. Kalıcı modda başarı bildiriminin yalnız sunucu yazması ve yeniden yükleme sonrasında gösterilmesi gerekir. Son bağımsız kod incelemesinde callback'in `await setData(...)` sonucunu beklediği, demo bildiriminin yalnız başarılı sonuçta gösterildiği doğrulandı. Kalıcı moddaki `useWorkspace` başarı durumu yalnız commit ve veri yeniden yüklemesi tamamlanınca oluşur.

## Geliştirici tarafından yapılan uçtan uca tarayıcı kontrolü

Geliştirme ajanı `node scripts/fullstack-check.mjs` komutunu ayrı geçici veritabanı ve çalışan API ile gerçek tarayıcı üzerinde çalıştırdığını, çıkış kodunun **0** olduğunu bildirdi. Bu koşum kalite güvence ajanı tarafından bağımsız tekrarlanmadı; geliştirici doğrulaması olarak kaydedilir.

Bildirilen sonuçlar:

- Gerçek `.xlsx` dosyasındaki toplam 34 kaynak kaydı (18 sipariş, 6 parça, 6 kalıp hareketi, 4 sevkiyat) önizlenip kullanıcı onayıyla aktarıldı. Onay öncesinde gerçek kaynak alanı boş kaldı.
- DB'de 18 sipariş ve 4 sevkiyat doğrulandı; depo eşleştirmeleri ve kalıp gereksinimleri kalıcı kaydedildi.
- Arayüz Python sonucunda 115 net / 5 kalan gösterdi. Parça pasifleştirme dört ilgili siparişe yansıdı.
- Sayfa yeniden yüklenince veriler korundu. Sipariş Excel dışa aktarımı başlık dahil 19 satır içerdi.
- Audit kaydı ve eski revizyon için 409 kontrol edildi; demo ve gerçek veri alanlarının ayrılığı doğrulandı.
- İlk geliştirici tarayıcı denemesindeki toplam kayıt beklentisi 28 yerine doğru toplam 34 olacak şekilde testte düzeltildi; bu veri sayım beklentisi hatasıydı.

Geliştirici tarafından bildirilen geçici koşum çıktı dizini: `/tmp/tgy-fullstack-vo4RP4`. Bu yol kalıcı kurulum veya kullanıcı yedeği değildir.

## Kapsam sınırları

- API TestClient kabul testleri ve gerçek SQLite dosyasıyla yeniden bağlantı kalıcılığı bağımsız çalıştırıldı. Ayrı işletim sistemi süreciyle sunucuyu yeniden başlatma ve tarayıcı dosya seçimi bu test grubunda çalıştırılmadı.
- Python kuralları geliştirici testleri ve React testleri başka test gruplarıdır; buradaki 26 bağımsız API testine dahil değildir.
- PostgreSQL, gerçek ERP, kimlik doğrulama, eşzamanlı çok kullanıcılı yük ve gerçek şirket Excel dosyaları test edilmedi.
- Excel turu dört kaynak tabloyu korur; depo/kalıp gereksinimi/link/ayarların tam uygulama yedeği olduğu iddia edilmez.
- Varsayılan API kaynak alanı boş başlar. Gerçek veriyle demo verinin karışmaması ayrıca arayüz iş akışında doğrulanmalıdır.

## Son geliştirici kontrolü

Kaynak arşivi ve son UI düzeltmeleri sonrasında `node scripts/fullstack-check.mjs` yeniden başarılı oldu (çıktılar: `/tmp/tgy-fullstack-Fqs3Gu`). Demo regresyonu `node scripts/browser-check.mjs` de başarılı: sekiz ekran, kaynak detayları, tarih sıralama, USD ve 115/5 hesabı, gerçek XLSX dışa aktarımı, tema, mobil görünüm, 40.000 sentetik satırda arama/sayfalama; JavaScript çalışma hatası yok. Son demo hacim gözlemi açılış 511 ms, arama 693 ms. Bunlar geliştirici koşumudur; bağımsız QA ölçümleri yukarıda ayrı verilmiştir.

`npm run build` ve `npm test` (40 TypeScript iş kuralı testi) başarılı. `.venv/bin/python -m pip check` bağımlılık uyumsuzluğu bulmadı. `scripts/backup.py` çalışan ana SQLite üzerinde yedek oluşturdu; SQLite bütünlük kontrolü başarılı. Asıl çalışma alanına test kayıtları yazılmadı.
