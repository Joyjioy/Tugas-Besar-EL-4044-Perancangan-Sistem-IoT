from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from mqtt_handler import start_mqtt, latest_data
from weather_service import update_weather, weather_data
from database import init_db
from database import get_history 

import threading
import time

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.on_event("startup")
def startup_event():

    init_db()

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
        request,
        "index.html",
        context
    )

@app.get("/api/status")
def get_status():

    latest_data["weather"] = weather_data

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