# ===================================================================================
# MEKE GÖLÜ KURUMA ANALİZİ - GÜNCELLENMIŞ VERSİYON
#
# Bu script, otomatik NDWI & NDVI değer bulucu sonuçlarından yararlanarak
# gelişmiş su alanı hesaplaması yapar.
# ===================================================================================

import pandas as pd
import numpy as np

# --- AYARLAR BÖLÜMÜ ---
INPUT_CSV = 'analiz/csv/otomatik_ndwi_ndvi_deger_sonuclari.csv'
OUTPUT_CSV = 'analiz/csv/main_analiz_sonuclari.csv'

# Landsat pikseli için alan (30m x 30m)
PIXEL_AREA_M2 = 30 * 30  # 900 m²

# Su derinliği tahmin parametreleri (Meke Gölü için kalibre edilmiş - CSV verilerine göre güncellenmiş)
MAKSIMUM_DERINLIK = 12.0  # metre (tam su seviyesinde - Meke Gölü için gerçekçi)
MAKSIMUM_ALAN = 0.55  # km² (CSV verilerinden maksimum 0.53 km² görüldü, güvenlik payı ile)
MINIMUM_ALAN = 0.0  # km² (tamamen kurumuş durumda)

# NDWI-Derinlik ilişkisi için katsayılar (CSV verilerine göre ayarlanmış)
NDWI_MIN_DERINLIK = 0.01  # CSV'de minimum anlamlı NDWI değeri ~0.015
NDWI_MAX_DERINLIK = 0.15  # CSV'de maksimum NDWI değeri ~0.14

def dogrusal_derinlik_modeli(alan_km2):
    """
    Model 1: Doğrusal İlişki
    Basit orantı: Alan azaldıkça derinlik doğrusal olarak azalır
    Meke Gölü için optimizasyonlu
    """
    if alan_km2 <= MINIMUM_ALAN:
        return 0.0
    
    derinlik_orani = alan_km2 / MAKSIMUM_ALAN
    # Meke Gölü sığ bir göl olduğu için derinlik oranını daha konservatif yap
    tahmin_derinlik = MAKSIMUM_DERINLIK * derinlik_orani * 0.8  # %80 katsayı
    return max(0.0, tahmin_derinlik)

def karekok_derinlik_modeli(alan_km2):
    """
    Model 2: Karekök İlişkisi  
    Daha gerçekçi: Derinlik, alanın kareköküyle orantılı
    Meke Gölü'nün sığ havza karakteristiği için uyarlanmış
    """
    if alan_km2 <= MINIMUM_ALAN:
        return 0.0
        
    alan_orani = alan_km2 / MAKSIMUM_ALAN
    derinlik_orani = np.sqrt(alan_orani)
    # Meke Gölü için daha gerçekçi katsayı
    tahmin_derinlik = MAKSIMUM_DERINLIK * derinlik_orani * 0.7  # %70 katsayı
    return max(0.0, tahmin_derinlik)

def logaritmik_derinlik_modeli(alan_km2):
    """
    Model 3: Logaritmik İlişki
    Su seviyesi düştükçe exponansiyel azalma
    Meke Gölü'nün kuruyan göl karakteristiği için optimize edilmiş
    """
    if alan_km2 <= MINIMUM_ALAN:
        return 0.0
        
    # Minimum değer koruması
    alan_km2 = max(alan_km2, 0.001)
    
    # Logaritmik ölçekleme
    alan_orani = alan_km2 / MAKSIMUM_ALAN
    if alan_orani <= 0:
        return 0.0
        
    # Meke Gölü için daha yumuşak logaritmik dönüşüm
    log_orani = np.log10(alan_orani * 9 + 1) / np.log10(10)  # 0-1 arası normalize
    tahmin_derinlik = MAKSIMUM_DERINLIK * max(0, log_orani) * 0.6  # %60 katsayı
    return max(0.0, tahmin_derinlik)

def ndwi_derinlik_modeli(ndwi_degeri):
    """
    Model 4: NDWI-Derinlik İlişkisi
    NDWI değerine göre tahmini derinlik
    CSV verilerindeki NDWI aralığına göre kalibre edilmiş (0.01-0.15)
    """
    if pd.isna(ndwi_degeri) or ndwi_degeri < NDWI_MIN_DERINLIK:
        return 0.0
    
    if ndwi_degeri > NDWI_MAX_DERINLIK:
        ndwi_degeri = NDWI_MAX_DERINLIK
    
    # CSV verilerine göre normalize et ve derinliğe çevir
    normalize_ndwi = (ndwi_degeri - NDWI_MIN_DERINLIK) / (NDWI_MAX_DERINLIK - NDWI_MIN_DERINLIK)
    
    # Meke Gölü için NDWI-derinlik ilişkisini güçlendir (karekök ile)
    derinlik_orani = np.sqrt(normalize_ndwi)  # Doğrusal yerine karekök ilişkisi
    tahmini_derinlik = MAKSIMUM_DERINLIK * derinlik_orani * 0.9  # %90 katsayı
    
    return max(0.0, tahmini_derinlik)

def ndvi_derinlik_modeli(ndvi_degeri):
    """
    Model 5: NDVI-Derinlik İlişkisi
    Negatif NDVI değerleri su varlığını işaret eder
    Daha negatif = daha derin su
    """
    if pd.isna(ndvi_degeri):
        return 0.0
    
    # NDVI negatif değilse su yok demektir
    if ndvi_degeri >= 0:
        return 0.0
    
    # NDVI ne kadar negatifse o kadar derin su olabilir
    # CSV verilerinde -0.20 ile 0 arası değerler var
    ndvi_min = -0.20  # En negatif değer
    ndvi_max = 0.0    # Su sınırı
    
    if ndvi_degeri < ndvi_min:
        ndvi_degeri = ndvi_min
    
    # Normalize et (0-1 arası)
    normalize_ndvi = abs(ndvi_degeri) / abs(ndvi_min)
    
    # Derinlik tahmini (NDVI tek başına güvenilir değil, düşük ağırlık)
    tahmini_derinlik = MAKSIMUM_DERINLIK * normalize_ndvi * 0.4  # %40 katsayı
    
    return max(0.0, tahmini_derinlik)

def kombine_derinlik_hesapla(alan_km2, ndwi_degeri, ndvi_degeri):
    """
    Tüm modelleri kullanarak kombine derinlik tahmini
    
    Args:
        alan_km2: Göl alanı (km²)
        ndwi_degeri: NDWI değeri
        ndvi_degeri: NDVI değeri
    
    Returns:
        dict: Tüm model sonuçları ve ortalama
    """
    # Beş farklı model ile derinlik tahmini
    derinlik_dogrusal = dogrusal_derinlik_modeli(alan_km2)
    derinlik_karekok = karekok_derinlik_modeli(alan_km2)
    derinlik_logaritmik = logaritmik_derinlik_modeli(alan_km2)
    derinlik_ndwi = ndwi_derinlik_modeli(ndwi_degeri)
    derinlik_ndvi = ndvi_derinlik_modeli(ndvi_degeri)
    
    # Ağırlıklı ortalama (NDWI ve karekök modeline en fazla ağırlık)
    agirlikli_ortalama = (
        derinlik_dogrusal * 0.15 +     # Doğrusal model
        derinlik_karekok * 0.30 +      # Karekök model (ana model)
        derinlik_logaritmik * 0.10 +   # Logaritmik model
        derinlik_ndwi * 0.35 +         # NDWI model (en güvenilir)
        derinlik_ndvi * 0.10           # NDVI model (yardımcı)
    )
    
    # Basit ortalama
    basit_ortalama = (derinlik_dogrusal + derinlik_karekok + derinlik_logaritmik + derinlik_ndwi + derinlik_ndvi) / 5
    
    return {
        'dogrusal': round(derinlik_dogrusal, 2),
        'karekok': round(derinlik_karekok, 2),
        'logaritmik': round(derinlik_logaritmik, 2),
        'ndwi': round(derinlik_ndwi, 2),
        'ndvi': round(derinlik_ndvi, 2),
        'agirlikli_ortalama': round(agirlikli_ortalama, 2),
        'basit_ortalama': round(basit_ortalama, 2)
    }

def hacim_hesapla(alan_km2, ortalama_derinlik_m):
    """Hacim hesaplama (milyon m³)"""
    alan_m2 = alan_km2 * 1_000_000  # km² -> m²
    hacim_m3 = alan_m2 * ortalama_derinlik_m  # m³
    hacim_milyon_m3 = hacim_m3 / 1_000_000  # milyon m³
    return round(hacim_milyon_m3, 3)

def su_durumu_belirle(alan_km2, derinlik_m):
    """Su durumunu kategorize et - Meke Gölü için optimize edilmiş"""
    if alan_km2 == 0 or derinlik_m == 0:
        return "Kurumuş"
    elif alan_km2 < 0.05:  # 0.05 km²'den küçük
        return "Kritik Seviye"
    elif alan_km2 < 0.20:  # 0.20 km²'den küçük
        return "Düşük Seviye"
    elif alan_km2 < 0.35:  # 0.35 km²'den küçük
        return "Orta Seviye"
    else:
        return "Yüksek Seviye"

def main():
    """Ana analiz fonksiyonu"""
    print("="*60)
    print("Meke Gölü NDWI & NDVI Analizi - Güncellenmiş Versiyon")
    print("="*60)
    
    try:
        # Otomatik değer bulucu sonuçlarını yükle
        df = pd.read_csv(INPUT_CSV)
        df['Tarih'] = pd.to_datetime(df['Tarih'])
        
        print(f"✓ {len(df)} veri noktası yüklendi")
        
        # Yeni analiz sonuçları için liste
        results = []
        
        for index, row in df.iterrows():
            tarih = row['Tarih']
            uydu = row['Uydu']
            yil = row['Yil']
            
            # Su piksel sayısını al (kombine alan kullanıyoruz - hem NDWI>0 hem NDVI<0)
            su_piksel_sayisi = row['Kombine_Piksel_Sayisi']
            
            # Alan hesaplama (km²)
            if pd.isna(su_piksel_sayisi) or su_piksel_sayisi == 0:
                gol_alani_km2 = 0.0
            else:
                alan_m2 = su_piksel_sayisi * PIXEL_AREA_M2
                gol_alani_km2 = alan_m2 / 1_000_000  # m² -> km²
            
            # NDVI değerini al (kombine alanların ortalaması varsa onu, yoksa genel ortalama)
            if not pd.isna(row['Kombine_NDVI_Ortalama']):
                ortalama_ndvi = row['Kombine_NDVI_Ortalama']
            else:
                # Kombine alan yoksa, tüm vejetasyon olmayan alanların NDVI ortalamasını kullan
                if not pd.isna(row['VejYok_NDVI_Ortalama']):
                    ortalama_ndvi = row['VejYok_NDVI_Ortalama']
                else:
                    # Hiç vejetasyon olmayan alan yoksa 0 kabul et
                    ortalama_ndvi = 0.0
            
            # NDWI değerini al (kombine alanların ortalaması)
            if not pd.isna(row['Kombine_NDWI_Ortalama']):
                ortalama_ndwi = row['Kombine_NDWI_Ortalama']
            else:
                # Kombine alan yoksa, su alanlarının NDWI ortalamasını kullan
                if not pd.isna(row['Su_NDWI_Ortalama']):
                    ortalama_ndwi = row['Su_NDWI_Ortalama']
                else:
                    ortalama_ndwi = 0.0
            
            # Su derinliği tahmini (kombine modeller)
            derinlik_sonuclari = kombine_derinlik_hesapla(gol_alani_km2, ortalama_ndwi, ortalama_ndvi)
            tahmini_derinlik = derinlik_sonuclari['agirlikli_ortalama']
            
            # Hacim hesaplama
            hacim_milyon_m3 = hacim_hesapla(gol_alani_km2, tahmini_derinlik)
            
            # Su durumu belirleme
            su_seviye_durumu = su_durumu_belirle(gol_alani_km2, tahmini_derinlik)
            
            print(f"📅 {tarih.strftime('%Y-%m-%d')}: Piksel={su_piksel_sayisi}, Alan={gol_alani_km2:.4f} km², NDVI={ortalama_ndvi:.4f}, NDWI={ortalama_ndwi:.4f}")
            print(f"     Derinlik: D={derinlik_sonuclari['dogrusal']:.1f}m, K={derinlik_sonuclari['karekok']:.1f}m, L={derinlik_sonuclari['logaritmik']:.1f}m, NDWI={derinlik_sonuclari['ndwi']:.1f}m, NDVI={derinlik_sonuclari['ndvi']:.1f}m → Ort={tahmini_derinlik:.2f}m")
            print(f"     Hacim={hacim_milyon_m3:.3f} milyon m³, Durum={su_seviye_durumu}")
            
            # Sonuçları kaydet
            results.append({
                'Yil': yil,
                'Tarih': tarih,
                'Uydu': uydu,
                'Gol_Alani_km2': gol_alani_km2,
                'Ortalama_NDVI': ortalama_ndvi,
                'Ortalama_NDWI': ortalama_ndwi,
                'Derinlik_Dogrusal_m': derinlik_sonuclari['dogrusal'],
                'Derinlik_Karekok_m': derinlik_sonuclari['karekok'],
                'Derinlik_Logaritmik_m': derinlik_sonuclari['logaritmik'],
                'Derinlik_NDWI_m': derinlik_sonuclari['ndwi'],
                'Derinlik_NDVI_m': derinlik_sonuclari['ndvi'],
                'Tahmini_Derinlik_m': tahmini_derinlik,
                'Hacim_Milyon_m3': hacim_milyon_m3,
                'Su_Piksel_Sayisi': su_piksel_sayisi,
                'Kombine_Piksel_Sayisi': su_piksel_sayisi,
                'Su_Durumu': row['Su_Durumu'],
                'Kombine_Durumu': row['Kombine_Durumu'],
                'Su_Seviye_Durumu': su_seviye_durumu
            })
        
        # DataFrame oluştur ve kaydet
        result_df = pd.DataFrame(results)
        result_df = result_df.sort_values(by=['Yil', 'Tarih']).reset_index(drop=True)
        
        # CSV'ye kaydet
        result_df.to_csv(OUTPUT_CSV, index=False, decimal='.', sep=',')
        
        print("\n" + "="*60)
        print("✅ Analiz Tamamlandı!")
        print(f"Sonuçlar '{OUTPUT_CSV}' dosyasına kaydedildi.")
        print("="*60)
        
        # Özet istatistikler
        print("\n📊 ÖZET İSTATİSTİKLER:")
        print(f"• Toplam ölçüm sayısı: {len(result_df)}")
        su_var_count = len(result_df[result_df['Su_Durumu'] == 'Su Var'])
        su_yok_count = len(result_df[result_df['Su_Durumu'] == 'Su Yok'])
        print(f"• Su olan ölçüm sayısı: {su_var_count}")
        print(f"• Su olmayan ölçüm sayısı: {su_yok_count}")
        
        if len(result_df) > 0:
            print(f"• Maksimum göl alanı: {result_df['Gol_Alani_km2'].max():.4f} km²")
            print(f"• Minimum göl alanı: {result_df['Gol_Alani_km2'].min():.4f} km²")
            print(f"• Ortalama göl alanı: {result_df['Gol_Alani_km2'].mean():.4f} km²")
            print(f"• Maksimum tahmini derinlik: {result_df['Tahmini_Derinlik_m'].max():.2f} m")
            print(f"• Ortalama tahmini derinlik: {result_df['Tahmini_Derinlik_m'].mean():.2f} m")
            print(f"• Maksimum hacim: {result_df['Hacim_Milyon_m3'].max():.3f} milyon m³")
            print(f"• Ortalama hacim: {result_df['Hacim_Milyon_m3'].mean():.3f} milyon m³")
        
        print("\n📋 İlk 10 Sonuç:")
        print(result_df[['Yil', 'Tarih', 'Uydu', 'Gol_Alani_km2', 'Ortalama_NDWI', 'Tahmini_Derinlik_m', 'Hacim_Milyon_m3', 'Su_Seviye_Durumu']].head(10))
        
        # Yıllık trend analizi
        print("\n📈 YILLIK TREND ANALİZİ:")
        yillik_istatistik = result_df.groupby('Yil').agg({
            'Gol_Alani_km2': ['mean', 'max', 'min', 'count'],
            'Ortalama_NDVI': 'mean',
            'Ortalama_NDWI': 'mean',
            'Tahmini_Derinlik_m': ['mean', 'max'],
            'Hacim_Milyon_m3': ['mean', 'max']
        }).round(4)
        
        yillik_istatistik.columns = ['Ortalama_Alan_km2', 'Max_Alan_km2', 'Min_Alan_km2', 'Olcum_Sayisi', 'Ortalama_NDVI', 'Ortalama_NDWI', 'Ortalama_Derinlik_m', 'Max_Derinlik_m', 'Ortalama_Hacim_milyon_m3', 'Max_Hacim_milyon_m3']
        
        for yil, row in yillik_istatistik.iterrows():
            print(f"  {yil}: Alan Ort={row['Ortalama_Alan_km2']:.4f} km², Max={row['Max_Alan_km2']:.4f} km², Min={row['Min_Alan_km2']:.4f} km²")
            print(f"        NDVI Ort={row['Ortalama_NDVI']:.4f}, NDWI Ort={row['Ortalama_NDWI']:.4f}, Ölçüm={int(row['Olcum_Sayisi'])}")
            print(f"        Derinlik Ort={row['Ortalama_Derinlik_m']:.2f}m, Max Derinlik={row['Max_Derinlik_m']:.2f}m")
            print(f"        Hacim Ort={row['Ortalama_Hacim_milyon_m3']:.3f} milyon m³, Max Hacim={row['Max_Hacim_milyon_m3']:.3f} milyon m³")
        
        # Su durumu analizi
        print("\n🌊 SU DURUMU ANALİZİ (Yıllık):")
        su_durumu_yillik = result_df.groupby(['Yil', 'Su_Durumu']).size().unstack(fill_value=0)
        
        for yil in sorted(result_df['Yil'].unique()):
            if yil in su_durumu_yillik.index:
                su_var = su_durumu_yillik.loc[yil, 'Su Var'] if 'Su Var' in su_durumu_yillik.columns else 0
                su_yok = su_durumu_yillik.loc[yil, 'Su Yok'] if 'Su Yok' in su_durumu_yillik.columns else 0
                toplam = su_var + su_yok
                if toplam > 0:
                    su_var_yuzde = (su_var / toplam) * 100
                    print(f"  {yil}: Su Var={su_var}, Su Yok={su_yok} | Su Var Oranı: %{su_var_yuzde:.1f}")
        
        # En büyük ve en küçük alan kayıtları
        print("\n🏆 EKSTREM DEĞERLER:")
        max_alan_row = result_df.loc[result_df['Gol_Alani_km2'].idxmax()]
        min_alan_row = result_df.loc[result_df['Gol_Alani_km2'].idxmin()]
        max_derinlik_row = result_df.loc[result_df['Tahmini_Derinlik_m'].idxmax()]
        max_hacim_row = result_df.loc[result_df['Hacim_Milyon_m3'].idxmax()]
        
        print(f"• En büyük göl alanı: {max_alan_row['Gol_Alani_km2']:.4f} km² ({max_alan_row['Tarih'].strftime('%Y-%m-%d')})")
        print(f"• En küçük göl alanı: {min_alan_row['Gol_Alani_km2']:.4f} km² ({min_alan_row['Tarih'].strftime('%Y-%m-%d')})")
        print(f"• En derin su tahmini: {max_derinlik_row['Tahmini_Derinlik_m']:.2f} m ({max_derinlik_row['Tarih'].strftime('%Y-%m-%d')}, NDWI={max_derinlik_row['Ortalama_NDWI']:.3f})")
        print(f"• En büyük hacim: {max_hacim_row['Hacim_Milyon_m3']:.3f} milyon m³ ({max_hacim_row['Tarih'].strftime('%Y-%m-%d')})")
        
        # Derinlik modelleri karşılaştırması
        print("\n🔬 DERİNLİK MODELLERİ KARŞILAŞTIRMASI:")
        model_ortalamalar = {
            'Doğrusal Model': result_df['Derinlik_Dogrusal_m'].mean(),
            'Karekök Model': result_df['Derinlik_Karekok_m'].mean(),
            'Logaritmik Model': result_df['Derinlik_Logaritmik_m'].mean(),
            'NDWI Model': result_df['Derinlik_NDWI_m'].mean(),
            'NDVI Model': result_df['Derinlik_NDVI_m'].mean(),
            'Kombine Model': result_df['Tahmini_Derinlik_m'].mean()
        }
        
        for model, ortalama in model_ortalamalar.items():
            print(f"  • {model}: {ortalama:.2f} m ortalama")
        
        # Derinlik kategorileri analizi
        print("\n🌊 DERİNLİK KATEGORİLERİ:")
        result_df['Derinlik_Kategorisi'] = pd.cut(
            result_df['Tahmini_Derinlik_m'], 
            bins=[0, 2, 5, 10, float('inf')], 
            labels=['Sığ (0-2m)', 'Orta (2-5m)', 'Derin (5-10m)', 'Çok Derin (>10m)'],
            include_lowest=True
        )
        
        derinlik_dagilimi = result_df['Derinlik_Kategorisi'].value_counts()
        for kategori, sayi in derinlik_dagilimi.items():
            yuzde = (sayi / len(result_df)) * 100
            print(f"  {kategori}: {sayi} ölçüm (%{yuzde:.1f})")
        
        # Su seviye durumu analizi
        print("\n💧 SU SEVİYE DURUMU DAĞILIMI:")
        seviye_dagilimi = result_df['Su_Seviye_Durumu'].value_counts()
        for seviye, sayi in seviye_dagilimi.items():
            yuzde = (sayi / len(result_df)) * 100
            print(f"  {seviye}: {sayi} ölçüm (%{yuzde:.1f})")
        
    except FileNotFoundError:
        print(f"❌ HATA: '{INPUT_CSV}' dosyası bulunamadı.")
        print("Lütfen 'otomatik_ndwi_ndvi_deger_bulucu.py' scriptini önce çalıştırdığınızdan emin olun.")
    except Exception as e:
        print(f"❌ HATA: {e}")

if __name__ == "__main__":
    main()
