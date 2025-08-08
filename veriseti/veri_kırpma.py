# =============================================================================
# UYDU GÖRÜNTÜSÜ KIRPMA SCRIPT'İ (NİHAİ VERSİYON)
#
# Bu script, belirtilen bir giriş klasöründeki ve tüm alt klasörlerindeki
# .TIF uydu görüntülerini, bir sınır dosyasına (GeoJSON/Shapefile) göre
# kırpar ve sonuçları yeni bir çıktı klasörüne kaydeder.
#
# Özellikler:
# - İç içe klasörlerde (recursive) arama yapar.
# - NoData değerlerini doğru şekilde işleyerek kırpma sonrası oluşan
#   siyah kenar (black border) sorununu önler.
# - Hata yönetimi içerir ve kullanıcıyı bilgilendirir.
# =============================================================================

import os
import glob
import geopandas as gpd
import rasterio
from rasterio.mask import mask

# --- AYARLAR BÖLÜMÜ ---
# Bu bölümdeki değişkenleri kendi klasör ve dosya adlarınıza göre düzenleyebilirsiniz.

# 1. Ham verilerin bulunduğu ana klasörün adı
input_folder = 'islenmemis_veri'

# 2. Kırpılmış verilerin kaydedileceği klasörün adı
output_folder = 'islenmis_veri'

# 3. Sınır dosyasının adı (Bu dosyanın script ile aynı dizinde olması beklenir)
aoi_file = 'meke_aoi.geojson'

# --- KOD BÖLÜMÜ (BURADAN SONRASINI DEĞİŞTİRMEYE GEREK YOK) ---

def main():
    """Ana script fonksiyonu"""
    print("="*50)
    print("Otomatik Uydu Görüntüsü Kırpma Script'i Başlatıldı")
    print("="*50)

    # Çıktı klasörünü oluştur (eğer mevcut değilse)
    os.makedirs(output_folder, exist_ok=True)
    print(f"Bilgi: Çıktı klasörü '{output_folder}' kontrol edildi/oluşturuldu.")

    try:
        # İlgi alanı (AOI) sınır dosyasını bir kez yükle
        aoi = gpd.read_file(aoi_file)
        print(f"Bilgi: İlgi alanı (AOI) dosyası '{aoi_file}' başarıyla yüklendi.")
    except Exception as e:
        print(f"HATA: '{aoi_file}' sınır dosyası bulunamadı veya okunamadı.")
        print(f"Lütfen dosyanın script ile aynı klasörde olduğundan emin olun.")
        print(f"Teknik Hata Detayı: {e}")
        return # Script'i sonlandır

    # Giriş klasöründeki ve tüm alt klasörlerindeki .tif ve .TIF uzantılı dosyaları bul
    print(f"Bilgi: '{input_folder}' klasörü ve tüm alt klasörleri taranıyor...")
    search_pattern_upper = os.path.join(input_folder, '**', '*.TIF')
    search_pattern_lower = os.path.join(input_folder, '**', '*.tif')
    
    tif_files = glob.glob(search_pattern_upper, recursive=True)
    tif_files.extend(glob.glob(search_pattern_lower, recursive=True))

    if not tif_files:
        print(f"UYARI: '{input_folder}' klasör yapısı içinde hiç .TIF veya .tif dosyası bulunamadı.")
        return

    print(f"Bilgi: Toplam {len(tif_files)} adet uydu görüntüsü bulundu. Kırpma işlemi başlıyor...")
    print("-"*50)

    # Bulunan her bir .TIF dosyası için döngü başlat
    for i, raster_path in enumerate(tif_files, 1):
        try:
            base_name = os.path.basename(raster_path)
            print(f"-> [{i}/{len(tif_files)}] İşleniyor: {base_name}")

            with rasterio.open(raster_path) as src:
                # Orijinal dosyanın NoData değerini al. Eğer yoksa 0 olarak kabul et.
                nodata_value = src.nodata if src.nodata is not None else 0
                
                # Sınır dosyasının projeksiyonunu (CRS), raster'ın projeksiyonu ile aynı yap
                aoi_reprojected = aoi.to_crs(src.crs)

                # Kırpma işlemini NoData değerini belirterek gerçekleştir
                out_image, out_transform = mask(src, aoi_reprojected.geometry, crop=True, nodata=nodata_value)
                out_meta = src.meta.copy()

            # Yeni, kırpılmış raster'ın metadata'sını (bilgilerini) güncelle
            out_meta.update({
                "driver": "GTiff",
                "height": out_image.shape[1],
                "width": out_image.shape[2],
                "transform": out_transform,
                "nodata": nodata_value  # NoData bilgisini metaveriye kalıcı olarak yaz
            })
            
            # Çıktı dosyasının adını ve tam yolunu oluştur
            new_filename = f"{os.path.splitext(base_name)[0]}_clipped.TIF"
            clipped_raster_path = os.path.join(output_folder, new_filename)

            # Yeni dosyayı diske kaydet
            with rasterio.open(clipped_raster_path, "w", **out_meta) as dest:
                dest.write(out_image)

            print(f"   Başarılı! Sonuç kaydedildi: {new_filename}")

        except Exception as e:
            print(f"   !!! HATA !!!: {base_name} dosyası işlenirken bir sorun oluştu.")
            print(f"   Teknik Hata Detayı: {e}")
    
    print("-"*50)
    print("Tüm işlemler başarıyla tamamlandı!")
    print(f"Kırpılmış dosyalarınızı '{output_folder}' klasöründe bulabilirsiniz.")
    print("="*50)


if __name__ == "__main__":
    main()