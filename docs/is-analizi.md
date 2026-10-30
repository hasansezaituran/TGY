# İş analizi ve sistem tasarımı

> Bu belge ilk prototipin analizini ve tarihsel değerlendirmesini içerir. Kullanıcı onayından sonraki çalışan Python/SQLite sürümü için [Aşama 2 mimarisi](asama2-mimari.md) ve [Aşama 2 test raporu](asama2-test-raporu.md) geçerlidir.

## Amaç ve aşama sınırı

2027 siparişlerini yalnızca listelemek yerine parça, kalıp ve sevkiyat kayıtlarıyla ilişkilendirerek açıklanabilir operasyonel karar üretmek hedeflenir. Bu belge, verilen sütun tanımlarının analizidir; henüz gerçek Excel dosyaları incelenmemiştir.

İlk aşama React ve TypeScript ile tarayıcıda çalışan, açıkça işaretlenmiş örnek verili prototiptir. Python, FastAPI, gerçek veri tabanı ve gerçek Excel içe aktarma ikinci aşamadır; kullanıcı web prototipini onaylamadan uygulanmaz. Prototipteki saklama kapsamı arayüzde ve kullanım belgesinde açıkça belirtilmelidir. Tarayıcı saklama alanı, kurumsal veri tabanı veya yedekleme olarak sunulmamalıdır.

## Veri ilişkileri

| Kaynak | Hedef | Anahtar / kural | Amaç |
| --- | --- | --- | --- |
| Sipariş Kalemleri | Parça Bilgileri | Malzeme Kodu | Aktif/pasif durumu, MRP ve teknik bilgiler |
| Sipariş Kalemleri | Kalıp Bilgileri | Malzeme Kodu → tanımlı kalıp gereksinimleri → kalıp kimliği | Gerekli kalıpları ve güncel konumlarını bulmak |
| Sipariş Kalemleri | Tedarikçi–Depo Eşleştirmesi | Tedarikçi Numarası → açıkça onaylı depo kimlikleri | Kalıbın sipariş tedarikçisinde olup olmadığını belirlemek |
| Sipariş Kalemleri | Sevkiyat Listesi | Sipariş Numarası + Malzeme Kodu + doğrulanmış tedarikçi kimliği | Aday sipariş kalemlerini bulmak; tek aday veya açık kullanıcı seçimiyle ilişki kurmak |
| Parça Bilgileri | Kalıp Bilgileri | Malzeme Kodu → kalıp gereksinimleri | Parçanın tüm ilgili kalıplarını göstermek |
| Parça Bilgileri | Sevkiyat Listesi | Malzeme Kodu | Sevkiyat ve seri geçmişini göstermek |

Sipariş kaleminin kimliği `Sipariş Numarası + Sipariş Kalem` birleşimidir. Kodlar metin olarak korunur; baştaki sıfırlar atılmaz. Eski Malzeme Kodu ancak onaylı, izlenebilir bir kod eşleştirmesiyle kullanılır. Benzer firma/depo adları otomatik kesin eşleşme oluşturmaz.

## Kritik kararlar ve güvenli davranış

1. **İadeler — yanıtlandı:** Gelen Miktar brüttür; net teslimat için İade Miktar bir kez düşülür. Kullanıcı ayarı yeniden tanımsız duruma getirirse iadeli kayıtta kesin net/kalan/oran hesaplanmaz.
2. **Çoklu kalıplar — yanıtlandı:** Kalıplar alternatiftir; doğru tedarikçide bir uygun kalıp yeterlidir. Diğer alternatifin yanlış yerde veya belirsiz olması bu uygunluğu bozmaz. Hiçbir alternatifin uygunluğu doğrulanamıyorsa eksik konum verisi `KONTROL GEREKLİ` üretir; tüm alternatiflerin yanlış yerde olduğu doğrulanırsa `ÜRETİLEMEZ` olur. Kalıp hareketi bulunamaması, fiziksel kalıbın yok olduğunu kanıtlamaz.
3. **Depo eşleştirmesi:** Hangi depo kimlikleri hangi tedarikçi numarasına bağlı? Öneri: kullanıcı tarafından yönetilen açık eşleştirme; isim benzerliği yalnızca öneri olabilir.
4. **Kalıp geçmişi:** ATA/ASY kodları tekil kimliği nasıl oluşturuyor? Başlangıç konumu ve aynı gün hareket sırası var mı? Tarih ve sıralama yeterli değilse son konum belirsizdir. Bir önceki hedef ile sonraki kaynağın çelişmesi uyarı üretmelidir.
5. **Sevkiyat ölçüsü — yanıtlandı:** Her seri satırı bir parçadır. Kesin bağlanan satır sayısı sevk adedi olarak kullanılabilir; sevk işlemi teslim alma işlemi değildir.
6. **Adam saati — yanıtlandı:** Değerler parça başınadır. Bu birim gösterilir; ayrıntılı kapasite planlaması bu prototipin kapsamı dışındadır.
7. **Para birimi — yanıtlandı:** USD kullanılacaktır. Kaynak sütunlara ek `Para Birimi` alanı önerilir. Farklı veya bilinmeyen para birimleri tek finansal toplamda birleştirilmez.
8. **Hacim ve geçmiş — yanıtlandı:** Yılda yaklaşık 40.000 sevkiyat satırı ve 2026'dan geçmiş veriler vardır. Prototip indeksleme ve sayfalama kullanır. Gerçek dosya henüz alınmadığı için 2026 geçmiş verisi yüklenmiş değildir; ikinci aşamada geçmiş korunmalı ve indeksli sorgularla sunucu tarafı filtreleme/sayfalama değerlendirilmelidir.

## Açıklanabilir karar kuralları

- Parça pasifse `ÜRETİLEMEZ`.
- Doğrulanan alternatif kalıp kuralında tüm alternatiflerin yanlış depoda olduğu biliniyorsa `ÜRETİLEMEZ`. Bir alternatif doğru depodaysa diğerinin yanlış yerde bulunması tek başına engel değildir. Ayar açıkça “tümü gerekli” olarak değiştirilirse gerekli kalıplardan birinin yanlış yerde olması engeldir.
- Parça aktifse ve en az bir tanımlı alternatif kalıp sipariş tedarikçisindeyse `ÜRETİLEBİLİR`.
- Eksik parça, belirsiz kalıp gereksinimi, yetersiz hareket geçmişi veya eksik depo eşleştirmesi kesin olumsuzluk yokken `KONTROL GEREKLİ` üretir.
- Birden fazla neden birlikte gösterilir. Onay bekleyen bir sipariş fiziksel olarak üretilebilir olabilir; bu iki durum ayrı alanlardır.
- Kalıp konumu, kalıp kimliğine göre gruplanmış hareketlerin tarih/sıra düzeniyle hesaplanır. Geçmiş tarihli yeni hareket eklenmesi tüm zinciri yeniden değerlendirir.
- Aynı siparişte aynı malzeme ve tedarikçiyle birden fazla kalem bulunursa sevkiyat rastgele bir kaleme atanmaz. Adaylar ve kullanıcı seçimi ayrı tutulur.
- Mükerrer seri, eksik irsaliye, siparişsiz sevkiyat, pasif parçanın sevkiyatı ve belirsiz eşleşme ayrı uyarılardır. Birden fazla sevkiyat tek başına hata değildir.

## Teknik mimari

İlk aşamada tek bir örnek veri durumu kaynak kayıtları tutar. Saf hesaplama fonksiyonları parça durumu, kalıp konumu, üretilebilirlik, teslimat ve sevkiyat eşleşmelerini türetir. Genel Bakış ile dört operasyon sayfası aynı hesaplama katmanını kullanır. Örneğin parçanın durumu değiştiğinde sipariş detayı ve KPI'lar aynı veriden yeniden hesaplanır; hesaplanan durum ayrıca elle kaydedilmez.

İkinci aşamada React arayüzü REST API üzerinden FastAPI'ye bağlanabilir. İş kuralları servis katmanında, veri erişimi ayrı katmanda tutulur. SQLite ile başlanan ilişkisel yapı PostgreSQL'e geçişi desteklemelidir. İçe aktarma önce geçici doğrulama/önizleme alanına alınır, farklar ve hatalar gösterilir; açık onaydan sonra tek işlem içinde uygulanır. Ham kaynak satırları, aktarım partisi ve yapılan kullanıcı seçimi izlenebilir tutulur.

| Model | Temel ilişki / bütünlük |
| --- | --- |
| `orders` | Sipariş numarası; tedarikçi ilişkisi |
| `order_items` | Sipariş + kalem tekilliği; malzeme ilişkisi; kaynak miktarlar ve fiyat |
| `materials` | Malzeme kodu tekilliği; üretim durumu; saat ve saat birimi |
| `material_code_aliases` | Eski/yeni kod, onay durumu ve geçerlilik; çelişkili eşleşme engeli |
| `suppliers`, `warehouses` | Kararlı kimlikler; adlar gösterim içindir |
| `supplier_warehouse_mappings` | Tedarikçi–depo ilişkisi, geçerlilik ve onay bilgisi |
| `molds` | Kalıp kimliği, ATA/ASY kodları ve varsa başlangıç konumu |
| `material_mold_requirements` | Malzeme–kalıp ilişkisi; gerekli/alternatif grup kuralı |
| `mold_movements` | Kalıp, kaynak, hedef, tarih ve varsa sıra; tarihsel kayıt |
| `shipments` | Sipariş numarası, malzeme, tedarikçi, seri/irsaliye ve ölçü türü |
| `shipment_order_item_links` | Kesinleşmiş bağlantı, seçim yöntemi, kullanıcı ve zaman |
| `import_batches` | Dosya/sayfa, doğrulama sonucu, onay ve uygulama geçmişi |

Kimlik ve kod alanları metin, miktarlar hassas ondalık, fiyatlar ondalık ve para birimiyle birlikte tutulmalıdır. Tarihler açık biçimde doğrulanmalı; geçersiz değerler sessizce dönüştürülmemelidir. Sipariş+kalem, malzeme kodu, kalıp+tarih+sıra ve sevkiyat aday anahtarları indekslenmelidir. Kaynak sütun isimleri ve sırası korunmalı; hesaplanan alanlar ayrıca belirtilmelidir.

## İlk prototipin kabul kriterleri

1. Genel Bakış, Sipariş Kalemleri, Kalıp Bilgileri, Parça Bilgileri ve Sevkiyat Listesi erişilebilir olmalıdır; tüm örnekler demo olarak işaretlenmelidir.
2. Arama/filtre, sıralama, sayfalama, sütun görünürlüğü ve satır detayı gerçekten çalışmalıdır. Henüz yapılmayan işlevler tamamlanmış gibi sunulmamalıdır.
3. Pasif parça, tüm alternatifleri yanlış depoda bulunan kalıp grubu, uygun bir alternatifi olan aktif parça, bilinmeyen konum, eksik parça ve belirsiz sevkiyat örnekleri ayrı sonuç üretmelidir.
4. Parça durumunun ve kalıp hareketinin değiştirilmesi ilişkili siparişleri, nedenleri ve dashboard göstergelerini yeniden hesaplamalıdır.
5. Tarihler GG.AA.YYYY, sayılar Türkçe biçimde gösterilmelidir. Renk yanında metin veya simge bulunmalıdır.
6. İade kuralı bilinmiyorsa çift düşüm yapılmamalı; farklı para birimleri toplanmamalıdır.
7. Sevkiyat sipariş detayında görünmeli; aday sayısı birden fazlaysa kullanıcı seçene kadar kesin bağlantı oluşmamalıdır.
8. Test raporu çalıştırılmış kontrolleri, başarısızlıkları ve test edilmemiş alanları ayırmalıdır. Prototipin mevcut oturum/tarayıcı saklama sınırı açıklanmalıdır.

## Operasyonel değerlendirme çerçevesi

Prototip satın alma ekibine açık siparişle fiziksel üretim engelini aynı görünümde değerlendirme olanağı vermelidir. En önemli fayda, sorun nedenini ve ilgili kaynak kaydı birlikte göstermektir. En önemli riskler yanlış depo eşleştirmesi, eski kodların kontrolsüz birleştirilmesi, belirsiz sevkiyatın rastgele atanması ve iadelerin çift düşülmesidir.

Gerçek kullanım öncesi örnek kaynak dosyalar, kalıp kimlikleri ve gerçek depo eşleştirmeleri doğrulanmalıdır. İade, alternatif kalıp, sevkiyat ölçüsü, saat birimi, para birimi ve yaklaşık hacim kullanıcı tarafından yanıtlanmıştır. İlk prototip operasyonel kararların nasıl sunulduğunu değerlendirmek içindir; gerçek ERP kaydı veya doğrulanmış üretim izni yerine geçmez. İşlevsel kontrollerin sonuçları bağımsız test raporunda izlenir.

## Aşama 1 operasyonel incelemesi

Bu değerlendirme `src/App.tsx`, `src/domain.ts` ve `src/data.ts` üzerinde bağımsız iş analisti kod incelemesine dayanır. Tarayıcı kabul testi gerçekleştirdiğim anlamına gelmez; yürütülen kontrollerin sonuçları kalite mühendisinin test raporunda ayrıca belirtilir.

### A. Uygulanan özellikler

- Genel Bakış ile dört operasyon sayfası aynı örnek veri durumunu kullanıyor. Demo 18 sipariş kalemi, 6 parça, 6 kalıp hareketi ve 4 sevkiyat kaydı içeriyor.
- Arayüzde üretilebilirlik, nedenleri, kaynak gelen/iade miktarları, kalan teslimat ve ilişkili sevkiyatlar ayrı gösteriliyor. Parça durumunu değiştirme, kalıp hareketi ekleme ve depo eşleştirmesini uygulama akışları ilişkili hesaplamaları yeniden çalıştırıyor.
- Tablolarda metin arama, sütun görünürlüğü, sekiz satırlık sayfalama, Shift ile çoklu sıralama, detay paneli ve `.xlsx` dışa aktarma kodlanmış. Sipariş tablosunda ayrıca tedarikçi, proje, sipariş durumu, teslimat ve üretilebilirlik filtreleri bulunuyor.
- Sevkiyat detayında yalnızca uygun aday sipariş kalemleri seçilebiliyor. Birden fazla aday kendiliğinden kesin bağlantıya dönüşmüyor; eşleştirme teslim alınan miktarı değiştirmiyor.
- Başlangıç ayarları kullanıcı yanıtlarına göre brüt gelen miktar, alternatif kalıp, seri başına bir adet ve parça başına saat olarak düzenlenmiştir. Sipariş para birimi USD'dir. Tanımsız kural seçeneği güvenli davranışı incelemek için ayarlarda korunur; farklı para birimleri dashboard'da ayrı tutulur.
- Ayarlar ekranında 40.000 sentetik sevkiyat ekleme akışı vardır. Bu kayıtlar 2027 tarihli demo verisidir; gerçek 2026 geçmişi değildir. Ana tabloda kayıtların tamamı sayfalanır; detay panelindeki ilişkili listeler ilk 50 kayıtla sınırlanır.
- Açık/koyu tema mevcut. Değişikliklerin yalnızca açık sayfada tutulduğu ve yenilemeyle sıfırlandığı arayüzde açıkça belirtiliyor.

Gerçek Excel içe aktarma, kalıcı veri tabanı, çok kullanıcılı kullanım, denetim izi, gerçek ERP bağlantısı ve Python backend bu aşamada uygulanmadı. Veri Aktarımı sayfası gelecek doğrulama akışını açıklıyor; yapılmayan dosya yüklemeyi çalışıyor gibi göstermiyor.

### B. Operasyonel faydalar

Satın alma ekibi sipariş onayını fiziksel üretim uygunluğundan ayırabiliyor. Üretim engelinin pasif parçadan, yanlış kalıp konumundan veya eksik bilgiden kaynaklandığını inceleyebiliyor. Tedarikçi–depo eşleştirmesi açık yönetildiği için isim benzerliğine dayalı hatalı karar riski azalıyor. Sevkiyatın teslim alım sayılmaması, ERP mutabakatındaki önemli bir ayrımı koruyor. Örnek veri üzerinde parça veya kalıp değiştirerek siparişlere etkisini gözlemleme olanağı, gerçek veri aktarımından önce iş kuralı değerlendirmesini kolaylaştırıyor.

### C. Tespit edilen riskler ve sınırlar

- **Kalıp kimliği varsayımı:** Prototip kalıbı `Malzeme Kodu + Kalıp ATA Kodu` ile tanıyor. ASY gösteriliyor, ancak konum anahtarına katılmıyor. Gerçekte aynı ATA'nın farklı ASY'leri veya farklı malzemelerde ortak fiziksel kalıp bulunuyorsa bu model onaylanmadan gerçek veride kullanılmamalıdır.
- **Çoklu kalıp kuralı:** Doğrulanan “bir uygun alternatif yeterli” seçimi prototipte bütün malzemelere uygulanıyor. Gerçek veride farklı bir gereksinim ortaya çıkarsa malzeme bazında alternatif gruplar ayrıca yönetilmelidir.
- **Başlangıç konumu ve sıra:** Hareketi olmayan kalıpta başlangıç konumu girişi uygulanmadı; sonuç belirsiz kalıyor. Aynı gün hareketleri, saat veya sıra bilgisi olmadığı için belirsiz sayılıyor. Bu ihtiyatlı davranış gerçek sıra alanıyla geliştirilebilir.
- **Demo eşleştirmeleri:** Tedarikçi, depo ve kalıp gereksinimleri örnek senaryonun tanımlarıdır; şirket verileri için onaylı eşleştirmeler değildir. Eski malzeme kodları otomatik bağlanmıyor.
- **Gösterge kapsamı:** Sipariş göstergeleri seçili filtreleri kullanırken toplam sevkiyat ve sevkiyat uyarıları tüm demo kayıtlarını kullanıyor. Arayüzde bu kapsam ayrımı korunmalı; gerçek raporlarda tarih ve tedarikçi kapsamları açık seçilmelidir.
- **Seri ve mutabakat:** Mükerrer seri kontrolü genel seri metnine dayanıyor. Seri tekilliğinin malzeme, tedarikçi veya tüm sistem bazında mı olduğu ayrıca doğrulanmalı. Kullanıcı her satırın bir parça olduğunu doğruladığı için sevk/teslim karşılaştırması başlangıçta etkindir; taşıma halindeki parçalar doğrudan veri hatası sayılmamalı.
- **Performans ve saklama:** Sentetik 40.000 kayıt gerçek kaynak dosyasındaki tüm veri şekillerini temsil etmez. Detay panelinde ilk 50 sınırı olduğundan tam liste için ana sayfalı tablo kullanılmalıdır. Kalıcı filtre tercihi, sunucu tarafı sayfalama ve kalıcı kayıt bulunmuyor. Sayfa yenilenmeden önce yapılan örnek değişiklikler gerekli görülürse dışa aktarılmalıdır.

### D. İyileştirme önerileri

Önce gerçek listelerden anonimleştirilmiş küçük bir örnekle kimlik, tarih, sayı ve depo sözlüğü doğrulanmalı. Ardından alternatif kalıp grupları, başlangıç konumu, sıra bilgisi ve onaylı kod eşleştirmesi tasarlanmalı. İkinci aşamada içe aktarma önizlemesi yeni/güncellenecek/çelişkili kayıtları ayrı göstermeli; uygulama kullanıcı onayı ve işlem günlüğüyle gerçekleşmelidir. Bilinen yıllık 40.000 sevkiyat ve yıllar arası birikim dikkate alınarak arayüz sanallaştırması veya sunucu tarafı sayfalama gerçek veride ölçümle seçilmelidir.

### E. Kullanıcıdan beklenen kararlar

Prototip onayında özellikle üç akış değerlendirilmelidir: pasif parça değişikliğinin siparişe etkisi, kalıp transferinden sonra konum/üretilebilirlik değişimi ve belirsiz sevkiyatın doğru sipariş kalemine seçilmesi. ATA/ASY'nin tekil kimlikteki rolü ve gerçek tedarikçi–depo eşleştirmeleri ayrıca doğrulanmalıdır. Python aşamasına geçiş ayrıca açık kullanıcı onayı gerektirir.

## Kullanıcı yanıtlarıyla doğrulanan kurallar ve hacim

Bu belgenin karar ve değerlendirme bölümleri kullanıcı yanıtlarına göre güncellenmiştir. Doğrulanan kuralların özeti:

| Konu | Doğrulanan kural | Hesaplama etkisi |
| --- | --- | --- |
| İade | Gelen Miktar brüttür (`gross`) | Net teslim = Gelen Miktar − İade Miktar; örneğin 120 gelen ve 5 iade → net 115 |
| Çoklu kalıp | Kalıplar alternatiftir (`any`) | Doğru tedarikçide bir uygun alternatif kalıp yeterlidir |
| Sevkiyat ölçüsü | Her satır bir parçadır (`shipmentUnits: true`) | Kesin bağlanan satırlar sevk adedi olarak karşılaştırılabilir; teslim alım otomatik güncellenmez |
| Adam saati | Parça başınadır (`piece`) | Saatin birimi artık tanımlıdır; gerçek kapasite planlaması ayrı kapsamdır |
| Para birimi | USD | Örnek sipariş tutarları USD ile gösterilir; farklı para birimleri gelirse ayrı tutulur |
| Tarih kapsamı | 2026 geçmiş verileri de vardır | Eski kayıtlar yalnızca yılından dolayı atılmaz; gerçek içe aktarımda geçmiş korunmalıdır |
| Hacim | Yılda yaklaşık 40.000 sevkiyat satırı | Her hesaplamada tüm sevkiyatları tekrar tekrar tarayan yaklaşım uygun değildir |

`src/indexed.ts` içindeki `createEngine(data)`, aynı veri anlık görüntüsünde sipariş adaylarını birleşik anahtar, parçaları malzeme kodu, seri tekrarlarını seri numarası ve hareketleri kalıp+malzeme anahtarıyla indeksler. Kesin bağlanan sevkiyatlar sipariş kimliğinde, belirsizler aday grubunda tutulur. İndeks kurulumu kayıt sayısıyla doğrusal büyür; belirsiz kayıtlar her aday sipariş için çoğaltılmaz. Kalıp tarih sıralaması ilgili grup ilk istendiğinde bir kez yapılır ve sonuç önbelleğe alınır. Hesaplamalar mevcut `domain.ts` kurallarını kullanır; hızlandırma karar mantığını değiştirmez. Veri, eşleştirme veya ayar değiştiğinde yeni motor oluşturulmalıdır.

40.000 sentetik sevkiyatla yapılan indeks testi algoritma maliyetini gözlemlemeye yarar. Ayarlar ekranından aynı hacimde 2027 demo kaydı eklenip ana tabloda sayfalanabilir; ayrıntı listeleri ilk 50 kaydı gösterir. Algoritma testi tek başına gerçek Excel doğrulaması, tam tarayıcı etkileşim testi veya yıllar boyu biriken verinin ölçümü anlamına gelmez. Gerçek 2026 dosyaları henüz yüklenmemiştir. İkinci aşama için indeksli veritabanı sorguları ve sunucu tarafı sayfalama önerisi geçerlidir.
