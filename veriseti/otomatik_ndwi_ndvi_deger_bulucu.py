# ===================================================================================
# OTOMATİK NDWI & NDVI DEĞER BULUCU
#
# Bu script, kırpılmış Landsat görüntülerinden NDWI ve NDVI değerlerini hesaplar.
# NDWI > 0 olan su alanlarını ve NDVI < 0 olan vejetasyon olmayan alanları bulur.
# Sonuçları yıllara göre gruplandırarak CSV dosyasına kaydeder.
# ===================================================================================

import os
import glob
import re
import rasterio
import numpy as np
import pandas as pd

# --- AYARLAR BÖLÜMÜ ---

# 1. Kırpılmış verilerin bulunduğu klasör
INPUT_FOLDER = 'veriseti/islenmis_veri'
# 2. Sonuçların kaydedileceği CSV dosyasının adı
OUTPUT_CSV = 'analiz/csv/otomatik_ndwi_ndvi_deger_sonuclari.csv'
# 3. Su olarak kabul edilecek NDWI eşik değeri (0'dan büyük)
NDWI_THRESHOLD = 0
# 4. Vejetasyon olmayan alan olarak kabul edilecek NDVI eşik değeri (0'dan küçük)
NDVI_THRESHOLD = 0

# --- BANT HARİTASI ---
# Farklı Landsat uyduları için doğru bant numaralarını tanımlayan sözlük
BAND_MAP = {
    'Landsat-5': {'GREEN': 'B2', 'RED': 'B3', 'NIR': 'B4'},
    'Landsat-7': {'GREEN': 'B2', 'RED': 'B3', 'NIR': 'B4'},
    'Landsat-8': {'GREEN': 'B3', 'RED': 'B4', 'NIR': 'B5'},
    'Landsat-9': {'GREEN': 'B3', 'RED': 'B4', 'NIR': 'B5'}
}

# --- YARDIMCI FONKSİYONLAR ---

def get_band_number_from_filename(filename):
    """Dosya adından bant numarasını çeker."""
    match = re.search(r'_B(\w+)_clipped', os.path.basename(filename), re.IGNORECASE)
    if match:
        return f"B{match.group(1).upper()}"
    return None

def get_date_and_satellite_from_filename(filename):
    """Dosya adından tarih ve uydu modelini çeker."""
    base_name = os.path.basename(filename)
    parts = base_name.split('_')
    
    satellite_model = None
    date_str = None
    
    if base_name.startswith('LC08'): satellite_model = 'Landsat-8'
    elif base_name.startswith('LC09'): satellite_model = 'Landsat-9'
    elif base_name.startswith('LE07'): satellite_model = 'Landsat-7'
    elif base_name.startswith('LT05'): satellite_model = 'Landsat-5'
    
    if satellite_model and len(parts) > 3:
        date_str = parts[3]
        
    return date_str, satellite_model

def get_year_from_date(date_str):
    """Tarih string'inden yılı çeker."""
    if date_str and len(date_str) >= 4:
        return date_str[:4]
    return None

# --- ANA ANALİZ FONKSİYONU ---

def main():
    """Ana script fonksiyonu"""
    print("="*60)
    print("Otomatik NDWI & NDVI Değer Bulucu Script'i Başlatıldı")
    print("="*60)

    # Kırpılmış TIF dosyalarını bul
    search_pattern = os.path.join(INPUT_FOLDER, '**', '*_clipped.TIF')
    clipped_files = glob.glob(search_pattern, recursive=True)

    if not clipped_files:
        print(f"HATA: '{INPUT_FOLDER}' klasöründe `_clipped.TIF` uzantılı dosya bulunamadı.")
        return

    # Dosyaları tarihe göre grupla
    grouped_files = {}
    for f in clipped_files:
        date, satellite = get_date_and_satellite_from_filename(f)
        if not date or not satellite:
            continue

        if date not in grouped_files:
            grouped_files[date] = {'files': {}, 'satellite': satellite}
        
        band = get_band_number_from_filename(f)
        if band:
            grouped_files[date]['files'][band] = f
    
    print(f"Bilgi: {len(grouped_files)} farklı tarih için görüntü gruplandı.")
    
    results = []
    
    # Her tarih için analiz yap
    for date, data in grouped_files.items():
        satellite = data['satellite']
        files = data['files']
        year = get_year_from_date(date)
        
        if not year:
            continue
            
        print(f"\n-> İşleniyor: Tarih={date}, Yıl={year}, Uydu={satellite}")
        
        # Uyduya göre doğru bant haritasını al
        satellite_bands = BAND_MAP.get(satellite)
        if not satellite_bands:
            print(f"   UYARI: {satellite} için bant haritası tanımlı değil. Atlanıyor.")
            continue

        # Gerekli bantların dosya yollarını al
        green_path = files.get(satellite_bands['GREEN'])
        red_path = files.get(satellite_bands['RED'])
        nir_path = files.get(satellite_bands['NIR'])
        
        if not (green_path and red_path and nir_path):
            print("   UYARI: Bu tarih için gerekli bantlardan biri eksik (Yeşil, Kırmızı, NIR). Atlanıyor.")
            continue
            
        try:
            # Bantları oku ve NoData maskesi oluştur
            with rasterio.open(green_path) as src:
                green = src.read(1)
                nodata_value = src.nodata if src.nodata is not None else 0
            with rasterio.open(red_path) as src: 
                red = src.read(1)
            with rasterio.open(nir_path) as src: 
                nir = src.read(1)
            
            nodata_mask = (green == nodata_value)

            # --- NDWI Hesabı (Yeşil - NIR) / (Yeşil + NIR) ---
            with np.errstate(divide='ignore', invalid='ignore'):
                ndwi_numerator = green.astype(float) - nir.astype(float)
                ndwi_denominator = green.astype(float) + nir.astype(float)
                ndwi = np.where(ndwi_denominator == 0, 0, ndwi_numerator / ndwi_denominator)

            # --- NDVI Hesabı (NIR - Kırmızı) / (NIR + Kırmızı) ---
            with np.errstate(divide='ignore', invalid='ignore'):
                ndvi_numerator = nir.astype(float) - red.astype(float)
                ndvi_denominator = nir.astype(float) + red.astype(float)
                ndvi = np.where(ndvi_denominator == 0, 0, ndvi_numerator / ndvi_denominator)
            
            # Su maskesi oluştur (NDWI > 0)
            water_mask = (ndwi > NDWI_THRESHOLD) & (~nodata_mask)
            
            # Vejetasyon olmayan alan maskesi oluştur (NDVI < 0)
            non_vegetation_mask = (ndvi < NDVI_THRESHOLD) & (~nodata_mask)
            
            # Kombine maske (hem su hem de vejetasyon olmayan)
            combined_mask = water_mask & non_vegetation_mask
            
            # Su durumu kontrolü
            has_water = np.sum(water_mask) > 0
            has_non_vegetation = np.sum(non_vegetation_mask) > 0
            has_combined = np.sum(combined_mask) > 0
            
            # Sonuç değişkenleri
            water_ndwi_min = water_ndwi_max = water_ndwi_mean = np.nan
            non_veg_ndvi_min = non_veg_ndvi_max = non_veg_ndvi_mean = np.nan
            combined_ndwi_min = combined_ndwi_max = combined_ndwi_mean = np.nan
            combined_ndvi_min = combined_ndvi_max = combined_ndvi_mean = np.nan
            
            # Su alanları için NDWI istatistikleri
            if has_water:
                water_ndwi_values = ndwi[water_mask]
                water_ndwi_min = np.min(water_ndwi_values)
                water_ndwi_max = np.max(water_ndwi_values)
                water_ndwi_mean = np.mean(water_ndwi_values)
            
            # Vejetasyon olmayan alanlar için NDVI istatistikleri
            if has_non_vegetation:
                non_veg_ndvi_values = ndvi[non_vegetation_mask]
                non_veg_ndvi_min = np.min(non_veg_ndvi_values)
                non_veg_ndvi_max = np.max(non_veg_ndvi_values)
                non_veg_ndvi_mean = np.mean(non_veg_ndvi_values)
            
            # Kombine alanlar için istatistikler
            if has_combined:
                combined_ndwi_values = ndwi[combined_mask]
                combined_ndvi_values = ndvi[combined_mask]
                combined_ndwi_min = np.min(combined_ndwi_values)
                combined_ndwi_max = np.max(combined_ndwi_values)
                combined_ndwi_mean = np.mean(combined_ndwi_values)
                combined_ndvi_min = np.min(combined_ndvi_values)
                combined_ndvi_max = np.max(combined_ndvi_values)
                combined_ndvi_mean = np.mean(combined_ndvi_values)
            
            print(f"   Su Alanları (NDWI>0): {np.sum(water_mask)} piksel")
            print(f"   Vejetasyon Olmayan (NDVI<0): {np.sum(non_vegetation_mask)} piksel")
            print(f"   Kombine Alan (NDWI>0 & NDVI<0): {np.sum(combined_mask)} piksel")
            
            if has_water:
                print(f"   Su NDWI Değerleri: Min={water_ndwi_min:.4f}, Max={water_ndwi_max:.4f}, Ort={water_ndwi_mean:.4f}")
            if has_non_vegetation:
                print(f"   Vej.Yok NDVI Değerleri: Min={non_veg_ndvi_min:.4f}, Max={non_veg_ndvi_max:.4f}, Ort={non_veg_ndvi_mean:.4f}")
            if has_combined:
                print(f"   Kombine NDWI: Min={combined_ndwi_min:.4f}, Max={combined_ndwi_max:.4f}, Ort={combined_ndwi_mean:.4f}")
                print(f"   Kombine NDVI: Min={combined_ndvi_min:.4f}, Max={combined_ndvi_max:.4f}, Ort={combined_ndvi_mean:.4f}")

            # Sonuçları listeye ekle
            results.append({
                'Yil': int(year),
                'Tarih': pd.to_datetime(date, format='%Y%m%d'),
                'Uydu': satellite,
                
                # Su alanları NDWI istatistikleri
                'Su_NDWI_Min': water_ndwi_min,
                'Su_NDWI_Max': water_ndwi_max,
                'Su_NDWI_Ortalama': water_ndwi_mean,
                'Su_Piksel_Sayisi': np.sum(water_mask),
                
                # Vejetasyon olmayan alanlar NDVI istatistikleri
                'VejYok_NDVI_Min': non_veg_ndvi_min,
                'VejYok_NDVI_Max': non_veg_ndvi_max,
                'VejYok_NDVI_Ortalama': non_veg_ndvi_mean,
                'VejYok_Piksel_Sayisi': np.sum(non_vegetation_mask),
                
                # Kombine alanlar istatistikleri
                'Kombine_NDWI_Min': combined_ndwi_min,
                'Kombine_NDWI_Max': combined_ndwi_max,
                'Kombine_NDWI_Ortalama': combined_ndwi_mean,
                'Kombine_NDVI_Min': combined_ndvi_min,
                'Kombine_NDVI_Max': combined_ndvi_max,
                'Kombine_NDVI_Ortalama': combined_ndvi_mean,
                'Kombine_Piksel_Sayisi': np.sum(combined_mask),
                
                # Durum bilgileri
                'Su_Durumu': 'Su Var' if has_water else 'Su Yok',
                'VejYok_Durumu': 'Var' if has_non_vegetation else 'Yok',
                'Kombine_Durumu': 'Var' if has_combined else 'Yok'
            })

        except Exception as e:
            print(f"   HATA: {date} tarihi işlenirken bir sorun oluştu. Hata: {e}")

    if not results:
        print("\nUYARI: Hiçbir veri işlenemedi.")
        return

    # Sonuçları bir Pandas DataFrame'e çevir ve sırala
    df = pd.DataFrame(results).sort_values(by=['Yil', 'Tarih']).reset_index(drop=True)
    
    # CSV dosyasına kaydet (virgülden sonra 5 ondalık basamak)
    df.to_csv(OUTPUT_CSV, index=False, decimal='.', sep=',', float_format='%.5f')
    
    print("\n" + "="*60)
    print("NDWI & NDVI Değer Analizi Tamamlandı!")
    print(f"Sonuçlar başarıyla '{OUTPUT_CSV}' dosyasına kaydedildi.")
    print("="*60)
    
    print("\nDetaylı Veriler (İlk 10 satır):")
    print(df.head(10))
    
    print("\n" + "="*60)
    print("YILLIK İSTATİSTİKLER")
    print("="*60)
    
    for year in sorted(df['Yil'].unique()):
        year_data = df[df['Yil'] == year]
        water_count = len(year_data[year_data['Su_Durumu'] == 'Su Var'])
        non_veg_count = len(year_data[year_data['VejYok_Durumu'] == 'Var'])
        combined_count = len(year_data[year_data['Kombine_Durumu'] == 'Var'])
        
        print(f"\n{year} Yılı (Toplam {len(year_data)} ölçüm):")
        print(f"  • Su olan ölçüm sayısı: {water_count}")
        print(f"  • Vejetasyon olmayan ölçüm sayısı: {non_veg_count}")
        print(f"  • Kombine alan olan ölçüm sayısı: {combined_count}")
        
        # Su alanları için istatistikler
        water_year_data = year_data[year_data['Su_Durumu'] == 'Su Var']
        if not water_year_data.empty:
            su_min = water_year_data['Su_NDWI_Min'].min()
            su_max = water_year_data['Su_NDWI_Max'].max()
            print(f"  • Su NDWI aralığı: {su_min:.4f} - {su_max:.4f}")
        
        # Vejetasyon olmayan alanlar için istatistikler
        non_veg_year_data = year_data[year_data['VejYok_Durumu'] == 'Var']
        if not non_veg_year_data.empty:
            vej_min = non_veg_year_data['VejYok_NDVI_Min'].min()
            vej_max = non_veg_year_data['VejYok_NDVI_Max'].max()
            print(f"  • Vej.Yok NDVI aralığı: {vej_min:.4f} - {vej_max:.4f}")
        
        # Kombine alanlar için istatistikler
        combined_year_data = year_data[year_data['Kombine_Durumu'] == 'Var']
        if not combined_year_data.empty:
            komb_ndwi_min = combined_year_data['Kombine_NDWI_Min'].min()
            komb_ndwi_max = combined_year_data['Kombine_NDWI_Max'].max()
            komb_ndvi_min = combined_year_data['Kombine_NDVI_Min'].min()
            komb_ndvi_max = combined_year_data['Kombine_NDVI_Max'].max()
            print(f"  • Kombine NDWI aralığı: {komb_ndwi_min:.4f} - {komb_ndwi_max:.4f}")
            print(f"  • Kombine NDVI aralığı: {komb_ndvi_min:.4f} - {komb_ndvi_max:.4f}")


if __name__ == "__main__":
    main()
