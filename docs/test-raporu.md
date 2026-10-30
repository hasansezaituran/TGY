# Aşama 1 — Bağımsız test raporu

## Güncel sonuç — Kullanıcı kararları ve 40.000 satır kontrolü

Kullanıcının iş kurallarını netleştirmesinden sonra bağımsız kalite güvence ajanı `/workspace/TGY` dizininde `npm test` komutunu yeniden çalıştırdı. **3 test dosyası, 40 test başarılı; 0 başarısız.** Koşum zamanı: 30.10.2026, 09.51 (İstanbul). Önceki 30 test korunmuş; 5 kullanıcı kararı kabul testi ve 5 indeks/hacim testi eklenmiştir.

### Doğrulanan kullanıcı kararları

| Kontrol | Beklenen ve doğrulanan sonuç |
|---|---|
| ERP iade kuralı | Gelen miktar brüttür; 120 gelen − 5 iade = 115 net; 120 siparişte kalan 5. |
| Çoklu kalıp | Kalıplar alternatiftir; Ege Metal siparişinde uygun K-006 varken K-007 konumu eksik olsa da fiziksel üretilebilirlik olumlu. |
| Sevkiyat birimi | Her satır bir parçadır; bir sevkiyat kaydı oluşturulması teslim alınan 115 net miktarı değiştirmez. Miktar farkı ayrıca uyarılır. |
| Adam saati | Örnek veri ayarı parça başına saattir. Gerçek kapasite planlaması doğrulanmış sayılmaz. |
| Para birimi | Tüm örnek siparişlerde USD açıkça tanımlıdır. |

### İndeks eşdeğerliği

`src/performance.test.ts`, `createEngine` indeksli motorunun adaylar, kesin eşleştirme, sevkiyat uyarıları, kalıp konumu ve sipariş değerlendirme sonuçlarını indekssiz referans işlemlerle karşılaştırır. Demo verisi, dokuz iade/kalıp kural birleşimi ve eksik/çelişkili veriler kontrol edildi. Yeni veri nesnesine yeni indeks kurulduğunda önceki parça/konum/sevkiyat sonuçlarının sızmadığı da doğrulandı. Sonuçlar eşdeğerdir.

### Sentetik hacim kontrolü

2026 tarihli **40.000 sentetik sevkiyat**, **2.000 sipariş kalemi**, 100 malzeme ve 100 kalıp hareketi oluşturuldu. Tüm sevkiyatlar ve siparişler gezilerek şu sonuçlar doğrulandı:

- 40.000 sevkiyatın tamamı tek doğru adaya bağlandı.
- Siparişlere bağlı sevkiyat toplamı 40.000 oldu; kayıt kaybı/çoğalması gözlenmedi.
- 2.000 siparişin tamamında üretilebilirlik, 20 net teslim ve 0 kalan doğrulandı.
- Benzersiz seri ve geçerli belge içeren bu sentetik veride sevkiyat veri uyarısı sayısı 0 oldu.
- Bu makinedeki bağımsız koşumda indeks kurulumu **68 ms**, indeks kurulumuyla tüm değerlendirmelerin toplamı **157 ms** sürdü.

Bu süreler tek bir Node/Vitest koşumunun gözlemidir; genel performans garantisi değildir. Gerçek Excel dosyasını okuma, tarayıcı çizimi, ağ/ERP aktarımı, veri tabanı ve çok kullanıcılı yük bu ölçüme dahil değildir. Kullanıcının bildirdiği 40.000 satır hacmi sentetik veriyle temsil edilmiştir; gerçek 2026 verisi sisteme yüklenmemiştir.

### Geliştirici tarayıcı hacim kontrolü ve düzeltme döngüsü

Bu kontrol geliştirme ajanının gerçek Chromium üzerinde çalıştırdığı `scripts/browser-check.mjs` sonucudur; bağımsız kalite güvence tarayıcı koşumu değildir.

İlk 40.000 satırlık arayüz denemesi başarısız oldu: detay panellerini ilk 50 kayıtla sınırlandıran değişiklik ana sevkiyat tablosuna da uygulanmıştı. Alt bilgide 40.000 kayıt bekleyen kontrol bu kesilmeyi yakaladı. Geliştirme ajanı ana `shipmentRows` dizisini tüm kayıtlardan oluşturacak şekilde düzeltti; yalnız detay listelerindeki ilk 50 sınırını ve açıklamasını korudu. Bağımsız kod incelemesi bu ayrımı doğruladı.

Düzeltme sonrasında geliştiricinin bildirdiği Chromium koşumunda:

- Ana tablo alt bilgisinde 40.000 kayıt doğrulandı.
- DOM üzerinde yalnız 8 tablo satırı çizildiği kontrol edildi.
- İlk 50 kaydın dışındaki `HACIM-39999` serisi arandı ve tek doğru satır bulundu.
- İlk başarılı hacim koşumunda sentetik kayıt ekleme ve sevkiyat tablosunu açma toplamı **491 ms**, tekil seri araması **771 ms** olarak gözlendi. Tarih sıralama düzeltmesinden sonraki son tam Chromium koşumunda bu süreler sırasıyla **694 ms** ve **818 ms** oldu; DOM üzerinde 8 satır kontrolü yine geçti.

Bu ölçüm, uygulamanın mevcut örnek siparişlerine bağlı 2027 tarihli sentetik sevkiyatları kullanır. Yukarıdaki 2.000 siparişli, 2026 tarihli bağımsız motor testinden farklı bir senaryodur. Gerçek 2026 verisi içe aktarılmamıştır.

Sonraki bağımsız kod incelemesinde, `GG.AA.YYYY` gösterimindeki tarihlerin gün öncelikli metin sıralamasına girdiği bulundu. Aynı karşılaştırıcıyla `08.02.2027` tarihinin `22.01.2027` önüne geçtiği doğrulandı. Geliştirme ajanı `Sevk Tarihi` sıralama değerini yıl–ay–gün düzenine çevirdi. Kod düzeltmesi bağımsız incelendi; tarih başlığına tıklamayla ilk satırın 22.01.2027 olması için geliştirici Chromium regresyon kontrolü eklendi. Son geliştirici Chromium koşumunda tarih başlığına tıklama sonrasında ilk satırın **22.01.2027** olması doğrulandı. Aynı tam koşum, kullanıcı ayarlarının başlangıç değerlerini, **115 net / 5 kalan** hesabını ve USD dolar gösterimini doğruladı; JavaScript hatası gözlenmedi ve işlem çıkış kodu 0 oldu. Geliştirme ajanı son `npm run build` komutunun da çıkış kodu 0 ile tamamlandığını bildirdi. Bu tarayıcı ve derleme sonuçları geliştirici doğrulamasıdır; bağımsız QA koşumuyla karıştırılmamalıdır.

Aşağıdaki bölüm önceki prototipin tarihsel 30 testlik raporunu korur. Güncel sonuç bu bölümdeki 40/40 sonucudur.

## Önceki prototip sonucu — Tarihsel kayıt

Kalite güvence ajanı, geliştirme ajanının yazdığı `src/domain.ts` iş kurallarını kullanıcı gereksinimlerinden bağımsız test verileri oluşturarak değerlendirdi. Testler `src/domain.test.ts` içinde yer alır. Üretim kodu kalite güvence ajanı tarafından değiştirilmedi.

**Çalıştırılan komut:** `/workspace/TGY` dizininde `npm test`.

**Sonuç:** 1 test dosyası, **30 test başarılı, 0 başarısız**. Test koşucusu Vitest 3.2.7. Bu raporun yürütümü 30.10.2026 tarihinde yapılmıştır. Tarayıcı işlevleri ve Excel dosyası indirme bu bağımsız iş kuralı test grubunun kapsamında değildir; bunların doğrulaması ayrıca raporlanmalıdır.

| No | Test adı | Test verisi | Beklenen sonuç | Gerçekleşen sonuç | Durum | Hata açıklaması / Düzeltme durumu |
|---|---|---|---|---|---|---|
| 1 | Pasif parça | Aktif kalıp konumuyla Pasif M1 | Üretilemez ve pasif parça nedeni | Üretilemez; neden listede | Başarılı | Hata yok |
| 2 | Yanlış depo | Tedarikçi A; K1 kalıbı DB'de | Üretilemez / Kalıp uygun değil | Her iki sonuç doğrulandı | Başarılı | Hata yok |
| 3 | Aktif parça ve uygun kalıp | M1 Aktif, K1 DA'da, A→DA eşleştirmesi | Üretilebilir | Üretilebilir | Başarılı | Hata yok |
| 4 | Eksik kalıp konumu | M1 için hiç hareket yok | Kontrol gerekli / Belirlenemedi | İki sonuç da doğrulandı | Başarılı | Hata yok |
| 5 | Kalıp transferi | A ve B siparişleri; DA→DB transferi | A üretilemez, B üretilebilir | İki sipariş de yeniden hesaplandı | Başarılı | Hata yok |
| 6 | Eksik parça | M1 siparişi var; parça kaydı yok | Kontrol gerekli / Parça kaydı eksik | Doğrulandı; otomatik üretilemez sayılmadı | Başarılı | Hata yok |
| 7 | Mükerrer sevkiyat | SN1 seri numarasıyla iki kayıt | İki kayıtta mükerrer seri uyarısı | İki kayıtta uyarı var | Başarılı | Hata yok |
| 8 | Sipariş–sevkiyat bağlantısı | Sipariş/malzeme/tedarikçi için tek aday | Sipariş detay verisine sevkiyat eklenir; teslimat değişmez | 1 sevkiyat; net teslim 40 olarak korundu | Başarılı | Hata yok; yalnız iş kuralı sonucu doğrulandı |
| 9 | Belirsiz kalem | Aynı anahtarlara sahip 10 ve 20 kalemleri | Otomatik bağlantı yok; geçerli kullanıcı seçimi kabul edilir | Belirsiz uyarısı, geçerli seçim ve geçersiz seçim reddi doğrulandı | Başarılı | Hata yok |
| 10 | Excel güncellemesi | Gerçek Excel içe aktarma | Aktarım onayından sonra ilgili siparişler değişmeli | Excel içe aktarma Aşama 2'ye bırakılmıştır | Test edilmedi | Kapsam dışı; başarılı diye sunulmadı |
| 10a | Parça verisi değişimi | M1 durumunu Aktif→Pasif değiştirme | Üretilebilir→Üretilemez | Yeni veriyle karar yeniden hesaplandı | Başarılı | Excel aktarımının yerine geçtiği iddia edilmez |
| 11 | İade miktarı | Miktar 100, gelen 40, iade 5 | Bilinmeyende hesap yok; net kuralda 40/60; brütte 35/65 | Net, kalan ve yüzde değerleri üç durumda doğrulandı | Başarılı | Çift düşüm yapılmadı |
| 12 | Geçmiş tarihli hareket | 10.01 MERKEZ→DA; 20.02 DA→DB; sonradan 01.01 X→MERKEZ | Son konum DB kalır | DB; fiziksel satır sırasından bağımsız | Başarılı | Hata yok |

## Ek 18 kontrol

Aşağıdaki kontroller de başarılıdır:

1. Aynı tarihli iki hareket kesin konum üretmez.
2. Kaynak–hedef zinciri kopuksa kesin konum üretilmez.
3. Konum hesabı kaynak hareket dizisinin sırasını değiştirmez.
4. Çoklu kalıp kullanım kuralı bilinmiyorsa kontrol gerekir.
5. Alternatif kalıplarda bir uygun kalıp yeterlidir.
6. Tüm kalıplar gerekliyken bilinmeyen konum kontrol gerektirir.
7. Tüm kalıplar gerekliyken bir yanlış konum üretimi engeller.
8. Pasif parça ve yanlış kalıp nedenleri birlikte korunur.
9. Onay bekleyen sipariş fiziksel olarak üretilebilir kalabilir; onay ayrıca uyarılır.
10. Tedarikçi–depo eşleştirmesi yoksa isim benzerliğinden karar üretilmez.
11. Eski malzeme kodu otomatik eşdeğer kabul edilmez.
12. Farklı tedarikçi sevkiyata aday sayılmaz.
13. Eksik irsaliye ve pasif parça uyarıları birlikte görünür.
14. Sevkiyat birim kuralı doğrulanmadan satır sayısından miktar farkı hesaplanmaz.
15. Sıfır sipariş miktarında yüzde hesaplanmaz.
16. `tarih-yok` geçersiz tarihi kesin konum üretmez.
17. `2027-02-30` geçersiz takvim günü kesin konum üretmez.
18. `2027-13-01` geçersiz ay kesin konum üretmez.

## Bulgu ve düzeltme döngüsü

İlk bağımsız incelemede geçersiz tarihlerin kalıp konumu hesabında kabul edildiği bulundu. Gerçek `domain.ts` modülü Node üzerinden çalıştırıldığında `tarih-yok`, `2027-02-30`, `2027-13-01` girdilerinin üçü de beklenen `null` yerine `DA` konumunu verdi. Geliştirme ajanına bildirildi; geliştirme ajanı ISO biçimi ve takvim geçerliliği kontrolünü ekledi. Son Vitest koşumunda üç regresyon testi ve önceki 27 test birlikte başarılı oldu.

Arayüz kodu ayrıca bağımsız olarak incelendi. Sıfır filtre sonucunda sipariş tablosu kaynak sütunlarının örnek satırdan türetilerek kaybolması ve kalıp uyarısı bağlantısının daha geniş Üretilemez filtresine gitmesi geliştirme ajanına bildirildi. Geliştirme ajanı, sütunları sabit kaynak şemasından türeterek ilk bulguyu; ayrı `issueFilter` ile yalnız kalıp uygunsuzluğu olan kayıtları seçerek ikinci bulguyu düzeltti. Bu arayüz düzeltmelerinin tarayıcı doğrulaması geliştirme ajanı tarafından yapıldı; bağımsız QA tarayıcı doğrulaması olarak sunulmaz.

## Geliştirici tarafından yapılan tarayıcı kontrolü

Bu bölüm geliştirme ajanının ilettiği sonuçları kaydeder. `scripts/browser-check.mjs` gerçek Chromium tarayıcısında geliştirme ajanı tarafından çalıştırılmıştır; kalite güvence ajanı bu tarayıcı koşumunu bağımsız olarak tekrarlamamıştır.

Geliştirme ajanının bildirdiği başarılı kontroller:

- Boş filtre sonucunda sipariş tablosunda 26 başlık korunuyor.
- Aramayla bulunan 4 satır Excel dosyasına aktarılıyor; indirilen dosya yeniden okunarak doğrulanıyor.
- Parçayı Pasif yapınca ilgili 4 siparişin durumu güncelleniyor.
- Kalıp transferi güncel konuma yansıyor.
- Belirsiz sevkiyat eşleştirmesi kullanıcı seçimiyle yapılabiliyor.
- Sekiz sayfaya erişim, tema değiştirme ve sayfa yenileme davranışı kontrol edildi.
- Mobil görünümde sayfa taşması ve JavaScript hatası gözlenmedi.

Ayrıca geliştirme ajanı son değişikliklerden sonra `npm test` komutunun yeniden 30/30 başarılı olduğunu bildirdi. Bağımsız QA iş kuralı koşumunun sonucu üst bölümde ayrı verilmiştir.

## Doğrulama sınırları

- Gerçek ERP verisi, Python/FastAPI, veri tabanı kalıcılığı, gerçek Excel içe aktarma, kimlik doğrulama ve çok kullanıcılı çalışma test edilmedi.
- İş kuralları birim testleri, arayüzde ilgili detayın tıklanabildiğini tek başına kanıtlamaz.
- Bu önceki rapor sırasında on binlerce satır testi yapılmamıştı. Sonraki bağımsız 40.000 sentetik sevkiyat kontrolü üst bölümde kayıtlıdır; gerçek veri ve uçtan uca tarayıcı yük testi halen yapılmamıştır.
- Kalıpların birlikte/alternatif kullanımı prototipte genel ayardır. Kullanıcı daha sonra alternatif kullanımını doğrulamıştır; malzeme bazında ayrı kural yönetimi henüz doğrulanmadı.
