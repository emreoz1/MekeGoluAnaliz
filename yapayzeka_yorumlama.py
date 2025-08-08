# ===================================================================================
# MEKE GÖLÜ KURUMA ANALİZİ - YAPAY ZEKA YORUMLAMA
#
# Bu script, analiz sonuçlarını Gemini AI ile yorumlar ve 
# Meke Gölü'nün neden kuruduğuna dair bilimsel açıklamalar sunar.
# ===================================================================================

import pandas as pd
import numpy as np
import google.generativeai as genai
import os
from dotenv import load_dotenv
import json
from datetime import datetime

# .env.local dosyasını yükle
load_dotenv('.env.local')

# Gemini API yapılandırması
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY or GEMINI_API_KEY == 'your_gemini_api_key_here':
    print("❌ HATA: Gemini API key bulunamadı!")
    print("Lütfen .env.local dosyasında GEMINI_API_KEY değerini güncelleyin.")
    exit(1)

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-pro')

# Dosya yolları
CSV_DOSYASI = 'analiz/csv/main_analiz_sonuclari.csv'
CIKTI_DOSYASI = 'analiz/meke_golu_ai_yorumlama.md'

def csv_verilerini_yukle():
    """CSV dosyasını yükle ve temel istatistikleri hesapla"""
    try:
        df = pd.read_csv(CSV_DOSYASI)
        df['Tarih'] = pd.to_datetime(df['Tarih'])
        
        print(f"✓ {len(df)} veri noktası yüklendi")
        print(f"✓ Tarih aralığı: {df['Tarih'].min().strftime('%Y-%m-%d')} - {df['Tarih'].max().strftime('%Y-%m-%d')}")
        
        return df
    except FileNotFoundError:
        print(f"❌ HATA: '{CSV_DOSYASI}' dosyası bulunamadı.")
        return None
    except Exception as e:
        print(f"❌ HATA: {e}")
        return None

def veri_analizi_hazirla(df):
    """Detaylı veri analizi ve istatistikler hazırla"""
    
    # Temel istatistikler
    analiz = {
        'genel_bilgiler': {
            'toplam_olcum': len(df),
            'baslangic_tarihi': df['Tarih'].min().strftime('%Y-%m-%d'),
            'bitis_tarihi': df['Tarih'].max().strftime('%Y-%m-%d'),
            'analiz_suresi_yil': (df['Tarih'].max() - df['Tarih'].min()).days / 365.25
        },
        
        'gol_alani_degisimi': {
            'maksimum_alan_km2': float(df['Gol_Alani_km2'].max()),
            'minimum_alan_km2': float(df['Gol_Alani_km2'].min()),
            'ortalama_alan_km2': float(df['Gol_Alani_km2'].mean()),
            'alan_kaybi_orani': float((df['Gol_Alani_km2'].max() - df['Gol_Alani_km2'].min()) / df['Gol_Alani_km2'].max() * 100),
            'max_alan_tarihi': df.loc[df['Gol_Alani_km2'].idxmax(), 'Tarih'].strftime('%Y-%m-%d'),
            'min_alan_tarihi': df.loc[df['Gol_Alani_km2'].idxmin(), 'Tarih'].strftime('%Y-%m-%d')
        },
        
        'su_derinligi_degisimi': {
            'maksimum_derinlik_m': float(df['Tahmini_Derinlik_m'].max()),
            'minimum_derinlik_m': float(df['Tahmini_Derinlik_m'].min()),
            'ortalama_derinlik_m': float(df['Tahmini_Derinlik_m'].mean()),
            'derinlik_kaybi_orani': float((df['Tahmini_Derinlik_m'].max() - df['Tahmini_Derinlik_m'].min()) / df['Tahmini_Derinlik_m'].max() * 100),
            'max_derinlik_tarihi': df.loc[df['Tahmini_Derinlik_m'].idxmax(), 'Tarih'].strftime('%Y-%m-%d'),
            'min_derinlik_tarihi': df.loc[df['Tahmini_Derinlik_m'].idxmin(), 'Tarih'].strftime('%Y-%m-%d')
        },
        
        'su_hacmi_degisimi': {
            'maksimum_hacim_milyon_m3': float(df['Hacim_Milyon_m3'].max()),
            'minimum_hacim_milyon_m3': float(df['Hacim_Milyon_m3'].min()),
            'ortalama_hacim_milyon_m3': float(df['Hacim_Milyon_m3'].mean()),
            'hacim_kaybi_orani': float((df['Hacim_Milyon_m3'].max() - df['Hacim_Milyon_m3'].min()) / df['Hacim_Milyon_m3'].max() * 100),
            'max_hacim_tarihi': df.loc[df['Hacim_Milyon_m3'].idxmax(), 'Tarih'].strftime('%Y-%m-%d'),
            'min_hacim_tarihi': df.loc[df['Hacim_Milyon_m3'].idxmin(), 'Tarih'].strftime('%Y-%m-%d')
        },
        
        'ndvi_ndwi_analizi': {
            'ortalama_ndvi': float(df['Ortalama_NDVI'].mean()),
            'ortalama_ndwi': float(df['Ortalama_NDWI'].mean()),
            'maksimum_ndvi': float(df['Ortalama_NDVI'].max()),
            'maksimum_ndwi': float(df['Ortalama_NDWI'].max()),
            'minimum_ndvi': float(df['Ortalama_NDVI'].min()),
            'minimum_ndwi': float(df['Ortalama_NDWI'].min())
        }
    }
    
    # Yıllık trend analizi
    yillik_analiz = df.groupby('Yil').agg({
        'Gol_Alani_km2': ['mean', 'max', 'min'],
        'Tahmini_Derinlik_m': ['mean', 'max', 'min'],
        'Hacim_Milyon_m3': ['mean', 'max', 'min'],
        'Ortalama_NDVI': 'mean',
        'Ortalama_NDWI': 'mean'
    }).round(4)
    
    analiz['yillik_trend'] = {}
    for yil in sorted(df['Yil'].unique()):
        yil_data = df[df['Yil'] == yil]
        analiz['yillik_trend'][str(yil)] = {
            'ortalama_alan_km2': float(yil_data['Gol_Alani_km2'].mean()),
            'maksimum_alan_km2': float(yil_data['Gol_Alani_km2'].max()),
            'minimum_alan_km2': float(yil_data['Gol_Alani_km2'].min()),
            'ortalama_derinlik_m': float(yil_data['Tahmini_Derinlik_m'].mean()),
            'ortalama_hacim_milyon_m3': float(yil_data['Hacim_Milyon_m3'].mean()),
            'ortalama_ndvi': float(yil_data['Ortalama_NDVI'].mean()),
            'ortalama_ndwi': float(yil_data['Ortalama_NDWI'].mean()),
            'olcum_sayisi': len(yil_data)
        }
    
    # Su durumu analizi
    su_durumu_analizi = df['Su_Seviye_Durumu'].value_counts()
    analiz['su_durumu_dagilimi'] = {}
    for durum, sayi in su_durumu_analizi.items():
        yuzde = (sayi / len(df)) * 100
        analiz['su_durumu_dagilimi'][durum] = {
            'sayi': int(sayi),
            'yuzde': float(yuzde)
        }
    
    # Kritik dönemler
    kritik_donemler = df[df['Su_Seviye_Durumu'].isin(['Kritik Seviye', 'Kurumuş'])]
    analiz['kritik_donemler'] = {
        'toplam_kritik_olcum': len(kritik_donemler),
        'kritik_donem_baslangici': kritik_donemler['Tarih'].min().strftime('%Y-%m-%d') if len(kritik_donemler) > 0 else 'Yok',
        'tam_kuruma_tarihi': df[df['Su_Seviye_Durumu'] == 'Kurumuş']['Tarih'].min().strftime('%Y-%m-%d') if len(df[df['Su_Seviye_Durumu'] == 'Kurumuş']) > 0 else 'Yok'
    }
    
    return analiz

def gemini_ile_analiz_et(analiz_verileri):
    """Gemini AI ile veri analizi ve yorumlama"""
    
    # Analiz verilerini JSON formatında hazırla
    veri_json = json.dumps(analiz_verileri, indent=2, ensure_ascii=False)
    
    prompt = f"""
Aşağıdaki Meke Gölü analiz verilerini detaylı olarak yorumla ve neden kuruduğunu bilimsel açıklamalarla anlat:

{veri_json}

Lütfen aşağıdaki konuları kapsamlı olarak ele al:

1. **MEKE GÖLÜ'NÜN KURUMA SÜRECİ**
   - 1984-2023 dönemindeki değişim analizi
   - Kritik kırılma noktaları ve dönemler
   - Kuruma hızı ve trendi

2. **KURUMA NEDENLERİ**
   - İklim değişikliği etkisi
   - Yağış rejimi değişiklikleri
   - Sıcaklık artışı ve buharlaşma
   - Antropojenik (insan kaynaklı) etkiler
   - Jeolojik faktörler

3. **VERİ ANALİZİ YORUMLARI**
   - NDVI değerlerinin anlamı (vejetasyon durumu)
   - NDWI değerlerinin anlamı (su varlığı)
   - Alan-derinlik-hacim ilişkileri
   - Mevsimsel değişimler

4. **EKOLOJİK VE ÇEVRESEL ETKİLER**
   - Ekosistem kaybı
   - Biyoçeşitlilik üzerindeki etkiler
   - Bölgesel mikroiklim değişiklikleri
   - Çevresel sonuçlar

5. **GELECEKTEKİ PROJEKSIYONLAR VE ÖNERİLER**
   - Mevcut trend devam ederse ne olur?
   - Rehabilitasyon imkânları
   - Koruma stratejileri
   - Su kaynaklarını koruma önerileri

Yanıtı Türkçe olarak, bilimsel ama anlaşılır bir dille ve Markdown formatında ver. Her bölümü detaylı açıkla ve sayısal verilerle destekle.
"""

    try:
        print("🤖 Gemini AI analiz yapıyor...")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"❌ Gemini API hatası: {e}")
        return None

def rapor_olustur(analiz_verileri, ai_yorumlama):
    """Detaylı analiz raporu oluştur"""
    
    # Tarih bilgisi
    tarih = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Rapor içeriği
    rapor = f"""# MEKE GÖLÜ KURUMA ANALİZİ - YAPAY ZEKA YORUMLAMA RAPORU

📅 **Rapor Tarihi:** {tarih}  
🤖 **Analiz Modeli:** Google Gemini 2.5 Pro  
📊 **Veri Kaynağı:** Landsat Uydu Görüntüleri (1984-2023)  

---

## 📋 ANALİZ ÖZETİ

### Temel İstatistikler
- **Analiz Dönemi:** {analiz_verileri['genel_bilgiler']['baslangic_tarihi']} - {analiz_verileri['genel_bilgiler']['bitis_tarihi']}
- **Toplam Ölçüm:** {analiz_verileri['genel_bilgiler']['toplam_olcum']} veri noktası
- **Analiz Süresi:** {analiz_verileri['genel_bilgiler']['analiz_suresi_yil']:.1f} yıl

### Göl Alanı Değişimi
- **Maksimum Alan:** {analiz_verileri['gol_alani_degisimi']['maksimum_alan_km2']:.4f} km² ({analiz_verileri['gol_alani_degisimi']['max_alan_tarihi']})
- **Minimum Alan:** {analiz_verileri['gol_alani_degisimi']['minimum_alan_km2']:.4f} km² ({analiz_verileri['gol_alani_degisimi']['min_alan_tarihi']})
- **Alan Kaybı:** %{analiz_verileri['gol_alani_degisimi']['alan_kaybi_orani']:.1f}

### Su Derinliği Değişimi
- **Maksimum Derinlik:** {analiz_verileri['su_derinligi_degisimi']['maksimum_derinlik_m']:.2f} m ({analiz_verileri['su_derinligi_degisimi']['max_derinlik_tarihi']})
- **Minimum Derinlik:** {analiz_verileri['su_derinligi_degisimi']['minimum_derinlik_m']:.2f} m ({analiz_verileri['su_derinligi_degisimi']['min_derinlik_tarihi']})
- **Derinlik Kaybı:** %{analiz_verileri['su_derinligi_degisimi']['derinlik_kaybi_orani']:.1f}

### Su Hacmi Değişimi
- **Maksimum Hacim:** {analiz_verileri['su_hacmi_degisimi']['maksimum_hacim_milyon_m3']:.3f} milyon m³ ({analiz_verileri['su_hacmi_degisimi']['max_hacim_tarihi']})
- **Minimum Hacim:** {analiz_verileri['su_hacmi_degisimi']['minimum_hacim_milyon_m3']:.3f} milyon m³ ({analiz_verileri['su_hacmi_degisimi']['min_hacim_tarihi']})
- **Hacim Kaybı:** %{analiz_verileri['su_hacmi_degisimi']['hacim_kaybi_orani']:.1f}

---

## 🔬 YILLIK TREND ANALİZİ

"""
    
    # Yıllık trend tablosu
    rapor += "| Yıl | Ortalama Alan (km²) | Ortalama Derinlik (m) | Ortalama Hacim (milyon m³) | Ortalama NDVI | Ortalama NDWI |\n"
    rapor += "|-----|--------------------|-----------------------|---------------------------|---------------|---------------|\n"
    
    for yil, veri in analiz_verileri['yillik_trend'].items():
        rapor += f"| {yil} | {veri['ortalama_alan_km2']:.4f} | {veri['ortalama_derinlik_m']:.2f} | {veri['ortalama_hacim_milyon_m3']:.3f} | {veri['ortalama_ndvi']:.4f} | {veri['ortalama_ndwi']:.4f} |\n"
    
    rapor += f"""

---

## 💧 SU DURUMU DAĞILIMI

"""
    
    # Su durumu dağılımı
    for durum, veri in analiz_verileri['su_durumu_dagilimi'].items():
        rapor += f"- **{durum}:** {veri['sayi']} ölçüm (%{veri['yuzde']:.1f})\n"
    
    rapor += f"""

---

## ⚠️ KRİTİK DÖNEMLER

- **Kritik Dönem Başlangıcı:** {analiz_verileri['kritik_donemler']['kritik_donem_baslangici']}
- **Tam Kuruma Tarihi:** {analiz_verileri['kritik_donemler']['tam_kuruma_tarihi']}
- **Toplam Kritik Ölçüm:** {analiz_verileri['kritik_donemler']['toplam_kritik_olcum']}

---

## 🤖 YAPAY ZEKA YORUMLAMA

{ai_yorumlama}

---

## 📊 RAW DATA SUMMARY

### NDVI/NDWI Analizi
- **Ortalama NDVI:** {analiz_verileri['ndvi_ndwi_analizi']['ortalama_ndvi']:.4f}
- **Ortalama NDWI:** {analiz_verileri['ndvi_ndwi_analizi']['ortalama_ndwi']:.4f}
- **NDVI Aralığı:** {analiz_verileri['ndvi_ndwi_analizi']['minimum_ndvi']:.4f} - {analiz_verileri['ndvi_ndwi_analizi']['maksimum_ndvi']:.4f}
- **NDWI Aralığı:** {analiz_verileri['ndvi_ndwi_analizi']['minimum_ndwi']:.4f} - {analiz_verileri['ndvi_ndwi_analizi']['maksimum_ndwi']:.4f}

---

**Bu rapor, Landsat uydu görüntüleri kullanılarak 1984-2023 döneminde Meke Gölü'nün su seviyesi, alanı, derinliği ve hacmindeki değişimler analiz edilerek, Google Gemini 2.5 Pro yapay zeka modeli ile yorumlanmıştır.**
"""
    
    return rapor

def main():
    """Ana çalıştırma fonksiyonu"""
    print("="*70)
    print("MEKE GÖLÜ YAPAY ZEKA YORUMLAMA ANALİZİ")
    print("="*70)
    
    # 1. CSV verilerini yükle
    print("\n📂 Veri yükleniyor...")
    df = csv_verilerini_yukle()
    if df is None:
        return
    
    # 2. Veri analizi hazırla
    print("\n📊 Veri analizi hazırlanıyor...")
    analiz_verileri = veri_analizi_hazirla(df)
    
    # 3. Gemini AI ile analiz et
    print("\n🤖 Yapay zeka analizi başlatılıyor...")
    ai_yorumlama = gemini_ile_analiz_et(analiz_verileri)
    
    if ai_yorumlama is None:
        print("❌ AI analizi başarısız!")
        return
    
    # 4. Rapor oluştur
    print("\n📄 Rapor hazırlanıyor...")
    rapor = rapor_olustur(analiz_verileri, ai_yorumlama)
    
    # 5. Raporu kaydet
    try:
        with open(CIKTI_DOSYASI, 'w', encoding='utf-8') as f:
            f.write(rapor)
        
        print(f"\n✅ Analiz tamamlandı!")
        print(f"📁 Rapor dosyası: {CIKTI_DOSYASI}")
        print(f"📏 Rapor uzunluğu: {len(rapor):,} karakter")
        
        # Özet bilgiler
        print(f"\n📋 ANALİZ ÖZETİ:")
        print(f"• Analiz Dönemi: {analiz_verileri['genel_bilgiler']['baslangic_tarihi']} - {analiz_verileri['genel_bilgiler']['bitis_tarihi']}")
        print(f"• Toplam Veri: {analiz_verileri['genel_bilgiler']['toplam_olcum']} ölçüm")
        print(f"• Alan Kaybı: %{analiz_verileri['gol_alani_degisimi']['alan_kaybi_orani']:.1f}")
        print(f"• Hacim Kaybı: %{analiz_verileri['su_hacmi_degisimi']['hacim_kaybi_orani']:.1f}")
        
        if analiz_verileri['kritik_donemler']['tam_kuruma_tarihi'] != 'Yok':
            print(f"• İlk Tam Kuruma: {analiz_verileri['kritik_donemler']['tam_kuruma_tarihi']}")
        
        print("\n" + "="*70)
        
    except Exception as e:
        print(f"❌ Rapor kaydetme hatası: {e}")

if __name__ == "__main__":
    main()