# Mate ve EvoSpace: öğrenci çalıştırma kılavuzu

YL – Ahmet ve Mehmet • 24 Kasım 2026 • Paket v1

Bu paket, iki yüksek lisans projesinin başlangıcında kullanılacak **Mate (FSM/PFSM)** ve **EvoSpace (YSA)** kaynaklarını, yayımlanmış hazır denetleyicileri ve önceki doğrulama kayıtlarını içerir. Amaç, bu denetleyicileri yeniden çalıştırmak ve üç görevde makalenin simülasyon ortalamalarıyla karşılaştırmaktır. Hazır denetleyiciler yeniden eğitilmez; tam otomatik tasarım/optimizasyon kampanyası bu komutlarla başlatılmaz.

**Başlangıç sırası:** ZIP’i çıkarın → ortamı hazırlayın → kaynakları derleyin → kısa kontrolü çalıştırın → tam deneyi çalıştırın → `ozet.json` içindeki altı sonucu inceleyin. Bu kılavuzun Word sürümü `README.docx` dosyasıdır.

## 1. Hangi bilgisayarda çalışır?

Simülasyon için **Linux x86-64**, Python 3.10+, g++, GNU make, pkg-config ve **CMake 3.x** gerekir. Windows kullanıyorsanız WSL2 altında Ubuntu kullanın. Yerel Windows, macOS ve ARM/Raspberry Pi simülasyon çalıştırması bu paketin doğrulanmış kapsamına dahil değildir. Arşiv ve dosya bütünlüğü kontrolleri Windows üzerinde de çalışır; Windows komutlarında `python3` yerine `python` kullanabilirsiniz.

Önceki simülasyonlar Linux x86-64, GCC 14.2.0, glibc 2.41 ve CMake 3.27.9 ile yapılmıştır. Ubuntu 24.04/WSL2, öğrenciler için kurulum yoludur; bu dağıtımda yeni bir tam deney çalıştırıldığı iddia edilmez. Bu paket hazırlanırken mevcut Windows ortamında Linux/WSL çalıştırılamadığı için yeni derleme ve simülasyon yapılmadı. Önceki 2.100 başarılı koşunun logları, girdileri ve ortalamaları yeniden denetlendi. Yeni ortak çalıştırma betiğinin Linux üzerindeki ilk kullanımında aşağıdaki kısa kontrolü tamamlayın.

Ubuntu ortamında eksik temel araçları kurun (internet ve yönetici parolası yalnızca bu adım için gerekebilir):

```bash
sudo apt update
sudo apt install -y build-essential cmake pkg-config python3 unzip
python3 --version
cmake --version
g++ --version
```

CMake çıktısı `3.x` olmalıdır. CMake 4, bu eski kaynakların politika uyumsuzluğu nedeniyle kurulum betiği tarafından reddedilir. Kendi CMake 3 kurulumunuz varsa `kur` komutuna `--cmake /tam/yol/cmake` ekleyin. Qt, ROS, NumPy, SciPy, R ve GPU bu hazır-denetleyici değerlendirmesi için gerekmez. Grafik pencere açılmadan sayısal sonuç üretilir; kamera sensörü simülasyonda aktiftir.

**Dizin adı:** paketi `~/mate_evospace` gibi boşluksuz ve yalnızca ASCII karakterlerden oluşan bir Linux yoluna çıkarın. WSL kullanırken `/mnt/c/Users/.../Öğrenci araştırma/...` altında derlemeyin. Eski EvoSpace `-g` argüman ayrıştırıcısı boşluk içeren genom yolunu kesmektedir; bu koşul baştan kontrol edilir. ZIP’teki iç klasörü `~/mate_evospace` olarak yeniden adlandırabilirsiniz.

Örnek çıkarma komutları (ZIP dosyasının yolunu kendi indirme konumunuza göre değiştirin):

```bash
mkdir -p ~/mate_evospace_paket
unzip /ZIP_DOSYASININ_YOLU/Mate_EvoSpace_Ogrenci_Paketi.zip -d ~/mate_evospace_paket
cd ~/mate_evospace_paket/Mate_EvoSpace_Ogrenci_Paketi
```

## 2. Önce paketin bütünlüğünü ve hazır sonuçlarını kontrol edin

Bu adım derleyici istemez ve simülasyon başlatmaz. Önceki kayıtların doğru taşındığını ve tablodaki ortalamaların ham loglardan hesaplanabildiğini gösterir:

```bash
python3 calistir.py arsiv-kontrol
```

Normal son satır: **`SONUÇ: 2100/2100 tarihsel kayıt ve altı görev ortalaması doğrulandı.`** Her satırda bir yöntem/görev, yayın ortalaması, arşiv ortalaması ve mutlak bağıl fark yazılır. Yalnızca dosya kontrolü için `python3 calistir.py butunluk` komutunu kullanın.

Bu başarı mesajı, kendi bilgisayarınızda simülatörün çalıştığı anlamına gelmez. Yeni simülasyon için 3–5. adımları uygulayın.

## 3. İki yöntemi tek komutla derleyin

Paketin kök dizininde:

```bash
python3 calistir.py kur --jobs 4
```

Komut, ZIP içindeki sabit kaynakları SHA-256 ile kontrol eder; ARGoS, e-puck, DAO, görev puanlayıcıları, Mate, EvoSpace ve açıkça belirtilen iki çalışma profili eklentisini `runtime/` altında derler. Kod indirmez, `sudo` kullanmaz, sistem dizinlerine kurulum yapmaz. Belleği az olan bilgisayarda `--jobs 2` kullanın. Hata varsa ilgili `runtime/**/logs/` veya derleme logunda ayrıntı bulunur.

Bu aşamada yalnızca derleme yapılır. Başarı sonunda `runtime/ogrenci_runtime.json` oluşur; kullanılan derleyici, yollar, komutlar ve yeni ikililerin hash’leri saklanır. Derleme tamamlandıktan sonra klasörü taşımayın. Taşıdıysanız yeni konumda `kur` komutunu yeniden çalıştırın.

## 4. Kısa işlev kontrolü: altı koşu

```bash
python3 calistir.py deney --kisa --workers 2 --out runs/kisa_01
```

Her yöntem/görev için ilk denetleyici ve ilk seed ile bir koşu yapılır: toplam altı koşu. Her koşu 20 robot, 120 saniye simülasyon ve saniyede 10 kontrol adımı kullanır. Duvar saati süresi bilgisayara bağlıdır; 120 saniye beklemek zorunda değildir.

Normal sonuç: `runs/kisa_01/ozet.json` içinde `runs: 6`, `all_successful: true`, `quick_check: true`. **Altı tekil koşuyla %10 ortalama eşiği değerlendirilemez.** Bu aşama, kurulumun ve eklentilerin çalışmasını sınar; tam sonuç için sonraki adımı yapın.

## 5. Tam karşılaştırma: 2.100 yeni simülasyon

```bash
python3 calistir.py deney --workers 2 --out runs/tam_01
```

Komut iki yöntemin üç görevini aşağıdaki sabit planla çalıştırır. Yalnız bir yöntem için şu komutları kullanabilirsiniz:

```bash
python3 calistir.py deney --method mate --workers 2 --out runs/mate_01
python3 calistir.py deney --method evospace --workers 2 --out runs/evospace_01
```

İsterseniz `--task apc`, `--task nc` veya `--task cc` ekleyerek tek görev seçin. Aynı komut ve aynı `--out` ile kesilmiş bir deneyi sürdürebilirsiniz; başarılı kayıtlar, çalışma imzası ve dosya hash’leri uyuşursa tekrar çalıştırılmaz. Ayarları değiştirdiğinizde yeni bir çıktı dizini kullanın. Başarısız kayıtlar sessizce atılmaz veya ortalamadan çıkarılarak kabul sonucu üretilmez.

| Yöntem / görev | Denetleyici | Seed aralığı | Koşu | Zemin / kamera | CC başlangıcı |
|---|---|---|---|---|---|
| Mate / APC | 10 FSM | 1001–1050 | 500 | warm / özgün | — |
| Mate / NC | 10 FSM | 4001–4050 | 500 | cold / kanonik | — |
| Mate / CC | 10 FSM | 1001–1050 | 500 | warm / özgün | İlk 5 beyaz, son 5 siyah |
| EvoSpace / APC | 10 YSA | 2001–2020 | 200 | cold / özgün | — |
| EvoSpace / NC | 10 YSA | 2001–2020 | 200 | cold / özgün | — |
| EvoSpace / CC | 10 YSA | 2001–2020 | 200 | cold / özgün | Özgün XML’deki rastgele politika |

Bu tablo, önceki %10 altı sonuçların elde edildiği **farklı profilleri** açıkça korur. Altı hücrenin tek ortak protokol altında çalıştırıldığı iddia edilmez. İki tez arasında yeni bilimsel yöntem karşılaştırması yapılacaksa ortak protokol ayrıca belirlenip bütün hücreler yeniden çalıştırılmalıdır.

## 6. Beklenen sonuçlar ve %10 hesabı

Aşağıdaki sayılar 21 Kasım 2026 tarihli **gerçek simülasyon loglarından** yeniden hesaplanan referanslardır. Öğrencinin yeni deneyinde hedef, her yöntem/görevin tam koşu ortalamasının yayın ortalamasından mutlak bağıl farkının %10 altında olmasıdır. Yeni bilgisayarda birebir aynı puan veya kesin %10 altı sonucu garanti edilmez; ortam farkı varsa sonuçlar korunur ve inceleme gerekir.

| Yöntem | Görev | n | Yayın ham ortalaması | Önceki koşuların ortalaması | Mutlak bağıl fark |
|---|---|---|---|---|---|
| Mate | APC | 500 | 102.753710 | 99.926514 | %2.7514 |
| Mate | NC | 500 | 646.043700 | 692.184560 | %7.1421 |
| Mate | CC | 500 | 735.828900 | 728.574574 | %0.9859 |
| EvoSpace | APC | 200 | 96.991930 | 93.168887 | %3.9416 |
| EvoSpace | NC | 200 | 682.770500 | 693.680035 | %1.5978 |
| EvoSpace | CC | 200 | 387.730900 | 394.199560 | %1.6683 |

```text
mutlak_bagil_fark_yuzde = 100 * abs(yeni_ortalama - yayin_ortalamasi) / abs(yayin_ortalamasi)
kabul = tum_kosular_basarili AND tam_kosu_sayisi AND mutlak_bagil_fark_yuzde < 10
```

%10, bir robotun hata yüzdesi, tek koşu sınırı, kapsama yüzdesindeki 10 puanlık fark veya istatistiksel eşdeğerlik değildir. Bu çalışma için kullanılan pratik tekrar değerlendirme eşiğidir; tarihsel sonuçlar görüldükten sonra benimsenmiştir. Yayın ortalaması görev başına 10 tasarımdan gelir; yeni çoklu-seed ortalaması, aynı 10 denetleyicinin yeniden değerlendirmesidir. 500 koşu, 500 yeni optimize edilmiş denetleyici demek değildir.

APC’de küçük ham puan, NC/CC’de büyük ham puan daha iyidir. APC ham ölçüsü uzaklık karesine dayanır; fiziksel uzaklık özeti istenirse her koşunun karekökü alındıktan sonra ortalama alınır. NC/CC ham puanı 1200 kontrol adımı boyunca biriken kapsama oranıdır; zaman ortalamalı kapsama yüzdesi için ham puanı 12’ye bölün. Kabul testi bu dönüşümlerden önce, tablodaki **ham ortalamalarla** yapılır.

Yeni deneyin normal kabul sonucu `ozet.json` içinde `all_successful: true` ve `below_10_percent_all_selected_cells: true` olmasıdır. Tam iki yöntem deneyinde `runs: 2100` beklenir. Her hücrede `full_cell: true`, `below_10_percent: true` olmalıdır. Komut başarılıysa çıkış kodu 0; başarısız koşu veya eşik aşımı varsa 2 döndürür. Ortam/kurulum hatalarında 1 döndürür.

## 7. Çıktılarda neyi inceleyeceksiniz?

| Dosya / dizin | İçerik |
|---|---|
| `runs/tam_01/ozet.json` | Altı hücrenin ortalamaları, yayın ve arşiv referansları, %10 kararları |
| `runs/tam_01/sonuclar.csv` | Her koşunun yöntemi, görevi, denetleyicisi, seed’i, puanı ve başarı durumu |
| `runs/tam_01/plan.json` | Çalışma planı ve değişiklik kontrolü için deney imzası |
| `runs/tam_01/records/` | Komut, profil, hash’ler, çıkış kodu ve süre içeren tekil koşu kayıtları |
| `runs/tam_01/configs/` | O koşuda gerçekten kullanılan XML dosyaları |
| `runs/tam_01/logs/` | Simülatörün ham çıktısı |
| `beklenen_sonuclar/` | Önceki 2.100 koşunun log/XML/JSON kayıtları, yayın tabloları, hedefler ve CSV özet |

Danışmana gönderirken `ozet.json`, `sonuclar.csv` ve `plan.json` dosyalarını verin. Hata varsa ilgili tekil JSON, XML ve logu da ekleyin. İlk çalıştırmada bu sayısal referans tamamlandıktan sonra LaykaSim2D’ye aktarım ve yeni deney tasarımına geçilebilir.

## 8. Kaynak kodları nereden alındı?

### 8.1. 01_Mate – FSM/PFSM tabanlı proje

Mate, davranış ve koşul modüllerinden oluşan olasılıksal sonlu durum makinelerini çalıştırır. Öğrenci bu aşamada `01_Mate/controllers/` altındaki görev başına 10 yayımlanmış FSM’yi değerlendirir. Okunabilir kaynak kodu `01_Mate/source/`, özgün deney XML’leri `01_Mate/configs/original/` altındadır. Derleme, değiştirilmeyen sürüm arşivini kullanır; bu okunabilir kopyada yapılan değişiklikler derlemeye kendiliğinden girmez.

- Kaynak depo: https://github.com/demiurge-project/ARGoS3-AutoMoDe
- Kullanılan etiket: https://github.com/demiurge-project/ARGoS3-AutoMoDe/tree/v1.0-mate
- Commit: `a08877310cb46abbf17c68f6152ee7ce333318ea`
- Sabit sürüm kaydı: https://doi.org/10.5281/zenodo.5893277
- Kaynak arşivi: `sources/ARGoS3-AutoMoDe-v1.0-mate.zip`

**Bu paketteki Mate profilleri:** APC ve CC’de ilk gerçek zemin ölçümü, beş örnekli filtre geçmişini doldurur (warm başlangıç). Bu, özgün başlangıç davranışına yapılmış açık bir müdahaledir; geçmiş makalenin aynen geri elde edildiği anlamına gelmez. NC’de özgün cold zemin başlangıcı ve robot kimliği/LED indeksiyle sıralanan kanonik kamera eklentisi kullanılır. NC’nin özgün `y >= 0.6` başlangıç bölgesi korunur; daha yakın sonuç veren alternatif bölge seçilmez. Kamera düzenlemesi gürültü örneklerinin LED’lere atanma sırasını ve blob sırasını değiştirir; davranışlar, FSM’ler ve amaç fonksiyonu değiştirilmez.

CC’de ilk beş FSM’yi beyaza, son beşi siyaha atama önceki denetimdeki açık varsayımdır. Beş beyaz/beş siyah dengesi tezde belirtilse de hangi FSM satırının hangi başlangıç rengine karşılık geldiği tarihsel simülasyon metadatasıyla doğrulanmamıştır. Bu atama tarihsel kesinlik olarak sunulmamalıdır.

### 8.2. 02_EvoSpace – YSA tabanlı proje

EvoSpace sabit yapılı sinir ağlarının ağırlıklarını evrimsel aramayla belirleyen yaklaşımdır. Bu pakette yeni ağırlık aramak yerine `02_EvoSpace/genomes/` altındaki yayımlanmış 30 ağırlık kümesi (görev başına 10) çalıştırılır. Genom dosyaları 0–9, ortak sonuç tablosundaki denetleyici satırları 1–10 numaralıdır. Okunabilir tam kaynak `02_EvoSpace/source/` altındadır. Depo adında NEAT bulunması, bu EvoSpace deneyinin ağ topolojisini NEAT ile evrimleştirdiği anlamına gelmez.

- Kaynak depo: https://github.com/demiurge-project/ARGoS3-NEAT
- Kullanılan etiket: https://github.com/demiurge-project/ARGoS3-NEAT/tree/v1.0-evspa
- Commit: `ab57a3fe2e80a54a912953f201542eef3132de63`
- Sabit EvoSpace sürüm kaydı: https://doi.org/10.5281/zenodo.5893320
- Kaynak arşivi: `sources/ARGoS3-NEAT-v1.0-evspa.zip`

Kod, yazarların ek materyalindeki `Code.tar.gz` paketinin `Mate/ARGoS3-NEAT` dizininden alınmış ve sabit EvoSpace sürümüyle önceki denetimde karşılaştırılmıştır. Kaynakların hash’leri `02_EvoSpace/source_sha256.json` içindedir. Özgün C++ yürütme mantığı ve genomlar değiştirilmez. XML’de eski kalan denetleyici kayıt adı çalışan `nn_rm_3Dot1_controller` adına uyarlanır, kütüphane yolları yenilenir ve grafik arayüz kaldırılır. CC’de XML’in rastgele başlangıç rengi politikası korunur. Genel sürüm ailesi DOI’si yerine yukarıdaki **sabit sürüm DOI’si** esas alınmalıdır.

### 8.3. Ortak makale, veri ve bağımlılıklar

- Makale: Mendiburu, F. J., Garzón Ramos, D., Morais, M. R. A., Lima, A. M. N. ve Birattari, M. (2022). *AutoMoDe-Mate: automatic off-line design of spatially-organizing behaviors for robot swarms*. Swarm and Evolutionary Computation, 74, 101118. https://doi.org/10.1016/j.swevo.2022.101118
- Resmî ek materyal, görev videoları, denetleyiciler ve yayın sonuçları: https://iridia.ulb.ac.be/supp/IridiaSupp2020-008/index.html
- Tam resmî kod paketi: https://iridia.ulb.ac.be/supp/IridiaSupp2020-008/docs/Code.tar.gz
- ARGoS beta48 sabit kaynak: https://doi.org/10.5281/zenodo.4889112
- e-puck 48 sabit kaynak: https://doi.org/10.5281/zenodo.4882715
- DAO: https://doi.org/10.5281/zenodo.5893406
- APC/NC/CC puanlayıcıları: https://doi.org/10.5281/zenodo.5893411
- Arşivlenmiş irace 2.2 kaynağı: https://doi.org/10.5281/zenodo.4888997

Bağımlılık arşivleri `sources/` içinde bulunduğu için kaynak derlemesi için yeniden depo indirmek gerekmez. URL, sürüm ve SHA-256 bilgileri `sources/manifest.json` ile iki projenin `kaynak.json` dosyalarındadır. Yayın sonuç tablolarında sütunlar sırasıyla Mate simülasyon, Mate gerçek robot, Chocolate simülasyon, Chocolate gerçek robot, EvoSpace simülasyon, EvoSpace gerçek robottur; bu kılavuz birinci ve beşinci sütunu karşılaştırır.

## 9. Sorun giderme

| Durum | Yapılacak işlem |
|---|---|
| Windows veya ARM ortamı hatası | Linux x86-64/WSL2 Ubuntu kullanın. Arşiv kontrolü için Linux gerekmez. |
| Boşluk/Türkçe karakter içeren yol | Paketi Linux ev dizininde boşluksuz ASCII bir konuma çıkarın; yeniden derleyin. |
| CMake 4 veya bulunamayan derleme aracı | CMake 3.x ve bölüm 1’deki araçları kurun. Gerekirse `--cmake /tam/yol/cmake` verin. |
| `lib...so` bulunamadı / denetleyici kaydı yok | XML’i elle açmak yerine ortak betiği kullanın; derleme loglarını ve `runtime/ogrenci_runtime.json` dosyasını inceleyin. |
| Kısa kontrolde `all_successful: false` | Tam deneye geçmeden ilgili logu ve seed/tick bildirimi alanlarını inceleyin. |
| Zaman aşımı | Çok yavaş bilgisayarda `--workers 1 --timeout 600` ile yeni çıktı dizininde deneyin; simülasyon süresini değiştirmeyin. |
| Önceki deneyle imza uyuşmuyor | Ayarlar/kod/ikili değişmiştir. Farklı `--out` kullanın; eski kayıtları yeni ortalamaya karıştırmayın. |
| Bütünlük hatası | ZIP’i yeniden temiz bir klasöre çıkarın. Girdi, FSM veya ağırlık dosyasını değiştirmeyin. |
| Ortalama %10 dışında | Koşu sayısını, profil tablosunu, CC politikasını, CMake/derleyici sürümünü ve logları kontrol edin. Sonucu koruyup danışmanla değerlendirin. Yakın puan elde etmek için seed, gürültü, amaç fonksiyonu veya başlangıç bölgesi seçmeyin. |

Özgün kamera uygulamasında LED ziyaret sırası bellek adresi sırasından etkilenebilir. Bu nedenle derleyici/eklenti/yükleme düzeni değişince aynı seed farklı davranışa gidebilir. NC için kanonik kamera kullanımı bu nedene yöneliktir; diğer hücrelerde özgün kamera korunur. Aynı dondurulmuş ikili ve aynı girdilerle yeniden koşunun log hassasiyetinde eşleşmesi beklenir; böyle bir birebir kontrol için %10 tolerans kullanılmaz.

## 10. Paket içeriği, değişiklikler ve lisanslar

| Yol | İçerik |
|---|---|
| `README.md`, `README.docx` | Aynı Türkçe çalıştırma kılavuzu |
| `calistir.py` | Ortak kurulum, kısa/tam deney, arşiv ve bütünlük kontrolü |
| `01_Mate/` | Mate kaynak kodu, FSM’ler, XML’ler ve kaynak kimliği |
| `02_EvoSpace/` | EvoSpace kaynak kodu, genomlar, derleme betiği ve kaynak kimliği |
| `sources/` | Değiştirilmemiş sürüm arşivleri ve bağımlılık manifesti |
| `betikler/`, `yamalar/` | Kaynak derlemesi ve açık profil eklentileri |
| `beklenen_sonuclar/` | 2.100 tarihsel koşu ve altı karşılaştırma hedefi |
| `kayitlar/` | Paket kökeni, kontrol raporu ve önceki Linux ortamı |
| `HASHES.sha256` | Dağıtılan bütün dosyaların SHA-256 manifesti |
| `runtime/`, `runs/` | Kurulum/deney sırasında sizin bilgisayarınızda oluşur |

Derleme için üç CMake uyumluluk düzenlemesi uygulanır: e-puck başlık önceliği, Qt yokken isteğe bağlı kamera GUI aracının atlanması ve ilgisiz Gianduja hedefinin kapatılması. APC/NC/CC puanlayıcıları değişmez. Mate’in warm başlangıcı ve NC’nin kanonik kamerası ayrı, açıkça etiketli çalışma eklentileridir; EvoSpace’e uygulanmaz. Önceki çalışma betikleri farklı klasörlerdeki mutlak yollara bağlı olduğundan bu dağıtım için ortak taşınabilir giriş betiği hazırlanmıştır.

Özgün projelerin lisans ve telif bildirimleri kaynaklarda/arşivlerde korunmuştur; bileşenler tek bir yeni lisans altında sunulmaz. Mate/EvoSpace, ARGoS, e-puck, DAO, görev puanlayıcıları ve irace’nin kendi koşullarını esas alın. irace kaynağı arşivde bulunur fakat R/irace kurulumu ve tam optimizasyon çalışması bu kılavuzun çalıştırma kapsamına dahil değildir. Makaledeki görev başına 10 tasarım ve tasarım başına 200.000 değerlendirmelik tam arama, burada yapılan hazır-denetleyici tekrar değerlendirmesinden ayrı bir iştir.
