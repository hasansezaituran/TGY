# Aşama 2 — Bağımsız API ve Excel test planı

Bu plan, kullanıcı onayıyla başlatılan Python/FastAPI ve kalıcı veri aşamasının kabul kriterlerini tanımlar. Her test izole geçici SQLite veritabanında çalıştırılır; gerçek kullanıcı kayıtlarına dokunulmaz. Henüz çalıştırılmayan senaryolar başarılı sayılmaz.

| Öncelik | Senaryo | Test verisi / İşlem | Beklenen sonuç |
|---|---|---|---|
| 1 | Gerçek ortam başlangıcı | Yeni veritabanında GET /api/state | Listeler boş; demo veri yok; gross/any/tek parça/parça başına saat ayarları doğru |
| 1 | Atomik kayıt | Tek değişiklik grubunda sipariş, parça, kalıp, sevkiyat ve eşleştirmeler | Kaynak kayıtlar saklanır; revizyon tek artar; hesaplanan alan kaynaklara karışmaz |
| 1 | Doğrulama ve geri alma | Geçerli parça + negatif miktarlı sipariş birlikte gönderilir | Hata; kısmi kayıt ve revizyon değişikliği olmaz |
| 1 | Eski revizyon | Aynı expected_revision ile iki farklı yazma | İkinci istek 409; ilk kayıt korunur |
| 1 | Önizleme kayıt yapmaz | Gerçek .xlsx dosyası preview ile yüklenir | Önizleme raporu oluşur; kaynak veriler/revizyon değişmez |
| 1 | İçe aktarma onayı | can_commit=true önizlemesi onaylanır | Kayıtlar atomik aktarılır; revizyon artar |
| 1 | Varsayılan koruma | Aynı doğal anahtarlı mevcut parçada farklı değerler yüklenir | update_existing=false varsayılanında önceki değer korunur; yeni kayıtlar eklenir |
| 1 | Açık güncelleme onayı | Aynı önizleme update_existing=true ile onaylanır | Mevcut hedef kayıt güncellenir; diğer varlıklar silinmez |
| 1 | Önizleme sonrası değişiklik | Önizleme alınır, API yazması yapılır, eski aktarım onaylanır | 409; yeni API verileri korunur |
| 1 | Mükerrer dosya satırı | Aynı doğal anahtarlı iki satır | Mükerrer raporlanır; sessiz yanlış üzerine yazma veya iki kayıt oluşmaz |
| 1 | Hatalı Excel | Eksik başlık, yanlış veri tipi, geçersiz gün/ay, bozuk dosya | Satır/alan bazlı anlaşılır hata; kaynak veriler korunur |
| 1 | Yeniden başlatmada kalıcılık | Kayıt yazılır, istemci/uygulama yeniden açılır | Kaynak veriler ve revizyon korunur |
| 2 | Excel dışa/içe turu | Dört varlığı export et; yeni boş veritabanına preview+commit | Kaynak sütun adları/sırası ve değerler korunur; sayfalar ilişkilenebilir |
| 2 | Kimlik ve veri bütünlüğü | Sipariş no+kalem çakışması, geçersiz manuel sevkiyat linki | Çakışma reddedilir; yanlış siparişe kesin bağlantı kurulmaz |
| 2 | Geçmiş yılı koruma | 2026 tarihli sevkiyat yükle | Yalnız eski tarih diye satır atılmaz |
| 2 | 40.000 satır | Benzersiz seri numaralı 40.000 gerçek xlsx satırı preview+commit | Tamamı görülür ve saklanır; önizleme toplamı sınırlı gösterimle karıştırılmaz |
| 2 | Güvenli şablon | GET /api/template | Dört veri grubu için doğru kaynak başlıkları; kullanıcı doldurabilir gerçek xlsx |

## Doğrulama sınırları

API testleri gerçek HTTP istemci sözleşmesini FastAPI TestClient üzerinden ve gerçek SQLite dosyasıyla doğrular. SQLite koşumu PostgreSQL çalışmasını, ağ dağıtımını veya gerçek ERP entegrasyonunu tek başına doğrulamaz. Tarayıcıdan dosya seçimi ve kullanıcının önizleme/onay akışı ayrıca uçtan uca test edilmelidir. Hacim ölçümleri sentetik dosya üzerinde raporlanacak; gerçek dosya veya genel performans garantisi gibi sunulmayacaktır.

## Raporlama

Her çalıştırma sonucu; geçen/kalan/çalıştırılmayan sayıları, kullanılan dosya ve kayıt adetleri, anlamlı süre ölçümleri, bulunan kusur ve düzeltme sonrası yeniden test durumlarıyla belgelenir. Önizleme aşamasındaki `import_batches` kaydı kaynak veri kaydı sayılmaz; önizleme kaynak listelerinin ve revizyonun değişmemesiyle kontrol edilir.
