import time

# Mengimpor nilai ambang batas (threshold) dari file konfigurasi
# DRY_LIMIT: Batas atas di mana tanah dianggap terlalu kering (memicu pompa ON)
# LIMIT_AKTIF: Batas bawah di mana tanah dianggap sudah cukup basah (memicu pompa OFF)
# COOLDOWN_SECONDS: Durasi jeda aman antar penyiraman
from config import DRY_LIMIT, LIMIT_AKTIF, COOLDOWN_SECONDS

# Variabel global untuk merekam jejak status sistem (State Management)

# last_watering merekam timestamp kapan pompa terakhir kali dimatikan
last_watering = 0
# pump_active melacak apakah saat ini pompa sedang dalam kondisi menyala atau mati
pump_active = False


def evaluate_feedback_control(soil_value):
    """
    Fungsi utama sistem kendali umpan balik (feedback control).
    Dievaluasi setiap kali ada data kelembapan baru dari sensor MQTT.
    """
    
    # Mendeklarasikan penggunaan variabel global agar nilainya dapat dimodifikasi 
    # di dalam cakupan fungsi ini dan perubahannya tersimpan untuk siklus berikutnya
    global last_watering, pump_active

    # Mengambil waktu saat ini dalam format detik (UNIX timestamp)
    now = time.time()

    # KONDISI 1: Evaluasi saat pompa SEDANG MENYALA
    if pump_active:
        
        # Cek apakah nilai sensor sudah turun mencapai atau melewati batas basah.
        # Catatan: Asumsi nilai sensor semakin kecil berarti tanah semakin basah.
        if soil_value <= LIMIT_AKTIF:
            
            # Ubah status internal pompa menjadi mati
            pump_active = False
            
            # Mulai menghitung mundur waktu cooldown dari detik ini
            last_watering = now
            
            # Kembalikan perintah pemutusan ke handler utama
            return "OFF"

        # Jika masih di atas LIMIT_AKTIF, kembalikan None (tidak melakukan apa-apa, biarkan menyala)
        return None

    # KONDISI 2: Evaluasi saat pompa SEDANG MATI
    else:
        
        # Proteksi Short-Cycling: Hitung selisih waktu sekarang dengan waktu mati terakhir.
        # Jika selisihnya masih di bawah batas cooldown, sistem ditahan agar tidak menyiram dulu.
        if now - last_watering < COOLDOWN_SECONDS:
            return None

        # Jika masa cooldown sudah lewat, cek apakah tanah masuk kategori kering
        if soil_value > DRY_LIMIT:
            
            # Ubah status internal pompa menjadi menyala
            pump_active = True
            
            # Kembalikan perintah penyalaan ke handler utama
            return "ON"

        # Jika tanah masih normal/basah, kembalikan None
        return None


def force_pump_off():
    """
    Fungsi interupsi paksa untuk mematikan pompa secara mendadak.
    """
    global last_watering, pump_active

    # Paksa reset status internal menjadi mati
    pump_active = False
    
    # Mulai ulang penghitungan cooldown dari waktu interupsi ini terjadi
    last_watering = time.time()
