# Aşama 2: Kalıcı uygulamanın mimarisi ve sınırları

## Çalışan bileşenler

React ve TypeScript arayüzü FastAPI REST API'ye bağlanır. Python tarafındaki `backend/rules.py`, kaynak kayıtları üzerinde indeksli ve açıklanabilir üretilebilirlik, teslimat ve sevkiyat kontrollerini hesaplar. Gerçek çalışma alanı boş veritabanıyla başlar; demo kayıtları otomatik eklenmez. Varsayılan kurallar brüt gelen miktar, alternatif kalıpta bir uygunun yeterliliği, sevkiyat satırı başına bir adet, parça başına saat ve USD'dir.

SQLAlchemy varsayılan olarak `backend/data/tgy.db` SQLite dosyasını kullanır. `DATABASE_URL` ortam değişkeniyle başka bir bağlantı seçilebilir. PostgreSQL sürücüsü ve uyumlu SQLAlchemy tipleri vardır; **gerçek PostgreSQL sunucusunda çalışma ve geçiş doğrulanmamıştır**. PostgreSQL'e geçiş tamamlanmış bir özellik olarak sunulmaz.

## Kalıcı veri modeli

| Tablo | Görev |
| --- | --- |
| `order_items` | Sipariş kalemleri; sipariş numarası + kalem tekilliği; malzeme/tedarikçi indeksleri |
| `materials` | Parça bilgileri; malzeme kodu kimliği |
| `mold_movements` | Tarihsel kalıp hareketleri; malzeme, ATA ve tarih indeksleri |
| `shipments` | Sevkiyatlar; malzeme, tedarikçi, sipariş, seri ve tarih indeksleri |
| `shipment_order_item_links` | Sevkiyat ve sipariş kalemine dış anahtarlarla bağlanan kesin seçimler |
| `source_records` | Kalıp gereksinimleri, tedarikçi–depo eşleştirmeleri ve hesaplama ayarları |
| `state_revision` | Tekil veri sürümü; iyimser eşzamanlılık kontrolü |
| `import_batches` | Önizleme raporu, doğrulanmış geçici kayıtlar ve aktarım durumu |
| `import_sources` | Aktarım partisine dış anahtarla bağlı özgün dosya adı ve çalışma kitabının orijinal baytları |
| `audit_log` | Değişiklik sürümü, zamanı, işlem türü ve önceki/sonraki değerler veya aktarım özeti |

Kaynak varlıklar ayrı tablolardadır; sık kullanılan ilişki anahtarları ayrı indeksli sütunlarda, tam kaynak kayıt Pydantic ile doğrulanmış JSON olarak tutulur. Bu, önerilen bütün iş varlıklarının tamamen normalleştirildiği anlamına gelmez. Tedarikçi, depo, kalıp gereksinimi ve eski kod onayı için genişletilmiş ilişkisel ana veri modeli ileride geliştirilebilir. Eksik parça veya bilinmeyen depo içeren kaynak satırlar silinmez; hesaplama katmanı bunları uyarı veya kontrol gereksinimi olarak gösterir.

## Yazma ve eşzamanlılık

`POST /api/changes` yalnızca doğrulanmış ekleme/güncelleme yapar; silme endpoint'i yoktur. İstemci gördüğü `expected_revision` değerini gönderir. Sunucu tek işlem içinde sürümü karşılaştırır, atomik artırır, kaynak değişikliklerini ve işlem günlüğünü yazar. Sürüm değişmişse HTTP 409 döner. Başarısız doğrulama veya doğal anahtar çakışmasında işlem geri alınır.

Kesin sevkiyat bağlantısı yalnızca sipariş, malzeme ve tedarikçisi eşleşen kaleme yapılabilir. Hem doğrudan güncelleme hem Excel güncellemesi mevcut kesin bağlantıları da yeniden doğrular. Kaynak değişikliği bir bağlantıyı geçersiz kılacaksa bütün işlem geri alınır. Sevkiyat bağlantısı teslim alınan miktarı değiştirmez.

## Excel akışı ve kaynak arşivi

1. Kullanıcı `.xlsx` dosyasını ve gerekiyorsa tek sayfanın liste türünü seçer.
2. OpenPyXL çalışma kitabını okur; kaynak sütunlar, metin/sayı/tarih alanları ve formül hücreleri doğrulanır. Pandas toplu seri tekrar kontrolünde kullanılır.
3. Önizleme; yeni, mevcut ve dosya içi mükerrer kayıt sayılarını, sınırlı örnek satırları, hataları ve uyarıları gösterir. Önizleme kaynak tablolara yazmaz.
4. Başarıyla ayrıştırılan çalışma kitabı, doğrulanmış geçici kayıtlar ve raporuyla aynı veritabanı işleminde **orijinal baytları ve dosya adıyla** arşivlenir. Alan doğrulama hataları içeren ama okunabilen dosyalar da raporuyla birlikte arşivlenir; bozuk veya güvenlik/boyut sınırını aşan dosyalar arşivlenmez.
5. Kullanıcı onayından sonra sürüm tekrar kontrol edilir. Varsayılan davranış mevcut kayıtları korur; yalnızca açık `update_existing` seçimi mevcut satırları günceller. Tam aynı kayıt yeniden eklenmez. Toplu eklemeler parçalara ayrılmış SQL işlemleriyle tek atomik aktarım içinde yapılır.

Kaynak sütun adları korunur. Metin kimlikleri baştaki sıfırlarıyla saklanır. Sayısal kimlikler açık uyarıyla metne çevrilir; Excel'de zaten kaybolmuş sıfırlar geri getirilemez. Sevkiyat tedarikçi adı yalnızca bilinen tek bir tedarikçi adıyla birebir eşleştiğinde numaraya çözümlenir ve uyarı üretilir. Çözümlenemeyen değer korunur. Özgün dosya arşivi, bu normalizasyonlardan önceki kaynak hücrelerin incelenmesini sağlar.

`GET /api/imports/{id}/source`, arşivlenen dosyanın baytlarını değişmeden indirir; HTTP dosya adı güvenli ve sabit `TGY-kaynak.xlsx` olarak verilir. Özgün kullanıcı dosya adı yalnızca veritabanında tutulur ve HTTP başlığına yerleştirilmez. Önceki sürümde oluşmuş ve kaynak arşivi olmayan partiler için 404 döner. `initialize()` yeni tabloyu ekleyerek var olan SQLite tablolarını ve kayıtlarını korur; bu mekanizma genel amaçlı şema değişikliği/migrasyon sistemi değildir.

Dosya sınırı 16 MB, toplam veri satırı sınırı 100.000'dir. Açılmış ZIP boyutu ve sayfa boyutları ayrıca sınırlanır. Hata/uyarı listeleri ilk 200 öğeyle, önizleme örneği ilk 20 kayıtla sınırlıdır; toplam sayılar ve kırpılma bilgisi ayrıca döner. Özgün çalışma kitaplarının veritabanında tutulması disk kullanımını artırır; üretim kullanımı öncesi yedekleme ve saklama politikası belirlenmelidir.

`GET /api/export` dört kaynak sayfasını XLSX olarak dışa aktarır. Bu dosya, ayarlar, kesin bağlantılar, aktarım arşivleri ve işlem günlüğünü kapsayan tam veritabanı yedeği değildir. `GET /api/template` aynı sütunlarla boş şablon üretir. Formül olarak yorumlanabilecek kaynak metinler dışa aktarımda metin hücresi olarak yazılır.

## Okuma ve performans sınırları

`GET /api/state` tam kaynak veri durumunu ve sürümü döndürür. `GET /api/assessments` aynı kaynaklardan sunucu tarafında hesaplanan sipariş sonuçlarını sürümle döndürür; sevkiyat ilişkileri tam nesne yerine kimlik listeleridir. İstemci veri ve hesaplama sürümlerinin uyuşmasını kontrol etmelidir.

`GET /api/orders?page=1&page_size=50&q=...`, aranan siparişleri hesaplanan alanlarıyla sayfalı döndürür. Endpoint mevcut olsa da **arayüz hâlen tam kaynak durumunu indirir ve yerel tablolarda sayfalar**. Tüm arayüzün sunucu tarafı sayfalama kullandığı iddia edilmemelidir. Ayrıca mevcut sipariş endpoint'i hesaplama motorunu kurmak için kaynak veri durumunu sunucu belleğine alır; tam SQL seviyesinde arama/hesaplama optimizasyonu tamamlanmış değildir.

İndeksli motor sipariş adaylarını birleşik anahtarla, seri tekrarlarını sayaçla ve hareketleri kalıp+malzemeyle bulur. Kalıp kronolojisi grup başına hesaplanır. 40.000 sentetik sevkiyat/2.000 sipariş motor kontrolü ve 40.000 satırlık gerçek XLSX biçiminde dosyanın önizleme/aktarımı test edilmiştir. Bu testler gerçek kullanıcı dosyasının doğrulandığı veya çok kullanıcılı üretim kapasitesinin ölçüldüğü anlamına gelmez. Yıllar arası büyümede SQL tarafı filtreleme/sayfalama, dar kapsamlı ilişki sorguları ve ölçüme dayalı önbellekleme gerekebilir.

## Doğrulanmış kapsam ve kalanlar

SQLite üzerinde boş başlangıç, kayıt doğrulama, yeniden açılışta kalıcılık, sürüm çakışması, atomik geri alma, Excel önizleme/onay, mevcut kayıt koruma, XLSX dışa/içe aktarım ve 40.000 satır akışı testlerle doğrulanmıştır. Bağımsız testin ayrıntıları ilgili test raporundadır; yeni eklenen özellikler ayrıca test edilmelidir.

Gerçek PostgreSQL, gerçek ERP bağlantısı, kullanıcı kimlik doğrulaması/yetkilendirme, çok kullanıcılı üretim dağıtımı, genel migrasyon altyapısı ve otomatik yedekleme doğrulanmış kapsamda değildir. Mevcut sunucu yerel geliştirme ve kullanıcı kabulü içindir; üretime dağıtım hazırlığı tamamlanmış gibi sunulmamalıdır.

## İş analisti operasyonel değerlendirmesi

### A. Tamamlanan özellikler

Gerçek çalışma alanı FastAPI ve SQLite üzerinden kalıcı kayıt tutar. Dört kaynak liste için Excel önizlemesi, sütun/veri tipi kontrolü, mükerrer değerlendirmesi, kullanıcı onaylı aktarım, mevcut kayıtları varsayılan olarak koruma ve XLSX dışa aktarma vardır. Parça durumu, kalıp konumu ve tedarikçi–depo eşleştirmelerindeki değişiklikler siparişin üretilebilirlik sonucuna ve açıklamalarına yansır. Belirsiz sevkiyat bağlantıları kesinleşmiş gibi kullanılmaz; kullanıcı yalnızca uygun aday kalemi seçebilir. Sunucu hesaplamaları kaynak veriden türetilir; fiziksel üretilebilirlik sipariş onayından ayrı değerlendirilir.

İyimser sürüm kontrolü, atomik geri alma ve işlem günlüğü uygulanmıştır. Özgün Excel kaynak arşivi, mevcut şemaya veri kaybı olmadan ekleme ve dosyanın birebir geri indirilmesiyle doğrulanmıştır. SQLite kalıcılığı ve tam uygulama akışları test edilmiştir; güncel test sayıları ve bağımsız kontrol kapsamı test raporundan izlenmelidir.

### B. Operasyonel faydalar

Satın alma ve planlama ekibi, siparişin neden üretilemediğini ilgili kaynak kayıtlarıyla inceleyebilir. Excel'in doğrudan canlı kayıtlara yazılmaması, hatalı satırların onay öncesinde görünmesini sağlar. Mevcut kayıtların korunması ve güncellemenin açık seçim gerektirmesi, yanlış dosya aktarımında üzerine yazma riskini azaltır. Özgün dosya arşivi ve aktarım günlüğü, normalizasyon sonrası değerin hangi kaynaktan geldiğinin araştırılmasına yardımcı olur.

Kalıcı kayıtlar uygulama yeniden açıldığında korunur. Sevkiyatın teslim alım sayılmaması ve iadelerin doğrulanan brüt kuralla bir kez düşülmesi mutabakatı destekler. Alternatif kalıplardan birinin uygun olmasıyla üretilebilirlik sağlanırken diğer alternatifin yanlış konumu gereksiz üretim engeline dönüştürülmez.

### C. Tespit edilen riskler ve sınırlar

- **Doğal anahtar değişiklikleri:** Sipariş kimliği sipariş numarası+kalem, sevkiyat kimliği seri+tedarikçi+sipariş+tarih+irsaliye, kalıp hareketi kimliği malzeme+ATA+ASY+tarih+kaynak+hedeftir. Excel'de bu alanların, özellikle tarihin, düzeltilmesi mevcut satırın güncellenmesi yerine yeni kimlikle yeni kayıt oluşmasına yol açabilir. Önizleme “yeni” sayısını gösterir; ancak bunun iş açısından düzeltme mi yeni olay mı olduğunu kendiliğinden bilemez. Yanlış eski kaydı sessizce silmez. Bu tür düzeltmeler kontrollü kayıt uzlaştırması gerektirir.
- **Kalıp kimliği ve depo ana verisi:** Fiziksel kalıbın ATA/ASY birleşimiyle nasıl tekilleştiği ve gerçek tedarikçi–depo karşılıkları henüz doğrulanmamıştır. Hesaplama motoru konum için malzeme+ATA anahtarını kullanır; aynı ATA altında farklı fiziksel kalıplar varsa gerçek kullanım öncesi model uyarlanmalıdır.
- **Yerel kullanım sınırı:** Kimlik doğrulama ve yetkilendirme yoktur. Mevcut uygulama yerel geliştirme ve kullanıcı kabulü içindir; çok kullanıcılı üretim dağıtımına hazır olduğu sonucuna varılmamalıdır.
- **Şema ve yedekleme:** Yeni tablo ekleme mevcut şemayı korur; genel şema migrasyonu, geri dönüş planı ve otomatik yedekleme altyapısı değildir. XLSX dışa aktarımı da bütün veritabanının yedeği değildir. Kaynak arşivinin disk kullanımına etkisi izlenmelidir.
- **Veri hacmi:** Sayfalı sipariş API'si vardır; arayüz hâlen tam veri durumunu indirir. 40.000 satırlık testler bu sınırı kaldırmaz. Yıllar biriktikçe istemci belleği, ilk yükleme süresi ve API sorguları gerçek veride ölçülmelidir.
- **Seri tekilliği:** Mükerrer kontrolü seri metni genelinde yapılır. Aynı seri numarası farklı malzeme veya tedarikçide meşru biçimde tekrar edebiliyorsa mevcut uyarı kapsamı gereğinden geniş olabilir; kayıtlar bu uyarı nedeniyle otomatik silinmez.

### D. İyileştirme önerileri

Öncelik, anonimleştirilmiş küçük bir gerçek dosya grubuyla kaynak kimlikleri ve depo sözlüğünü doğrulamak olmalıdır. Ardından doğal anahtarı değişen düzeltmeler için eski/yeni kayıtları yan yana gösteren, açık onay ve işlem izi olan bir uzlaştırma akışı tasarlanmalıdır. Gerçek geçmiş dosyaları küçük bir partide aktarılıp kaynak arşivi, sipariş bağlantıları ve tutar mutabakatı kontrol edildikten sonra kapsam büyütülebilir.

İşletim ihtiyacına göre otomatik SQLite yedeği, kaynak dosya saklama süresi ve geri yükleme tatbikatı belirlenmelidir. Çok kullanıcılı kullanımdan önce erişim kontrolü, genel migrasyon altyapısı ve hedef veritabanında entegrasyon testleri tamamlanmalıdır. Hacim arttıkça arayüzün sayfalı API'lere taşınması ve hesaplama için gerekli dar veri kümelerinin sorgulanması önerilir.

### E. Kullanıcıdan beklenen kalan kararlar

Gelen Miktar'ın brüt olduğu, alternatif kalıptan bir uygunun yeterli olduğu, sevkiyat satırının bir parça olduğu, saatlerin parça başına tanımlandığı, USD ve yaklaşık yıllık 40.000 sevkiyat hacmi yanıtlanmıştır; bu konularda yeniden karar beklenmemektedir.

Kalan ana veri kararları şunlardır:

1. ATA ve ASY tek başına veya birlikte hangi fiziksel kalıbı tanımlar? Bir kalıp birden fazla malzemede ortak kullanılabilir mi?
2. Gerçek tedarikçi numaraları hangi depo kimlikleriyle eşleştirilmelidir? İlk örnek eşleştirmeleri kim doğrulayacaktır?
3. Seri numarası bütün sistemde mi, malzeme bazında mı, tedarikçi bazında mı tekildir?

Bu kararlar netleşene kadar eksik veya çelişkili kayıtlar kesin olumlu eşleşme yerine açık uyarı/kontrol gereksinimiyle değerlendirilmelidir.
