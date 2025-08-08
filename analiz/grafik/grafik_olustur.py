# ===================================================================================
# MEKE GÖLÜ ANALİZ GRAFİKLERİ
#
# Bu script, main_analiz_sonuclari.csv dosyasından alınan verilerle
# su derinliği ve hacim değişimlerini görselleştirir.
# ===================================================================================

import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Türkçe karakter desteği için
plt.rcParams['font.family'] = ['Arial Unicode MS', 'DejaVu Sans', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

# Renk paleti ayarları
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f']
sns.set_palette(colors)

# CSV dosyası yolu
INPUT_CSV = 'analiz/csv/main_analiz_sonuclari.csv'

def mevsim_belirle(ay):
    """Aydan mevsimi belirle"""
    if ay in [12, 1, 2]:
        return 'Kış'
    elif ay in [3, 4, 5]:
        return 'İlkbahar'
    elif ay in [6, 7, 8]:
        return 'Yaz'
    else:
        return 'Sonbahar'

def veri_yukle_ve_hazirla():
    """CSV dosyasını yükle ve analiz için hazırla"""
    try:
        df = pd.read_csv(INPUT_CSV)
        df['Tarih'] = pd.to_datetime(df['Tarih'])
        df['Ay'] = df['Tarih'].dt.month
        df['Mevsim'] = df['Ay'].apply(mevsim_belirle)
        
        # Ay isimlerini ekle
        ay_isimleri = {
            1: 'Ocak', 2: 'Şubat', 3: 'Mart', 4: 'Nisan',
            5: 'Mayıs', 6: 'Haziran', 7: 'Temmuz', 8: 'Ağustos',
            9: 'Eylül', 10: 'Ekim', 11: 'Kasım', 12: 'Aralık'
        }
        df['Ay_Ismi'] = df['Ay'].map(ay_isimleri)
        
        print(f"✓ {len(df)} veri noktası yüklendi")
        print(f"✓ Tarih aralığı: {df['Tarih'].min().strftime('%Y-%m-%d')} - {df['Tarih'].max().strftime('%Y-%m-%d')}")
        
        return df
    except FileNotFoundError:
        print(f"❌ HATA: '{INPUT_CSV}' dosyası bulunamadı.")
        return None
    except Exception as e:
        print(f"❌ HATA: {e}")
        return None

def yillik_degisim_grafigi(df):
    """Su derinliği ve hacmin yıllara göre değişimi"""
    # Yıllık ortalama değerleri hesapla
    yillik_data = df.groupby('Yil').agg({
        'Tahmini_Derinlik_m': 'mean',
        'Hacim_Milyon_m3': 'mean',
        'Gol_Alani_km2': 'mean'
    }).reset_index()
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('Meke Gölü - Yıllık Değişim Analizi', fontsize=16, fontweight='bold')
    
    # 1. Su Derinliği - Yıllık
    ax1.plot(yillik_data['Yil'], yillik_data['Tahmini_Derinlik_m'], 
             marker='o', linewidth=2, markersize=8, color=colors[0])
    ax1.set_title('Ortalama Su Derinliği (Yıllık)', fontweight='bold')
    ax1.set_xlabel('Yıl')
    ax1.set_ylabel('Su Derinliği (m)')
    ax1.grid(True, alpha=0.3)
    ax1.set_xticks(yillik_data['Yil'])
    
    # Değerleri noktaların üzerine yaz
    for i, row in yillik_data.iterrows():
        ax1.annotate(f'{row["Tahmini_Derinlik_m"]:.1f}m', 
                    (row['Yil'], row['Tahmini_Derinlik_m']),
                    textcoords="offset points", xytext=(0,10), ha='center')
    
    # 2. Su Hacmi - Yıllık
    ax2.plot(yillik_data['Yil'], yillik_data['Hacim_Milyon_m3'], 
             marker='s', linewidth=2, markersize=8, color=colors[1])
    ax2.set_title('Ortalama Su Hacmi (Yıllık)', fontweight='bold')
    ax2.set_xlabel('Yıl')
    ax2.set_ylabel('Su Hacmi (Milyon m³)')
    ax2.grid(True, alpha=0.3)
    ax2.set_xticks(yillik_data['Yil'])
    
    # Değerleri noktaların üzerine yaz
    for i, row in yillik_data.iterrows():
        ax2.annotate(f'{row["Hacim_Milyon_m3"]:.2f}', 
                    (row['Yil'], row['Hacim_Milyon_m3']),
                    textcoords="offset points", xytext=(0,10), ha='center')
    
    # 3. Göl Alanı - Yıllık
    ax3.plot(yillik_data['Yil'], yillik_data['Gol_Alani_km2'], 
             marker='^', linewidth=2, markersize=8, color=colors[2])
    ax3.set_title('Ortalama Göl Alanı (Yıllık)', fontweight='bold')
    ax3.set_xlabel('Yıl')
    ax3.set_ylabel('Göl Alanı (km²)')
    ax3.grid(True, alpha=0.3)
    ax3.set_xticks(yillik_data['Yil'])
    
    # Değerleri noktaların üzerine yaz
    for i, row in yillik_data.iterrows():
        ax3.annotate(f'{row["Gol_Alani_km2"]:.3f}', 
                    (row['Yil'], row['Gol_Alani_km2']),
                    textcoords="offset points", xytext=(0,10), ha='center')
    
    # 4. Kombinasyon grafik (İkili Y ekseni)
    ax4_twin = ax4.twinx()
    
    line1 = ax4.plot(yillik_data['Yil'], yillik_data['Tahmini_Derinlik_m'], 
                    marker='o', linewidth=2, markersize=6, color=colors[0], label='Derinlik (m)')
    line2 = ax4_twin.plot(yillik_data['Yil'], yillik_data['Hacim_Milyon_m3'], 
                         marker='s', linewidth=2, markersize=6, color=colors[1], label='Hacim (Milyon m³)')
    
    ax4.set_title('Derinlik ve Hacim Kombinasyonu', fontweight='bold')
    ax4.set_xlabel('Yıl')
    ax4.set_ylabel('Su Derinliği (m)', color=colors[0])
    ax4_twin.set_ylabel('Su Hacmi (Milyon m³)', color=colors[1])
    ax4.grid(True, alpha=0.3)
    ax4.set_xticks(yillik_data['Yil'])
    
    # Legend
    lines1, labels1 = ax4.get_legend_handles_labels()
    lines2, labels2 = ax4_twin.get_legend_handles_labels()
    ax4.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
    
    plt.tight_layout()
    plt.savefig('analiz/grafik/grafik_yillik_degisim.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    return yillik_data

def mevsimsel_degisim_grafigi(df):
    """Su derinliği ve hacmin mevsimlere göre değişimi"""
    # Mevsimsel ortalama değerleri hesapla
    mevsimsel_data = df.groupby('Mevsim').agg({
        'Tahmini_Derinlik_m': ['mean', 'std', 'count'],
        'Hacim_Milyon_m3': ['mean', 'std', 'count'],
        'Gol_Alani_km2': ['mean', 'std', 'count']
    }).reset_index()
    
    # Kolon isimlerini düzelt
    mevsimsel_data.columns = ['Mevsim', 'Derinlik_Ort', 'Derinlik_Std', 'Derinlik_Count',
                             'Hacim_Ort', 'Hacim_Std', 'Hacim_Count',
                             'Alan_Ort', 'Alan_Std', 'Alan_Count']
    
    # Mevsim sıralaması
    mevsim_sirasi = ['İlkbahar', 'Yaz', 'Sonbahar', 'Kış']
    mevsimsel_data['Mevsim'] = pd.Categorical(mevsimsel_data['Mevsim'], 
                                             categories=mevsim_sirasi, 
                                             ordered=True)
    mevsimsel_data = mevsimsel_data.sort_values('Mevsim')
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('Meke Gölü - Mevsimsel Değişim Analizi', fontsize=16, fontweight='bold')
    
    # 1. Su Derinliği - Mevsimsel (Bar Chart)
    bars1 = ax1.bar(mevsimsel_data['Mevsim'], mevsimsel_data['Derinlik_Ort'], 
                    yerr=mevsimsel_data['Derinlik_Std'], capsize=5, 
                    color=colors[:len(mevsimsel_data)], alpha=0.7)
    ax1.set_title('Ortalama Su Derinliği (Mevsimsel)', fontweight='bold')
    ax1.set_ylabel('Su Derinliği (m)')
    ax1.grid(True, alpha=0.3)
    
    # Değerleri barların üzerine yaz
    for i, (bar, row) in enumerate(zip(bars1, mevsimsel_data.itertuples())):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                f'{row.Derinlik_Ort:.1f}m\n(n={row.Derinlik_Count})',
                ha='center', va='bottom', fontweight='bold')
    
    # 2. Su Hacmi - Mevsimsel (Bar Chart)
    bars2 = ax2.bar(mevsimsel_data['Mevsim'], mevsimsel_data['Hacim_Ort'], 
                    yerr=mevsimsel_data['Hacim_Std'], capsize=5,
                    color=colors[:len(mevsimsel_data)], alpha=0.7)
    ax2.set_title('Ortalama Su Hacmi (Mevsimsel)', fontweight='bold')
    ax2.set_ylabel('Su Hacmi (Milyon m³)')
    ax2.grid(True, alpha=0.3)
    
    # Değerleri barların üzerine yaz
    for i, (bar, row) in enumerate(zip(bars2, mevsimsel_data.itertuples())):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                f'{row.Hacim_Ort:.2f}\n(n={row.Hacim_Count})',
                ha='center', va='bottom', fontweight='bold')
    
    # 3. Göl Alanı - Mevsimsel (Bar Chart)
    bars3 = ax3.bar(mevsimsel_data['Mevsim'], mevsimsel_data['Alan_Ort'], 
                    yerr=mevsimsel_data['Alan_Std'], capsize=5,
                    color=colors[:len(mevsimsel_data)], alpha=0.7)
    ax3.set_title('Ortalama Göl Alanı (Mevsimsel)', fontweight='bold')
    ax3.set_ylabel('Göl Alanı (km²)')
    ax3.grid(True, alpha=0.3)
    
    # Değerleri barların üzerine yaz
    for i, (bar, row) in enumerate(zip(bars3, mevsimsel_data.itertuples())):
        ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                f'{row.Alan_Ort:.3f}\n(n={row.Alan_Count})',
                ha='center', va='bottom', fontweight='bold')
    
    # 4. Box Plot - Mevsimsel dağılım
    mevsim_colors = {mevsim: colors[i] for i, mevsim in enumerate(mevsim_sirasi)}
    
    box_data = [df[df['Mevsim'] == mevsim]['Tahmini_Derinlik_m'].values 
                for mevsim in mevsim_sirasi if mevsim in df['Mevsim'].values]
    box_labels = [mevsim for mevsim in mevsim_sirasi if mevsim in df['Mevsim'].values]
    
    bp = ax4.boxplot(box_data, labels=box_labels, patch_artist=True)
    
    # Box plot renklerini ayarla
    for patch, mevsim in zip(bp['boxes'], box_labels):
        patch.set_facecolor(mevsim_colors[mevsim])
        patch.set_alpha(0.7)
    
    ax4.set_title('Su Derinliği Dağılımı (Mevsimsel)', fontweight='bold')
    ax4.set_ylabel('Su Derinliği (m)')
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('analiz/grafik/grafik_mevsimsel_degisim.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    return mevsimsel_data

def aylik_karsilastirma_grafigi(df):
    """Her yılın aynı ayına göre karşılaştırma (Nisan ve Haziran verileri Mayıs'a dahil)"""
    # Önce Nisan ve Haziran verilerini Mayıs'a ekle
    df_aylik = df.copy()
    
    # Nisan (4) ve Haziran (6) verilerini Mayıs (5) olarak değiştir
    df_aylik.loc[df_aylik['Ay'] == 4, 'Ay'] = 5
    df_aylik.loc[df_aylik['Ay'] == 6, 'Ay'] = 5
    df_aylik.loc[df_aylik['Ay'] == 5, 'Ay_Ismi'] = 'Mayıs'
    
    # Mevcut ayları belirle (güncellenmiş verilerden)
    mevcut_aylar = sorted(df_aylik['Ay'].unique())
    
    # Subplot sayısını hesapla (her ay için bir grafik)
    n_aylar = len(mevcut_aylar)
    n_rows = (n_aylar + 1) // 2
    
    fig, axes = plt.subplots(n_rows, 2, figsize=(16, 4*n_rows))
    fig.suptitle('Meke Gölü - Aynı Ay Karşılaştırması (Yıllık Trend)', fontsize=16, fontweight='bold')
    
    if n_rows == 1:
        axes = axes.reshape(1, -1)
    
    for i, ay in enumerate(mevcut_aylar):
        row = i // 2
        col = i % 2
        ax = axes[row, col]
        
        # O ayın verilerini filtrele
        ay_data = df_aylik[df_aylik['Ay'] == ay].copy()
        ay_data = ay_data.sort_values('Yil')
        
        if len(ay_data) > 0:
            ay_ismi = ay_data['Ay_Ismi'].iloc[0]
            
            # Mayıs ayı için özel grup işlemi (aynı yılda birden fazla veri varsa ortalama al)
            if ay == 5:  # Mayıs ayı
                ay_data_grouped = ay_data.groupby('Yil').agg({
                    'Tahmini_Derinlik_m': 'mean',
                    'Hacim_Milyon_m3': 'mean',
                    'Gol_Alani_km2': 'mean',
                    'Ay_Ismi': 'first'
                }).reset_index()
                ay_data = ay_data_grouped
            
            # İkili Y ekseni oluştur
            ax2 = ax.twinx()
            
            # Derinlik çizgisi
            line1 = ax.plot(ay_data['Yil'], ay_data['Tahmini_Derinlik_m'], 
                           marker='o', linewidth=2, markersize=6, 
                           color=colors[0], label='Derinlik (m)')
            
            # Hacim çizgisi
            line2 = ax2.plot(ay_data['Yil'], ay_data['Hacim_Milyon_m3'], 
                            marker='s', linewidth=2, markersize=6, 
                            color=colors[1], label='Hacim (Milyon m³)')
            
            ax.set_title(f'{ay_ismi} Karşılaştırması', fontweight='bold')
            ax.set_xlabel('Yıl')
            ax.set_ylabel('Su Derinliği (m)', color=colors[0])
            ax2.set_ylabel('Su Hacmi (Milyon m³)', color=colors[1])
            
            # Grid
            ax.grid(True, alpha=0.3)
            
            # X ekseni yılları
            ax.set_xticks(ay_data['Yil'])
            ax.tick_params(axis='x', rotation=45)
            
            # Değerleri noktaların yanına yaz
            for _, row_data in ay_data.iterrows():
                # Derinlik değeri
                ax.annotate(f'{row_data["Tahmini_Derinlik_m"]:.1f}', 
                           (row_data['Yil'], row_data['Tahmini_Derinlik_m']),
                           textcoords="offset points", xytext=(-15,5), 
                           ha='center', fontsize=8, color=colors[0])
                # Hacim değeri
                ax2.annotate(f'{row_data["Hacim_Milyon_m3"]:.2f}', 
                            (row_data['Yil'], row_data['Hacim_Milyon_m3']),
                            textcoords="offset points", xytext=(15,5), 
                            ha='center', fontsize=8, color=colors[1])
            
            # Legend
            lines1, labels1 = ax.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax.legend(lines1 + lines2, labels1 + labels2, loc='upper right', fontsize=8)
        
        else:
            ax.text(0.5, 0.5, 'Veri Yok', ha='center', va='center', transform=ax.transAxes)
            ax.set_title(f'Ay {ay} - Veri Yok')
    
    # Boş subplot'ları gizle
    for i in range(n_aylar, n_rows * 2):
        row = i // 2
        col = i % 2
        axes[row, col].set_visible(False)
    
    plt.tight_layout()
    plt.savefig('analiz/grafik/grafik_aylik_karsilastirma.png', dpi=300, bbox_inches='tight')
    plt.close()

def detayli_trend_analizi(df):
    """Detaylı trend analizi ve istatistikler"""
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Meke Gölü - Detaylı Trend Analizi', fontsize=16, fontweight='bold')
    
    # 1. Zaman serisinde tüm değerler
    ax1.scatter(df['Tarih'], df['Tahmini_Derinlik_m'], alpha=0.7, s=50, color=colors[0], label='Derinlik')
    ax1.plot(df['Tarih'], df['Tahmini_Derinlik_m'], alpha=0.5, color=colors[0])
    ax1.set_title('Su Derinliği Zaman Serisi', fontweight='bold')
    ax1.set_xlabel('Tarih')
    ax1.set_ylabel('Su Derinliği (m)')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # 2. Hacim zaman serisi
    ax2.scatter(df['Tarih'], df['Hacim_Milyon_m3'], alpha=0.7, s=50, color=colors[1], label='Hacim')
    ax2.plot(df['Tarih'], df['Hacim_Milyon_m3'], alpha=0.5, color=colors[1])
    ax2.set_title('Su Hacmi Zaman Serisi', fontweight='bold')
    ax2.set_xlabel('Tarih')
    ax2.set_ylabel('Su Hacmi (Milyon m³)')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    # 3. Derinlik vs Alan scatter
    ax3.scatter(df['Gol_Alani_km2'], df['Tahmini_Derinlik_m'], 
               c=df['Yil'], cmap='viridis', s=60, alpha=0.8)
    ax3.set_title('Su Derinliği vs Göl Alanı İlişkisi', fontweight='bold')
    ax3.set_xlabel('Göl Alanı (km²)')
    ax3.set_ylabel('Su Derinliği (m)')
    ax3.grid(True, alpha=0.3)
    
    # Colorbar
    cbar = plt.colorbar(ax3.collections[0], ax=ax3)
    cbar.set_label('Yıl')
    
    # 4. Su seviye durumu dağılımı
    su_durumu_counts = df['Su_Seviye_Durumu'].value_counts()
    wedges, texts, autotexts = ax4.pie(su_durumu_counts.values, 
                                      labels=su_durumu_counts.index,
                                      autopct='%1.1f%%',
                                      colors=colors[:len(su_durumu_counts)])
    ax4.set_title('Su Seviye Durumu Dağılımı', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('analiz/grafik/grafik_detayli_trend_analizi.png', dpi=300, bbox_inches='tight')
    plt.close()

def istatistik_ozeti_olustur(df):
    """Detaylı istatistik özeti yazdır"""
    print("\n" + "="*80)
    print("MEKE GÖLÜ ANALİZ İSTATİSTİKLERİ")
    print("="*80)
    
    # Genel istatistikler
    print("\n📊 GENEL İSTATİSTİKLER:")
    print(f"• Toplam ölçüm sayısı: {len(df)}")
    print(f"• Analiz dönem aralığı: {df['Tarih'].min().strftime('%Y-%m-%d')} - {df['Tarih'].max().strftime('%Y-%m-%d')}")
    print(f"• Maksimum su derinliği: {df['Tahmini_Derinlik_m'].max():.2f} m")
    print(f"• Ortalama su derinliği: {df['Tahmini_Derinlik_m'].mean():.2f} m")
    print(f"• Maksimum su hacmi: {df['Hacim_Milyon_m3'].max():.3f} milyon m³")
    print(f"• Ortalama su hacmi: {df['Hacim_Milyon_m3'].mean():.3f} milyon m³")
    print(f"• Maksimum göl alanı: {df['Gol_Alani_km2'].max():.4f} km²")
    print(f"• Ortalama göl alanı: {df['Gol_Alani_km2'].mean():.4f} km²")
    
    # Yıllık trend
    print("\n📈 YILLIK TREND:")
    yillik_ort = df.groupby('Yil').agg({
        'Tahmini_Derinlik_m': 'mean',
        'Hacim_Milyon_m3': 'mean',
        'Gol_Alani_km2': 'mean'
    }).round(3)
    
    for yil, row in yillik_ort.iterrows():
        print(f"  {yil}: Derinlik={row['Tahmini_Derinlik_m']:.2f}m, " +
              f"Hacim={row['Hacim_Milyon_m3']:.3f}Mm³, " +
              f"Alan={row['Gol_Alani_km2']:.4f}km²")
    
    # Mevsimsel trend
    print("\n🌤️  MEVSIMSEL TREND:")
    mevsimsel_ort = df.groupby('Mevsim').agg({
        'Tahmini_Derinlik_m': 'mean',
        'Hacim_Milyon_m3': 'mean',
        'Gol_Alani_km2': 'mean'
    }).round(3)
    
    for mevsim, row in mevsimsel_ort.iterrows():
        print(f"  {mevsim}: Derinlik={row['Tahmini_Derinlik_m']:.2f}m, " +
              f"Hacim={row['Hacim_Milyon_m3']:.3f}Mm³, " +
              f"Alan={row['Gol_Alani_km2']:.4f}km²")
    
    # Su durumu analizi
    print("\n💧 SU DURUMU ANALİZİ:")
    su_durumu_dagilim = df['Su_Seviye_Durumu'].value_counts()
    for durum, sayi in su_durumu_dagilim.items():
        yuzde = (sayi / len(df)) * 100
        print(f"  {durum}: {sayi} ölçüm (%{yuzde:.1f})")

def main():
    """Ana çalıştırma fonksiyonu"""
    print("Meke Gölü Grafik Analizi Başlatılıyor...")
    print("="*60)
    
    # Veriyi yükle
    df = veri_yukle_ve_hazirla()
    if df is None:
        return
    
    print("\n📈 Grafikler oluşturuluyor...")
    
    # 1. Yıllık değişim grafiği
    print("1. Yıllık değişim grafiği oluşturuluyor...")
    yillik_data = yillik_degisim_grafigi(df)
    
    # 2. Mevsimsel değişim grafiği
    print("2. Mevsimsel değişim grafiği oluşturuluyor...")
    mevsimsel_data = mevsimsel_degisim_grafigi(df)
    
    # 3. Aylık karşılaştırma grafiği
    print("3. Aylık karşılaştırma grafiği oluşturuluyor...")
    aylik_karsilastirma_grafigi(df)
    
    # 4. Detaylı trend analizi
    print("4. Detaylı trend analizi oluşturuluyor...")
    detayli_trend_analizi(df)
    
    # 5. İstatistik özeti
    istatistik_ozeti_olustur(df)
    
    print("\n✅ Tüm grafikler başarıyla oluşturuldu!")
    print("📁 Grafik dosyaları kaydedildi:")
    print("   • grafik_yillik_degisim.png")
    print("   • grafik_mevsimsel_degisim.png") 
    print("   • grafik_aylik_karsilastirma.png")
    print("   • grafik_detayli_trend_analizi.png")
    print("="*60)

if __name__ == "__main__":
    main()