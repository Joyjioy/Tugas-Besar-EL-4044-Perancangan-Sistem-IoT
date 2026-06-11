from pathlib import Path
import threading
import time

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from mqtt_handler import start_mqtt, latest_data
from weather_service import update_weather, weather_data
from database import init_db, get_history


BASE_DIR = Path(__file__).resolve().parent

app = FastAPI()

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static"
)

templates = Jinja2Templates(
    directory=BASE_DIR / "templates"
)


@app.on_event("startup")
def startup_event():

    init_db()

    update_weather()

    start_mqtt()

    def weather_loop():
        while True:
            update_weather()
            time.sleep(600)

    threading.Thread(
        target=weather_loop,
        daemon=True
    ).start()


@app.get("/")
def dashboard(request: Request):

    context = {
        "request": request
    }

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context=context
    )

@app.get("/api/status")
def get_status():

    latest_data["weather"] = weather_data

    last_update = latest_data.get("last_update")

    if last_update is None:
        latest_data["sensor_status"] = "Offline"
        latest_data["seconds_since_update"] = None

    else:
        seconds_since_update = int(time.time() - last_update)

        latest_data["seconds_since_update"] = seconds_since_update

        if seconds_since_update <= 15:
            latest_data["sensor_status"] = "Online"
        else:
            latest_data["sensor_status"] = "Offline"

    return latest_data


@app.get("/api/history")
def history():

    rows = get_history()

    result = []

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


@app.get("/api/stats")
def stats():

    rows = get_history()

    if not rows:
        return {
            "total_readings": 0,
            "average_soil": 0,
            "min_soil": 0,
            "max_soil": 0,
            "pump_on_count": 0,
            "rain_count": 0
        }

    soil_values = [row[0] for row in rows]
    pump_values = [row[1] for row in rows]
    rain_values = [row[4] for row in rows]

    pump_on_count = sum(
        1 for pump in pump_values
        if pump and "ON" in str(pump)
    )

    rain_count = sum(
        1 for rain in rain_values
        if int(rain) == 1
    )

    return {
        "total_readings": len(rows),
        "average_soil": round(sum(soil_values) / len(soil_values), 2),
        "min_soil": min(soil_values),
        "max_soil": max(soil_values),
        "pump_on_count": pump_on_count,
        "rain_count": rain_count
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000
    )
