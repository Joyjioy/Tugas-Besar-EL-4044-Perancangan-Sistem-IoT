import time
from config import DRY_LIMIT, LIMIT_AKTIF, COOLDOWN_SECONDS

# State global untuk melacak sistem kontrol
last_watering = 0
pump_active = False 

def evaluate_feedback_control(soil_value):
    """
    Sistem kendali feedback untuk menghindari over-watering.
    Mengembalikan:
      - "ON"  : Jika tanah kering dan pompa harus dinyalakan.
      - "OFF" : Jika pompa sedang aktif dan kelembapan tanah sudah cukup.
      - None  : Jika tidak ada perubahan status (tetap pada kondisi terakhir).
    """
    global last_watering, pump_active
    now = time.time()

    # KONDISI A: Pompa Sedang Aktif (Mekanisme Feedback Pemutusan)
    if pump_active:
        # Berdasarkan logika dasar: nilai semakin kecil = semakin basah.
        # Jika nilai soil sudah turun dan masuk ke range aman (di bawah DRY_LIMIT menuju WET_LIMIT),
        # atau bahkan sudah melewati WET_LIMIT (sangat basah), maka pompa harus mati seketika.
        if soil_value <= DRY_LIMIT:
            pump_active = False
            last_watering = now  # Cooldown mulai dihitung saat pompa mati
            return "OFF"
        return None

    # KONDISI B: Pompa Sedang Mati (Mekanisme Pemicu Penyiraman)
    else:
        # Proteksi cooldown agar pompa tidak mengalami short-cycling
        if now - last_watering < COOLDOWN_SECONDS:
            return None
        
        # Jika tanah kering (nilai soil melebihi DRY_LIMIT), nyalakan pompa
        if soil_value > DRY_LIMIT:
            pump_active = True
            return "ON"
        
        return None