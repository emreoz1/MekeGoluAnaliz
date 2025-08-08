# 🌊 Meke Gölü Uzaktan Algılama Analizi

Bu proje, Konya ili Karapınar ilçesinde bulunan **Meke Gölü**'nün 1984-2023 yılları arasındaki kuruma sürecini uzaktan algılama teknikleri ile analiz etmektedir. Landsat uydu görüntüleri kullanılarak NDWI (Normalized Difference Water Index) ve NDVI (Normalized Difference Vegetation Index) hesaplamaları yapılmış, gölün alan, derinlik ve hacim değişimleri detaylı şekilde incelenmiştir.

## 📊 Proje Özeti

- **Analiz Dönemi:** 1984-2023 (39 yıl)
- **Veri Kaynağı:** Landsat 5, 7, 8 ve 9 uydu görüntüleri
- **Analiz Yöntemi:** NDWI ve NDVI indeksleri
- **Önemli Bulgu:** Gölün %100 kuruma süreci tespit edilmiştir

## 🛰️ Kullanılan Uydu Sistemleri

| Dönem | Uydu | Sensör | Spektral Bantlar |
|-------|------|--------|------------------|
| 1984-1995 | Landsat 4-5 | TM C2 L2 | GREEN (B2), RED (B3), NIR (B4) |
| 2000-2010 | Landsat 7 | ETM+ C2 L2 | GREEN (B2), RED (B3), NIR (B4) |
| 2010-2023 | Landsat 8-9 | OLI C2 L2 | GREEN (B3), RED (B4), NIR (B5) |

## 📁 Proje Yapısı

```
MekeGoluAnaliz/
├── 📄 main.py                          # Ana analiz modülü
├── 📄 yapayzeka_yorumlama.py           # AI destekli analiz yorumlama
├── 📂 veriseti/                        # Veri işleme modülleri
│   ├── 📄 veri_kırpma.py              # Uydu görüntülerini AOI'ye göre kırpma
│   ├── 📄 manuel_ndwi_ndvi_deger_bulucu.py  # Manuel interaktif analiz aracı
│   ├── 📄 otomatik_ndwi_ndvi_deger_bulucu.py # Otomatik toplu analiz
│   ├── 📄 meke_aoi.geojson            # Meke Gölü sınır dosyası
│   ├── 📂 islenmemis_veri/            # Ham Landsat görüntüleri (yıllara göre)
│   └── 📂 islenmis_veri/              # Kırpılmış ve işlenmiş görüntüler
├── 📂 analiz/                          # Analiz sonuçları ve raporlar
│   ├── 📄 ndwi_analiz.py              # NDWI tabanlı su alanı analizi
│   ├── 📄 ndwi_ndvi_analiz.py         # Kombine NDWI-NDVI analizi
│   ├── 📄 meke_golu_ai_yorumlama.md   # AI yorumlama raporu
│   ├── 📂 csv/                        # Analiz sonuç tabloları
│   │   ├── main_analiz_sonuclari.csv
│   │   ├── ndwi_analiz_sonuclari.csv
│   │   ├── ndwi_ndvi_analiz_sonuclari.csv
│   │   └── otomatik_ndwi_ndvi_deger_sonuclari.csv
│   └── 📂 grafik/                     # Görselleştirme ve grafikler
│       ├── 📄 grafik_olustur.py
│       ├── 🖼️ grafik_yillik_degisim.png
│       ├── 🖼️ grafik_aylik_karsilastirma.png
│       ├── 🖼️ grafik_mevsimsel_degisim.png
│       └── 🖼️ grafik_detayli_trend_analizi.png
└── 📄 README.md                       # Bu dosya
```

## 🔬 Analiz Metodolojisi

### 1. NDWI (Normalized Difference Water Index)
```
NDWI = (GREEN - NIR) / (GREEN + NIR)
```
- Su alanlarının tespiti için kullanılır
- NDWI > 0 değerleri su varlığını işaret eder

### 2. NDVI (Normalized Difference Vegetation Index)
```
NDVI = (NIR - RED) / (NIR + RED)
```
- Bitki örtüsü sağlığını değerlendirir
- NDVI < 0 değerleri vejetasyon olmayan alanları gösterir

### 3. Su Alanı Tespiti
Kombine yaklaşım: **NDWI > 0 VE NDVI < 0** koşulunu sağlayan pikseller su alanı olarak kabul edilir.

## 🚀 Kurulum ve Kullanım

### Gerekli Kütüphaneler
```bash
pip install rasterio geopandas pandas numpy matplotlib seaborn google-generativeai python-dotenv
```

### Kullanım Adımları

1. **Veri Hazırlama:**
   ```bash
   python veriseti/veri_kırpma.py
   ```
   Ham Landsat görüntülerini AOI sınırlarına göre kırpar.

2. **Otomatik Analiz:**
   ```bash
   python veriseti/otomatik_ndwi_ndvi_deger_bulucu.py
   ```
   Tüm kırpılmış görüntüler için NDWI/NDVI değerlerini hesaplar.

3. **Ana Analiz:**
   ```bash
   python main.py
   ```
   Su alanı, derinlik ve hacim hesaplamalarını yapar.

4. **Grafik Oluşturma:**
   ```bash
   python analiz/grafik/grafik_olustur.py
   ```
   Trend analizi grafiklerini oluşturur.

5. **AI Yorumlama (Opsiyonel):**
   ```bash
   python yapayzeka_yorumlama.py
   ```
   Google Gemini AI ile analiz sonuçlarını yorumlar.

## 📈 Temel Bulgular

| Yıl | Göl Alanı (km²) | Ortalama Derinlik (m) | Su Hacmi (milyon m³) |
|-----|-----------------|----------------------|---------------------|
| 1984 | 0.453 | 6.50 | 2.95 |
| 1990 | 0.503 | 7.06 | 3.56 |
| 2000 | 0.444 | 6.43 | 2.86 |
| 2010 | 0.181 | 4.36 | 1.24 |
| 2015 | 0.054 | 2.26 | 0.24 |
| 2020 | 0.007 | 0.73 | 0.01 |
| 2023 | 0.000 | 0.00 | 0.00 |

**Kritik Tespit:** Meke Gölü 2015 yılından itibaren hızlı kuruma sürecine girmiş ve 2023 yılı itibarıyla tamamen kurumuştur.

## 🎯 Proje Özellikleri

- ✅ Çoklu Landsat uydu desteği (5, 7, 8, 9)
- ✅ Otomatik bant haritalama sistemi
- ✅ Zamansal trend analizi (39 yıl)
- ✅ Çoklu derinlik tahmin modeli
- ✅ Interaktif manuel analiz aracı
- ✅ AI destekli sonuç yorumlama
- ✅ Kapsamlı görselleştirme sistemi
- ✅ NoData ve hata yönetimi

## 📊 Veri Kaynakları

- **Uydu Görüntüleri:** [USGS EarthExplorer](https://earthexplorer.usgs.gov/)
- **Ham Veri Seti:** [Kaggle - Konya Meke Maar Raw Images](https://www.kaggle.com/datasets/emreeoz/konya-meke-maar-raw-image)
- **Bant Bilgileri:** [USGS Landsat Band Designations](https://www.usgs.gov/faqs/what-are-band-designations-landsat-satellites)
- **Meke Gölü Hakkında:** [Doç. Dr. Fetullah Arık](https://www.jmo.org.tr/resimler/ekler/5a366e769b1cde8_ek.pdf)

## 🔧 Teknik Detaylar

### Piksel Çözünürlükleri
- **Landsat 5/7/8/9:** 30m × 30m (900 m² piksel alanı)

### Veri Kalitesi
- Bulutsuz görüntüler tercih edilmiştir
- Mayıs ve Eylül ayları (kuru/nemli dönem karşılaştırması)
- Yaklaşık 5 yıllık aralıklarla örnekleme

### Su Derinliği Tahmin Modelleri
1. **Doğrusal Model:** Basit orantısal ilişki
2. **Karekök Model:** Non-linear NDWI-derinlik ilişkisi  
3. **Logaritmik Model:** Doygun su alanları için
4. **NDWI Kalibreli Model:** Meke Gölü'ne özel kalibrasyonlu
5. **NDVI Destekli Model:** Vejetasyon etkisi dahil

## 📝 Lisans ve Kullanım

Bu proje akademik araştırma amaçlı geliştirilmiştir. Veri setleri USGS'den alınmış olup, kullanımları ilgili kurumların lisans şartlarına tabidir.

---

*Bu analiz, uzaktan algılama teknolojilerinin iklim değişikliği ve çevresel izleme uygulamalarındaki gücünü göstermektedir.*