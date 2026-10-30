# TGY — 2027 Sipariş, Kalıp ve Sevkiyat Takip Sistemi

**Aşama 2:** React + TypeScript arayüz, Python/FastAPI servis, SQLAlchemy/SQLite kalıcı kayıt, Pandas/OpenPyXL ile gerçek Excel aktarımı. Arayüz Türkçedir. Kullanıcının web prototipi onayı alınmıştır.

## Yalnız Python ile hazır paketi çalıştırma

**[Python için tam ZIP paketini indir](https://github.com/hasansezaituran/TGY/raw/refs/heads/main/release/TGY-Python-Tam-Paket.zip)**

Hazır ZIP içinde `dist` derlenmiş arayüzü bulunur. **Node.js gerekmez.** ZIP'i tamamen çıkarın. Python 3.12+ bulunan bilgisayarda Windows'ta `BASLAT.bat` dosyasına çift tıklayın veya `py baslat.py`; macOS/Linux'ta `python3 baslat.py` çalıştırın. İlk açılış Python bağımlılıkları için internet ister. Tarayıcı otomatik açılır; adres `http://127.0.0.1:8765` olur. Tek Python sunucusu arayüzü ve API'yi birlikte sunar. Terminal açık kalır; Ctrl+C ile kapatılır. `KULLANIM.txt` dosyasını okuyun.

Aşağıdaki Node.js adımları arayüz kaynak kodunu **geliştirmek/yeniden derlemek** içindir. Hazır paketi denemek için gerekmez.

## Kurulum

Node.js 24 LTS / npm 11 ve Python 3.12 ile doğrulandı. Yerel bilgisayarda depo kök dizininde çalıştırın:

```sh
python -m venv .venv
# Linux/macOS:
.venv/bin/python -m pip install -r backend/requirements.txt
# Windows alternatifi:
# .venv\Scripts\python.exe -m pip install -r backend/requirements.txt
npm ci --no-audit --no-fund
```

Bulut checkout yolu `/workspace/TGY`'dir. Mevcut checkout kullanılır; kullanıcı istemedikçe worktree oluşturulmaz.

## Çalıştırma

İki terminalde, depo kök dizininde:

```sh
# Terminal 1 — Python API
.venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
# Windows'ta .venv/bin/python yerine .venv\Scripts\python.exe kullanın.

# Terminal 2 — Web arayüzü
npm run dev -- --port 5173
```

Yerel bilgisayarda tarayıcıya `http://127.0.0.1:5173` adresini yazın. Bulut onboarding ortamında bu yerel adres kullanıcı önizleme bağlantısı değildir. Vite `/api` isteklerini yerel FastAPI sunucusuna iletir. API sağlığı `/api/health`, etkileşimli API belgesi Python sunucusunun `/docs` yolundadır. `npm run build` üretim derlemesini üretir; `npm run preview` tek başına Python API'sini sağlamaz. Bu teslimin çalıştırma yolu yukarıdaki iki süreçtir.

## Gerçek veri ve demo ayrımı

- İlk açılış **Gerçek veriler · Kalıcı** alanıdır. Veritabanı boş başlar; demo kayıtları otomatik eklenmez.
- Kaynak kayıtlar, eşleştirmeler, kalıp gereksinimleri ve kurallar `backend/data/tgy.db` dosyasında tutulur. Sayfa veya servis yeniden başlasa da veriler korunur. Bu dosyayı silmek veriyi siler.
- Üst menüde **Demo · Geçici** seçilirse örnek veri açılır. Demo değişiklikleri sayfa yenilendiğinde sıfırlanır ve gerçek veritabanına yazılmaz. Mod seçimi tarayıcıda hatırlanır.
- Gerçek modda sipariş hesapları Python servisinden gelir. Veriler değiştiğinde ilişkiler yeniden hesaplanır. Hatalı veya eski sürümlü yazma başarı bildirimi üretmez; eski sürüm 409 hatasıyla reddedilir.
- Filtreler, sütun görünürlüğü ve tema oturum tercihidir; kalıcı iş verisinin parçası değildir.

## Excel aktarımı

1. **Veri Aktarımı → Excel şablonu** ile kaynak başlıklarını indirin. Başlıkları değiştirmeyin. Malzeme, sipariş ve kalem kodlarını metin olarak saklayın; baştaki sıfırları koruyun.
2. Aynı dosyada `Sipariş Kalemleri`, `Kalıp Bilgileri`, `Parça Bilgileri`, `Sevkiyat Listesi` sayfalarını kullanın. Tek sayfalı dosyada liste türünü ekrandan seçebilirsiniz. Gruplar ayrı dosyalardan da alınabilir.
3. `.xlsx` dosyasını seçip **Dosyayı doğrula ve önizle** düğmesine basın. Kaynak kayıtlar henüz değişmez. Eksik sütun, tip, tarih, miktar, çelişkili mükerrer ve eşleşme uyarıları ile ilk 20 örnek gösterilir.
4. Hata varsa dosyayı düzeltin. Hata/uyarı raporu tür başına ilk 200 sorunu ve toplam sayıları gösterir; kontrol listesini Excel'e indirebilirsiniz.
5. Varsayılan aktarım yalnız yeni kayıt ekler, mevcut kayıtları korur. Mevcut değerleri güncellemek için ayrıca **güncellemeyi onaylıyorum** seçeneğini işaretleyin. **Önizlemeyi inceledim** onayından sonra aktarımı uygulayın. Hiçbir kaynak kayıt otomatik silinmez.
6. Eşzamanlı değişiklik nedeniyle önizleme sürümü eskirse dosyayı yeniden önizleyin. Aktarım tek transaction'dır; hatada kısmi kayıt bırakılmaz.

Sınırlar: dosya en fazla 16 MB, toplam en fazla 100.000 veri satırı, açılmış çalışma kitabı en fazla 128 MB. Formül hücreleri reddedilir; hesaplanmış değeri yapıştırın. Excel tarih hücreleri, `GG.AA.YYYY` ve ISO tarihler desteklenir. Sayısal hücreler veya noktalı ondalık metin kullanın; belirsiz virgüllü metinler sessizce çevrilmez. Sayısal kodlar metne çevrilirse uyarılır; Excel'de kaybolmuş sıfırlar geri getirilemez.

Sipariş anahtarı **Sipariş Numarası + Sipariş Kalem**, parça anahtarı **Malzeme Kodu**. Kalıp hareketleri kaynak/hedef/tarih/kalıp birleşimiyle, sevkiyatlar tedarikçi/sipariş/malzeme/seri/tarih/irsaliye birleşimiyle kontrol edilir. Aynı seri farklı hareketlerde görünürse kayıtlar korunur ve uyarılır. Hareketin tarihini veya sevkiyatın kimlik alanlarını düzeltecekseniz mevcut kaydı detay panelinden düzenleyin; farklı doğal anahtarlı Excel satırı yeni kayıt sayılır.

**Tüm kaynak verileri yedekle** dört kaynak listesini Excel'e çıkarır; ayarlar, bağlantılar ve işlem geçmişinin tam yedeği değildir. Orijinal yükleme dosyaları veri tabanındaki aktarım arşivinde korunur. Tam yedek aşağıda açıklanır.

## İlişkileri tanımlama ve düzenleme

- Her operasyon sayfasında **Kayıt ekle**; detayda **Kaynak kaydı düzenle** bulunur. Değişiklikler kaydedilip durumlar yeniden hesaplanır.
- Parça detayında alternatif **Kalıp ATA Kodları** listesini noktalı virgülle tanımlayın. Kalıp hareketi kaydı tek başına bu kalıbın gerekli olduğunu kanıtlamaz; gereksinimler otomatik tahmin edilmez.
- Ayarlardan **Tedarikçi–Depo eşleştirmeleri**ni açıkça tanımlayın. Benzer isimler otomatik eşleştirilmez.
- Sevkiyat detayında birden fazla sipariş kalemi adayı varsa kullanıcı doğru kalemi seçer. Sevkiyat, teslim alınan miktarı değiştirmez.
- **Raporlar → İşlem geçmişi** kaynak güncellemelerini ve aktarımları sürüm bilgisiyle gösterir.

Doğrulanmış başlangıç kuralları: Gelen Miktar brüt; net = gelen − iade. Alternatif kalıplardan biri uygunsa yeterli. Sevkiyat satırı 1 adet. Adam saatleri parça başına. Para birimi USD; farklı para birimleriyle gelen gelecekteki kayıtlar birleştirilmez. Kaynak teslim durumu ve hesaplanan kalan miktar ayrı tutulur.

## Yedekleme

Uygulama çalışırken bile SQLite'ın tutarlı yedeğini almak için:

```sh
.venv/bin/python scripts/backup.py
# İsteğe bağlı yeni hedef dosyası:
.venv/bin/python scripts/backup.py /guvenli/yedek/tgy.sqlite
```

Mevcut hedef dosyanın üzerine yazılmaz. Varsayılan klasör `backend/data/backups`'tır. Daha güvenli saklama için yedeği bu makine dışında kendi yedekleme alanınıza kopyalayın. Geri yüklemede iki servisi durdurun, mevcut dosyayı ayrıca koruyun ve yedeğin kopyasını `backend/data/tgy.db` olarak kullanın; yanlış dosyanın üzerine yazmayın.

`DATABASE_URL` ile SQLite yolu veya PostgreSQL bağlantısı seçilebilir (`backend/.env.example`). Örnek dosya otomatik okunmaz; değişkeni süreç ortamına kendiniz tanımlayın. PostgreSQL sürücüsü kurulur, ancak gerçek PostgreSQL üzerinde çalışma ve veri taşıma bu teslimde doğrulanmadı. Mevcut SQLite verisini URL değiştirmek otomatik taşımaz.

## Doğrulama

```sh
npm test
npm run build
.venv/bin/python -m pytest backend/tests -q
# Sistem Chromium /usr/bin/chromium ve açık Vite 5173 ile demo regresyonu:
node scripts/browser-check.mjs
# Geçici SQLite + kendi API/Vite süreçleriyle kalıcı uygulama testi:
node scripts/fullstack-check.mjs
```

Tam yığın betiği yalnız kendisinin açtığı 8001/5174 süreçlerini durdurur; kullanıcı veritabanını kullanmaz. Test dosyaları `/tmp/tgy-fullstack-*` altında kalır. Tarayıcı testleri bu Linux ortamındaki Chromium yolunu kullanır; başka işletim sisteminde yol uyarlanmalıdır.

2026 sevkiyat hacmi olan **40.000 satır** referans alınmıştır. Gerçek `.xlsx` üretme/önizleme/aktarımı/yeniden açılışı ve indeksli motor sentetik 40.000 satırla test edilmiştir. Kullanıcının gerçek dosyaları henüz yüklenmedi. API'de sayfalı sipariş uç noktası bulunur; mevcut arayüz çalışma alanı verilerini toplu yükler. Gerçek çok kullanıcılı yük, ağ koşulları ve PostgreSQL performansı doğrulanmadı.

Bu sürüm yerel çalışma içindir. Kimlik doğrulama, kullanıcı yetkileri ve üretim dağıtımı eklenmeden internete açık sunucu olarak yayımlamayın. SQLite şeması ilk açılışta oluşturulur; mevcut kurulumlar için kapsamlı sürümlü migration sistemi henüz yoktur. ExcelJS dışa aktarım parçası ihtiyaç anında yüklenir; büyük dosya boyutu uyarısı derlemeyi engellemez.

İş analizi: [docs/is-analizi.md](docs/is-analizi.md). Python kuralları: [docs/python-kurallari.md](docs/python-kurallari.md). Aşama 2 doğrulama: [docs/asama2-test-raporu.md](docs/asama2-test-raporu.md). Önceki prototip raporu: [docs/test-raporu.md](docs/test-raporu.md).
