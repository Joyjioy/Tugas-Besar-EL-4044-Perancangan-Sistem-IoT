from pathlib import Path
import threading
import time

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Mengimpor modul-modul internal sistem IoT yang telah dibuat sebelumnya
from mqtt_handler import start_mqtt, latest_data
from weather_service import update_weather, weather_data
from database import init_db, get_history

# Menentukan direktori dasar
BASE_DIR = Path(__file__).resolve().parent

# Inisialisasi aplikasi FastAPI
app = FastAPI()

# Memasang (mount) direktori "static" untuk menyajikan file statis 
# yang dibutuhkan oleh antarmuka web
app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static"
)

# Menentukan folder "templates" sebagai tempat penyimpanan file HTML (dashboard)
templates = Jinja2Templates(
    directory=BASE_DIR / "templates"
)

# Event startup ini akan dieksekusi satu kali secara otomatis sesaat sebelum 
# server FastAPI mulai menerima permintaan (request) HTTP
@app.on_event("startup")
def startup_event():
    
    # Memastikan tabel database SQLite tersedia sebelum mulai menyimpan riwayat
    init_db()

    # Memanggil pembaruan cuaca pertama kali agar data tidak kosong saat server baru nyala
    update_weather()

    # Memulai koneksi MQTT.
    start_mqtt()

    # Fungsi untuk memperbarui cuaca secara berkala (infinite loop)
    def weather_loop():
        while True:
            update_weather()
            time.sleep(600)  # Memberikan jeda 10 menit (600 detik) antar request

    # Menjalankan fungsi weather_loop di dalam thread terpisah (background thread)
    # daemon=True memastikan thread ini akan ikut dihentikan secara otomatis 
    # ketika aplikasi server utama (FastAPI) dimatikan.
    threading.Thread(
        target=weather_loop,
        daemon=True
    ).start()


# Endpoint untuk menyajikan halaman utama (Dashboard HTML)
@app.get("/")
def dashboard(request: Request):
    
    context = {
        "request": request
    }

    # Merender dan mengembalikan file index.html ke browser pengguna
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context=context
    )

# Endpoint API untuk mengambil status operasional terkini secara real-time
@app.get("/api/status")
def get_status():
    
    # Menyisipkan objek data cuaca terbaru ke dalam dictionary pengiriman
    latest_data["weather"] = weather_data

    last_update = latest_data.get("last_update")

    # Logika deteksi koneksi:
    # Jika server baru menyala dan belum ada data masuk sama sekali dari MQTT
    if last_update is None:
        latest_data["sensor_status"] = "Offline"
        latest_data["seconds_since_update"] = None

    else:
        # Menghitung berapa detik yang lalu sensor terakhir kali mengirim data
        seconds_since_update = int(time.time() - last_update)

        latest_data["seconds_since_update"] = seconds_since_update

        # Menentukan threshold 15 detik. Jika tidak ada pesan baru selama lebih dari 
        # 15 detik, sistem akan menandai perangkat keras sensor di lapangan sebagai "Offline"
        if seconds_since_update <= 15:
            latest_data["sensor_status"] = "Online"
        else:
            latest_data["sensor_status"] = "Offline"

    # Mengembalikan dictionary Python yang secara otomatis diubah menjadi JSON oleh FastAPI
    return latest_data


# Endpoint API untuk mengambil semua riwayat data dari database
@app.get("/api/history")
def history():
    
    # Mengambil seluruh baris data dari tabel SQLite
    rows = get_history()

    result = []

    # Mengonversi format baris mentah dari SQLite (Tuple) menjadi daftar Dictionary (JSON)
    for row in rows:
        result.append({
            "soil": row[0],
            "pump": row[1],
            "humidity": row[2],
            "temperature": row[3],
            "rain": row[4],
            "created_at": row[5]
        })

    return result


# Endpoint API untuk mengambil ringkasan analitik dan statistik data
@app.get("/api/stats")
def stats():
    
    rows = get_history()

    # Memproteksi endpoint dari error pembagian dengan nol jika database masih kosong
    if not rows:
        return {
            "total_readings": 0,
            "average_soil": 0,
            "min_soil": 0,
            "max_soil": 0,
            "pump_on_count": 0,
            "rain_count": 0
        }

    # Mengekstrak nilai spesifik dari setiap kolom database menggunakan list comprehension
    soil_values = [row[0] for row in rows]
    pump_values = [row[1] for row in rows]
    rain_values = [row[4] for row in rows]

    # Menghitung berapa kali siklus pompa menyala terekam di database
    pump_on_count = sum(
        1 for pump in pump_values
        if pump and "ON" in str(pump)
    )

    # Menghitung berapa kali cuaca hujan (direpresentasikan dengan angka 1/True) terekam
    rain_count = sum(
        1 for rain in rain_values
        if int(rain) == 1
    )

    # Menghitung statistik komputasi dasar dan mengembalikannya sebagai JSON
    return {
        "total_readings": len(rows),
        "average_soil": round(sum(soil_values) / len(soil_values), 2),
        "min_soil": min(soil_values),
        "max_soil": max(soil_values),
        "pump_on_count": pump_on_count,
        "rain_count": rain_count
    }


# Menjalankan Uvicorn
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000
    )
