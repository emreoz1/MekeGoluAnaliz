# ===================================================================================
# MEKE GÖLÜ KURUMA ANALİZİ - NİHAİ SCRIPT
#
# Bu script, kırpılmış Landsat 5, 7 ve 8 görüntülerinden hem göl alanını (NDWI)
# hem de çevresindeki bitki örtüsü sağlığını (NDVI) hesaplar.
# Uydu modelini otomatik olarak tanır ve doğru bantları kullanır.
# Tüm sonuçları tek bir CSV dosyasına kaydeder.
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
OUTPUT_CSV = 'analiz/csv/ndwi_analiz_sonuclari.csv'
# 3. Su olarak kabul edilecek NDWI eşik değeri
NDWI_THRESHOLD = 0

# --- BANT HARİTASI ---
# Farklı Landsat uyduları için doğru bant numaralarını tanımlayan sözlük
BAND_MAP = {
    'Landsat-5': {'GREEN': 'B2', 'RED': 'B3', 'NIR': 'B4'},
    'Landsat-7': {'GREEN': 'B2', 'RED': 'B3', 'NIR': 'B4'},
    'Landsat-8': {'GREEN': 'B3', 'RED': 'B4', 'NIR': 'B5'},
    'Landsat-9': {'GREEN': 'B3', 'RED': 'B4', 'NIR': 'B5'}
    # Not: Sentinel-2 analizi yapılacaksa buraya eklenebilir.
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

def get_pixel_area_m2(satellite_name):
    """Uydu ismine göre bir pikselin alanını metrekare olarak döndürür."""
    if 'Landsat' in satellite_name:
        return 30 * 30
    # Gelecekte Sentinel eklenecek olursa diye
    elif 'Sentinel' in satellite_name:
        return 10 * 10
    return None

# --- ANA ANALİZ FONKSİYONU ---

def main():
    """Ana script fonksiyonu"""
    print("="*60)
    print("Meke Gölü Kuruma Analizi Script'i Başlatıldı (NDWI & NDVI)")
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
        
        print(f"\n-> İşleniyor: Tarih={date}, Uydu={satellite}")
        
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
            print("   UYARI: Bu tarih için gerekli Yeşil, Kırmızı veya NIR bantlarından biri eksik. Atlanıyor.")
            continue
            
        try:
            # Bantları oku ve NoData maskesi oluştur
            with rasterio.open(green_path) as src:
                green = src.read(1)
                nodata_value = src.nodata if src.nodata is not None else 0
            with rasterio.open(red_path) as src: red = src.read(1)
            with rasterio.open(nir_path) as src: nir = src.read(1)
            
            nodata_mask = (green == nodata_value)

            # --- NDWI ve Alan Hesabı ---
            with np.errstate(divide='ignore', invalid='ignore'):
                numerator = green.astype(float) - nir.astype(float)
                denominator = green.astype(float) + nir.astype(float)
                ndwi = np.where(denominator == 0, 0, numerator / denominator)
            
            water_mask = (ndwi > NDWI_THRESHOLD) & (~nodata_mask)
            water_pixel_count = np.sum(water_mask)
            pixel_area_m2 = get_pixel_area_m2(satellite)
            total_area_km2 = (water_pixel_count * pixel_area_m2) / 1_000_000
            print(f"   NDWI Sonucu: Göl alanı = {total_area_km2:.4f} km²")

            # --- NDVI ve Ortalama Değer Hesabı ---
            with np.errstate(divide='ignore', invalid='ignore'):
                numerator = nir.astype(float) - red.astype(float)
                denominator = nir.astype(float) + red.astype(float)
                ndvi = np.where(denominator == 0, 0, numerator / denominator)

            # Sadece geçerli piksellerin ortalamasını al
            ortalama_ndvi = np.mean(ndvi[~nodata_mask])
            print(f"   NDVI Sonucu: Ortalama bitki örtüsü sağlığı = {ortalama_ndvi:.4f}")

            # Sonuçları listeye ekle
            results.append({
                'Tarih': pd.to_datetime(date, format='%Y%m%d'),
                'Uydu': satellite,
                'Gol_Alani_km2': total_area_km2,
                'Ortalama_NDVI': ortalama_ndvi
            })

        except Exception as e:
            print(f"   HATA: {date} tarihi işlenirken bir sorun oluştu. Hata: {e}")

    if not results:
        print("\nUYARI: Hiçbir veri işlenemedi.")
        return

    # Sonuçları bir Pandas DataFrame'e çevir ve sırala
    df = pd.DataFrame(results).sort_values(by='Tarih').reset_index(drop=True)
    
    # CSV dosyasına kaydet
    df.to_csv(OUTPUT_CSV, index=False, decimal='.', sep=',')
    
    print("\n" + "="*60)
    print("Tüm Analizler Tamamlandı!")
    print(f"Sonuçlar başarıyla '{OUTPUT_CSV}' dosyasına kaydedildi.")
    print("="*60)
    print("\nCSV Dosyası Önizlemesi:\n")
    print(df.head())


if __name__ == "__main__":
    main()