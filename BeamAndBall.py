import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Button
import skfuzzy as fuzz
from skfuzzy import control as ctrl

# =========================================================
# Fiziksel parametreler
# =========================================================
yercekimi = 9.81         # Yerçekimi ivmesi (m/s^2)
dt = 0.02                # Zaman adımı (s)
top_yaricap = 0.05       # Top yarıçapı (m)
cubuk_yarim_uzunluk = 1.0 # Çubuğun yarı uzunluğu (m)

# =========================================================
# Sistem durum değişkenleri
# =========================================================
top_konum = 0.2          # Topun çubuk üzerindeki konumu
top_hiz = 0.0            # Topun hızı
cubuk_aci_gercek = 0.0   # Motorun ürettiği gerçek çubuk açısı
cubuk_aci_dinamik = 0.0  # Dinamik hesaplamada kullanılan açı
cubuk_aci_gorsel = 0.0   # Görselleştirmede kullanılan açı
zaman = 0.0
MOD_OTOMATIK = False     # Kontrolörler arası geçiş için değişken

# --- VERİ TOPLAMA LİSTELERİ (YENİ) ---
gecmis_zaman = []
gecmis_konum = []
gecmis_aci = []

# =========================================================
# Gürültü ve bozucular
# =========================================================
olcum_gurultusu_acik = False
fiziksel_gurultu_acik = False
cubuk_darbesi = 0.0

# =========================================================
# 1. SİSTEM: SEZGİSEL BULANIK KONTROLÖR
# =========================================================
konum = ctrl.Antecedent(np.linspace(-1, 1, 101), 'konum')
hiz = ctrl.Antecedent(np.linspace(-1, 1, 101), 'hiz')
aci = ctrl.Consequent(np.linspace(-1, 1, 101), 'aci')

konum['sol'] = fuzz.trimf(konum.universe, [-1, -1, 0])
konum['orta'] = fuzz.trimf(konum.universe, [-0.3, 0, 0.3])
konum['sag'] = fuzz.trimf(konum.universe, [0, 1, 1])

hiz['neg'] = fuzz.trimf(hiz.universe, [-1, -1, 0])
hiz['sifir'] = fuzz.trimf(hiz.universe, [-0.2, 0, 0.2])
hiz['poz'] = fuzz.trimf(hiz.universe, [0, 1, 1])

aci['sola'] = fuzz.trimf(aci.universe, [-1, -0.5, 0])
aci['duz'] = fuzz.trimf(aci.universe, [-0.1, 0, 0.1])
aci['saga'] = fuzz.trimf(aci.universe, [0, 0.5, 1])

kurallar_sezgisel = [
    ctrl.Rule(konum['sag'] & hiz['poz'], aci['sola']),
    ctrl.Rule(konum['sag'] & hiz['sifir'], aci['sola']),
    ctrl.Rule(konum['sag'] & hiz['neg'], aci['duz']),
    ctrl.Rule(konum['orta'] & hiz['poz'], aci['sola']),
    ctrl.Rule(konum['orta'] & hiz['sifir'], aci['duz']),
    ctrl.Rule(konum['orta'] & hiz['neg'], aci['saga']),
    ctrl.Rule(konum['sol'] & hiz['neg'], aci['saga']),
    ctrl.Rule(konum['sol'] & hiz['sifir'], aci['saga']),
    ctrl.Rule(konum['sol'] & hiz['poz'], aci['duz']),
]

bulanık_sim = ctrl.ControlSystemSimulation(ctrl.ControlSystem(kurallar_sezgisel))

# =========================================================
# 2. SİSTEM: OTOMATİK BULANIK KONTROLÖR
# =========================================================
konum_oto = ctrl.Antecedent(np.linspace(-1, 1, 101), 'konum_oto')
hiz_oto   = ctrl.Antecedent(np.linspace(-1, 1, 101), 'hiz_oto')
aci_oto   = ctrl.Consequent(np.linspace(-1, 1, 101), 'aci_oto')

konum_oto.automf(3)
hiz_oto.automf(3)
aci_oto.automf(3)

kurallar_oto = []
etiketler = ['poor', 'average', 'good']
etiket_deger = {'poor': -1, 'average': 0, 'good': 1}

def otomatik_karar(k, h):
    etki = -k - 0.5 * h
    if etki > 0.3: return 'good'
    elif etki < -0.3: return 'poor'
    else: return 'average'

for k_lbl in etiketler:
    for h_lbl in etiketler:
        cikti_lbl = otomatik_karar(etiket_deger[k_lbl], etiket_deger[h_lbl])
        kurallar_oto.append(ctrl.Rule(konum_oto[k_lbl] & hiz_oto[h_lbl], aci_oto[cikti_lbl]))

otomatik_ctrl = ctrl.ControlSystem(kurallar_oto)
otomatik_sim  = ctrl.ControlSystemSimulation(otomatik_ctrl)

# =========================================================
# KONTROLÖR FONKSİYONU
# =========================================================
def kontrolor(t_konum, t_hiz):
    t_konum = np.clip(t_konum, -1, 1)
    t_hiz = np.clip(t_hiz, -1, 1)
    
    if MOD_OTOMATIK:
        otomatik_sim.input['konum_oto'] = t_konum
        otomatik_sim.input['hiz_oto'] = t_hiz
        otomatik_sim.compute()
        return 1.8 * otomatik_sim.output['aci_oto']
    else:
        bulanık_sim.input['konum'] = t_konum
        bulanık_sim.input['hiz'] = t_hiz
        bulanık_sim.compute()
        return 1.5 * bulanık_sim.output['aci']

# =========================================================
# Raporlama ve Analiz Modülü (EKLEME)
# =========================================================
def rapor_al(event):
    if len(gecmis_zaman) < 10:
        print("Yeterli veri yok! Simülasyonu biraz çalıştırın.")
        return

    t_arr = np.array(gecmis_zaman)
    x_arr = np.array(gecmis_konum)
    u_arr = np.array(gecmis_aci)
    aktif_mod = "OTOMATIK" if MOD_OTOMATIK else "SEZGISEL"

    # --- Performans Metrikleri ---
    iae = np.sum(np.abs(x_arr)) * dt
    max_asim = np.max(np.abs(x_arr))
    
    tolerans = 0.05
    yerlesme_suresi = 0.0
    for i in range(len(x_arr) - 1, -1, -1):
        if abs(x_arr[i]) > tolerans:
            yerlesme_suresi = t_arr[i]
            break
            
    yerlesme_metin = f"{yerlesme_suresi:.2f} sn" if yerlesme_suresi < t_arr[-1] - 0.2 else "Yerleşmedi"

    print(f"\n--- RAPOR ({aktif_mod}) ---")
    print(f"IAE (Toplam Hata): {iae:.4f}")
    print(f"Max Aşım: {max_asim:.4f} m")
    print(f"Yerleşme Süresi: {yerlesme_metin}")

    # --- Grafik Çizimi ---
    plt.figure(figsize=(10, 8))
    
    plt.subplot(2, 1, 1)
    plt.plot(t_arr, x_arr, label="Top Konumu", color="blue", linewidth=2)
    plt.axhline(0, color="black", linestyle="--", alpha=0.5)
    plt.axhspan(-tolerans, tolerans, color="green", alpha=0.1, label="Tolerans Bandı (0.05m)")
    plt.title(f"Sistem Cevabı - Mod: {aktif_mod}")
    plt.ylabel("Konum (m)")
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(loc="upper right")
    
    plt.subplot(2, 1, 2)
    plt.plot(t_arr, u_arr, label="Kontrol Sinyali (Açı)", color="red", linewidth=1.5)
    plt.xlabel("Zaman (s)")
    plt.ylabel("Çubuk Açısı (rad)")
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(loc="upper right")
    
    info_text = (f"IAE: {iae:.3f}\nMax Aşım: {max_asim:.3f} m\nYerleşme: {yerlesme_metin}")
    plt.figtext(0.15, 0.02, info_text, bbox=dict(facecolor='white', alpha=0.8))

    plt.tight_layout(rect=[0, 0.05, 1, 1])
    plt.show()

# =========================================================
# Simülasyon adımı
# =========================================================
def adim():
    global top_konum, top_hiz, cubuk_aci_gercek, cubuk_aci_dinamik, cubuk_aci_gorsel, zaman, cubuk_darbesi

    olculen_konum = top_konum
    olculen_hiz = top_hiz
    
    if olcum_gurultusu_acik:
        olculen_konum += np.random.normal(0, 0.03)
        olculen_hiz += np.random.normal(0, 0.1)

    istenen_aci = kontrolor(olculen_konum, olculen_hiz)

    # Veri Kaydı (YENİ)
    gecmis_zaman.append(zaman)
    gecmis_konum.append(top_konum)
    gecmis_aci.append(istenen_aci)

    zaman_sabiti = 0.1
    cubuk_aci_gercek += (istenen_aci - cubuk_aci_gercek) * dt / zaman_sabiti

    fiziksel_gurultu = 0.0
    if fiziksel_gurultu_acik:
        fiziksel_gurultu = (0.02 * np.sin(0.001 * zaman) + 0.01 * np.random.randn())
    
    cubuk_darbesi *= 0.95
    cubuk_aci_dinamik = cubuk_aci_gorsel
    cubuk_aci_gorsel = cubuk_aci_gercek + fiziksel_gurultu + cubuk_darbesi

    top_ivme = (5 / 7) * yercekimi * np.sin(cubuk_aci_dinamik)
    top_hiz += top_ivme * dt
    top_konum += top_hiz * dt
    top_konum = np.clip(top_konum, -cubuk_yarim_uzunluk, cubuk_yarim_uzunluk)
    zaman += dt

# =========================================================
# GÖRSELLEŞTİRME
# =========================================================
fig, ax = plt.subplots(figsize=(8, 7))
plt.subplots_adjust(bottom=0.35)
ax.set_xlim(-1.2, 1.2)
ax.set_ylim(-0.6, 0.6)
ax.set_aspect('equal')

cubuk_cizgi, = ax.plot([], [], lw=5, color='black')
top_nokta, = ax.plot([], [], 'o', markersize=18, color='red')
bilgi_yazisi = ax.text(-1.15, 0.45, "", fontsize=10, weight='bold', bbox=dict(facecolor='yellow', alpha=0.3))

def guncelle(frame):
    adim()
    x1, y1 = -cubuk_yarim_uzunluk * np.cos(cubuk_aci_gorsel), -cubuk_yarim_uzunluk * np.sin(cubuk_aci_gorsel)
    x2, y2 = cubuk_yarim_uzunluk * np.cos(cubuk_aci_gorsel), cubuk_yarim_uzunluk * np.sin(cubuk_aci_gorsel)
    cubuk_cizgi.set_data([x1, x2], [y1, y2])

    tx, ty = top_konum * np.cos(cubuk_aci_gorsel), top_konum * np.sin(cubuk_aci_gorsel)
    nx, ny = -np.sin(cubuk_aci_gorsel), np.cos(cubuk_aci_gorsel)
    top_nokta.set_data([tx + top_yaricap * nx], [ty + top_yaricap * ny])

    mod_metni = "AKTIF SISTEM: OTOMATIK" if MOD_OTOMATIK else "AKTIF SISTEM: SEZGISEL"
    bilgi_yazisi.set_text(f"{mod_metni}\nZaman: {zaman:.2f}s\nKonum: {top_konum:.2f}\nGürültüler: O:{olcum_gurultusu_acik} F:{fiziksel_gurultu_acik}")
    return cubuk_cizgi, top_nokta, bilgi_yazisi

# =========================================================
# BUTON FONKSİYONLARI
# =========================================================
def cubuga_darbe_fonk(event):
    global cubuk_darbesi
    cubuk_darbesi = np.random.choice([-1.5, 1.5])

def olcum_degistir(event):
    global olcum_gurultusu_acik
    olcum_gurultusu_acik = not olcum_gurultusu_acik

def fizik_degistir(event):
    global fiziksel_gurultu_acik
    fiziksel_gurultu_acik = not fiziksel_gurultu_acik

def sifirla_fonk(event):
    global top_konum, top_hiz, cubuk_aci_gercek, zaman, cubuk_darbesi, gecmis_zaman, gecmis_konum, gecmis_aci
    top_konum, top_hiz, cubuk_aci_gercek, zaman, cubuk_darbesi = 0.5, 0.0, 0.0, 0.0, 0.0
    gecmis_zaman, gecmis_konum, gecmis_aci = [], [], []
    print("Sistem ve geçmiş veriler sıfırlandı.")

def sistem_degistir(event):
    global MOD_OTOMATIK
    MOD_OTOMATIK = not MOD_OTOMATIK
    btn_switch.color = 'lime' if MOD_OTOMATIK else 'cyan'

# --- BUTON YERLEŞİMİ ---
ax_darbe = plt.axes([0.05, 0.22, 0.18, 0.07])
ax_olcum = plt.axes([0.28, 0.22, 0.18, 0.07])
ax_fizik = plt.axes([0.51, 0.22, 0.18, 0.07])
ax_reset = plt.axes([0.74, 0.22, 0.18, 0.07])
ax_switch = plt.axes([0.05, 0.12, 0.41, 0.07])
ax_rapor = plt.axes([0.51, 0.12, 0.41, 0.07]) # Rapor butonu yeri

btn_darbe = Button(ax_darbe, "Darbe Vur")
btn_darbe.on_clicked(cubuga_darbe_fonk)

btn_olcum = Button(ax_olcum, "Ölçüm Gürültüsü")
btn_olcum.on_clicked(olcum_degistir)

btn_fizik = Button(ax_fizik, "Fiziksel Gürültü")
btn_fizik.on_clicked(fizik_degistir)

btn_reset = Button(ax_reset, "Sifirla")
btn_reset.on_clicked(sifirla_fonk)

btn_switch = Button(ax_switch, "SİSTEM DEĞİŞTİR", color='cyan')
btn_switch.on_clicked(sistem_degistir)

btn_rapor = Button(ax_rapor, "RAPOR AL & ANALİZ ET", color='orange')
btn_rapor.on_clicked(rapor_al)

animasyon = FuncAnimation(fig, guncelle, interval=20, cache_frame_data=False)
plt.show()