# Aşama 1 — Bağımsız kalite güvence test planı

Bu plan kullanıcı gereksinimlerinden hazırlanmıştır. Testler henüz çalıştırılmamıştır; aşağıdaki tüm sonuçlar **Test edilmedi** durumundadır. Kod ve test ortamı hazır olduğunda gerçekleşen sonuç, hata açıklaması ve düzeltme durumu ayrıca kaydedilecektir. Testler demo veri üzerinde gerçekleştirilecek; gerçek ERP entegrasyonu veya Python uygulaması doğrulanmış sayılmayacaktır.

| No | Test adı | Test verisi | Beklenen sonuç | Gerçekleşen sonuç | Durum | Hata açıklaması / Düzeltme |
|---|---|---|---|---|---|---|
| 1 | Pasif parça | M-01 parçası Pasif; kalıbı doğru tedarikçide | ÜRETİLEMEZ; pasif parça nedeni görünür | Çalıştırılmadı | Test edilmedi | İnceleme bekliyor |
| 2 | Yanlış depodaki kalıp | M-02 aktif; sipariş tedarikçisi A; gerekli kalıbın konumu B | ÜRETİLEMEZ; yanlış konum nedeni görünür | Çalıştırılmadı | Test edilmedi | İnceleme bekliyor |
| 3 | Uygun kalıp ve aktif parça | M-03 aktif; tüm tanımlı gerekli kalıplar açık eşleştirmeyle A'da | ÜRETİLEBİLİR; sipariş onayı ayrı gösterilir | Çalıştırılmadı | Test edilmedi | İnceleme bekliyor |
| 4 | Eksik kalıp verisi | M-04 aktif; gerekli kalıbın başlangıç konumu ve hareketi yok | KONTROL GEREKLİ; kalıbın yok olduğu varsayılmaz | Çalıştırılmadı | Test edilmedi | İnceleme bekliyor |
| 5 | Kalıp transferi | M-05 aktif; A tedarikçisine sipariş; kalıp A→B geçerli transferi | A siparişi üretilemez; varsa B siparişi üretilebilir olarak yeniden hesaplanır | Çalıştırılmadı | Test edilmedi | İnceleme bekliyor |
| 6 | Eksik parça kaydı | Siparişte M-06 var; parça listesinde yok | VERİ EKSİK / KONTROL GEREKLİ; yalnızca eksiklikten üretilemez sonucu çıkmaz | Çalıştırılmadı | Test edilmedi | İnceleme bekliyor |
| 7 | Mükerrer sevkiyat | Aynı seri numarasıyla iki sevkiyat | Şüpheli mükerrer seri uyarısı; sessiz birleştirme veya silme yok | Çalıştırılmadı | Test edilmedi | İnceleme bekliyor |
| 8 | Sipariş–sevkiyat eşleşmesi | Sipariş, malzeme ve tedarikçi anahtarlarında tek aday sevkiyat | İlgili sipariş detayında görünür; teslim alınan miktar değişmez | Çalıştırılmadı | Test edilmedi | İnceleme bekliyor |
| 9 | Belirsiz sipariş kalemi | Aynı sipariş/malzeme/tedarikçiye ait 10 ve 20 kalemleri; sevkiyatta kalem yok | İki aday sunulur; kullanıcı seçene kadar kesin bağlantı kurulmaz | Çalıştırılmadı | Test edilmedi | İnceleme bekliyor |
| 10 | Excel güncellemesi | Parça M-10 aktiften pasife değişen içe aktarım | Doğrulama ve önizleme sonrası onayla değişir; ilgili sipariş yeniden hesaplanır | Çalıştırılmadı | Test edilmedi | Gerçek Excel akışı yoksa açıkça kapsam dışı raporlanmalı |
| 11 | İade miktarı | Miktar 100; Gelen 40; İade 5; iade kuralı bilinmiyor / net / brüt | Bilinmiyorsa kesin net hesap yok; net kuralda net 40/kalan 60; brütte net 35/kalan 65 | Çalıştırılmadı | Test edilmedi | İnceleme bekliyor |
| 12 | Geçmiş tarihli kalıp hareketi | 10.01 A→B; 20.02 B→C; sonradan 01.01 X→A eklenir | Güncel konum C kalır; fiziksel satır sırasına göre hesaplanmaz | Çalıştırılmadı | Test edilmedi | İnceleme bekliyor |

## Ek risk kontrolleri

- Aynı tarihli çelişkili hareketler veya kaynak–hedef zincirindeki kopukluk, kesin lokasyon yerine açıklanabilir uyarı üretmelidir.
- Çoklu kalıp gerekliliği tanımlanmamışsa tümü veya herhangi biri varsayımıyla kesin üretilebilirlik kararı verilmemelidir.
- Birden fazla olumsuz koşul birlikte açıklanmalıdır. Sipariş onayı fiziksel üretilebilirliğin yerine geçmemelidir.
- Tedarikçi–depo ilişkisi yalnızca isim benzerliğiyle kesinleştirilmemelidir.
- Eski malzeme kodu, onaylı kod eşleştirmesi olmadan yeni kodla eşdeğer kabul edilmemelidir.
- Para birimi bilinmeyen tutarlar veya farklı para birimleri tek genel toplamda birleştirilmemelidir.
- Seri bazlı sevkiyat varsayımı doğrulanmadan satır sayısı teslimat miktarı olarak kullanılmamalıdır.
- Arama, filtreleme, sıralama, sayfalama, kolon görünürlüğü ve detay paneli; boş sonuç ve sıfır kayıt durumlarında kontrol edilmelidir.
- Değişikliklerin saklama süresi ekranda belirtilmeli; kaydetmeyen prototip kalıcıymış gibi sunulmamalıdır.
- Excel aktarımı veya gerçek dosya içe aktarma yoksa bu özellikler çalışıyor diye raporlanmamalıdır.

## Yürütme ve raporlama

İş kuralları bağımsız test verileriyle doğrulanacak. Arayüz akışları mümkünse gerçek tarayıcı otomasyonuyla kontrol edilecek. Derleme yalnız başına işlevsel doğrulama kabul edilmeyecek. Başarısız testler geliştirmeciye bildirilecek; düzeltme sonrası ilgili test ve regresyon grubu yeniden çalıştırılacak. Son rapor, başarılı/başarısız/test edilmedi durumlarını ayrı gösterecek.
