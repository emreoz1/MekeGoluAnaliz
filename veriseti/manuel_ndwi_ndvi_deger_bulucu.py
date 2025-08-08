# =============================================================================
# İNTERAKTİF İKİLİ ANALİZ ARACI (NDWI & NDVI)
#
# Bu script, seçilen bir tarihe ait uydu görüntüsü için hem NDWI (Su)
# hem de NDVI (Bitki Örtüsü) haritalarını yan yana gösterir.
#
# Fareyi haritalar üzerinde gezdirerek, herhangi bir pikselin
# her iki indeks değerini de aynı anda görebilirsiniz.
# Bu, su ve kara ayrımını en doğru şekilde yapmanızı sağlar.
# =============================================================================

import rasterio
import numpy as np
import matplotlib.pyplot as plt
import os

# --- AYARLAR ---
# Analiz etmek istediğiniz tarihe ait bantların tam dosya yollarını buraya girin.
# Örnek olarak 1984 yılı Eylül ayı verilmiştir. Kendi dosyalarınızla değiştirin.

GREEN_BAND_PATH = 'veriseti/islenmis_veri/LT05_L2SP_176034_19840515_20200918_02_T1_SR_B2_clipped.TIF'
NIR_BAND_PATH = 'veriseti/islenmis_veri/LT05_L2SP_176034_19840515_20200918_02_T1_SR_B4_clipped.TIF'
RED_BAND_PATH = 'veriseti/islenmis_veri/LT05_L2SP_176034_19840515_20200918_02_T1_SR_B3_clipped.TIF'

# --- KOD BÖLÜMÜ ---

def interactive_dual_analysis():
    """Kullanıcının NDWI ve NDVI değerlerini interaktif olarak incelemesini sağlar."""
    
    print("İkili Analiz Aracı Başlatıldı...")
    
    # Dosyaların varlığını kontrol et
    required_files = [GREEN_BAND_PATH, RED_BAND_PATH, NIR_BAND_PATH]
    if not all(os.path.exists(f) for f in required_files):
        print("\nHATA: Belirtilen dosya yollarından en az biri bulunamadı!")
        print("Lütfen AYARLAR bölümündeki dosya yollarını kontrol edin.")
        return

    try:
        # Bantları oku ve NoData maskesini oluştur
        with rasterio.open(GREEN_BAND_PATH) as src:
            green = src.read(1); nodata_value = src.nodata if src.nodata is not None else 0
        with rasterio.open(RED_BAND_PATH) as src: red = src.read(1)
        with rasterio.open(NIR_BAND_PATH) as src: nir = src.read(1)
        
        nodata_mask = (green == nodata_value)

        # İndeksleri hesapla
        with np.errstate(divide='ignore', invalid='ignore'):
            # NDWI
            num_ndwi = green.astype(float) - nir.astype(float)
            den_ndwi = green.astype(float) + nir.astype(float)
            ndwi = np.where(den_ndwi == 0, 0, num_ndwi / den_ndwi)
            
            # NDVI
            num_ndvi = nir.astype(float) - red.astype(float)
            den_ndvi = nir.astype(float) + red.astype(float)
            ndvi = np.where(den_ndvi == 0, 0, num_ndvi / den_ndvi)

        # NoData alanlarını grafikte göstermemek için NaN (Not a Number) yap
        ndwi[nodata_mask] = np.nan
        ndvi[nodata_mask] = np.nan
        
        print("İndeksler hesaplandı. Grafik penceresi açılıyor...")
        
        # Yan yana iki grafik için bir figür ve eksenler oluştur
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        # --- Sol Grafik: NDWI ---
        im1 = ax1.imshow(ndwi, cmap='RdYlBu', vmin=-0.5, vmax=0.5)
        fig.colorbar(im1, ax=ax1, shrink=0.6).set_label('NDWI Değeri (Mavi=Su)')
        ax1.set_title('NDWI (Su İndeksi) Haritası')
        ax1.set_xticks([]) # Eksen çizgilerini gizle
        ax1.set_yticks([])

        # --- Sağ Grafik: NDVI ---
        im2 = ax2.imshow(ndvi, cmap='RdYlGn', vmin=-0.5, vmax=0.5)
        fig.colorbar(im2, ax=ax2, shrink=0.6).set_label('NDVI Değeri (Yeşil=Bitki)')
        ax2.set_title('NDVI (Bitki Örtüsü İndeksi) Haritası')
        ax2.set_xticks([])
        ax2.set_yticks([])

        # --- İnteraktif Kısım ---
        def format_coord(x, y):
            # Tıklanan koordinatları al
            col = int(x + 0.5)
            row = int(y + 0.5)
            
            # Koordinatların görüntü içinde olduğundan emin ol
            if 0 <= col < ndwi.shape[1] and 0 <= row < ndwi.shape[0]:
                # Hem NDWI hem de NDVI değerini al ve formatla
                val_ndwi = ndwi[row, col]
                val_ndvi = ndvi[row, col]
                return f'x={col}, y={row}  |  NDWI = {val_ndwi:.4f}  |  NDVI = {val_ndvi:.4f}'
            return f'x={col}, y={row}'

        # Bu fonksiyonu her iki grafiğe de ata
        ax1.format_coord = format_coord
        ax2.format_coord = format_coord
        
        fig.suptitle(f'İnteraktif Analiz - {os.path.basename(GREEN_BAND_PATH).split("_")[3]}', fontsize=16)
        plt.tight_layout(rect=[0, 0.03, 1, 0.95]) # Başlık için yer bırak
        plt.show()

    except Exception as e:
        print(f"\nBir hata oluştu: {e}")

if __name__ == '__main__':
    interactive_dual_analysis()