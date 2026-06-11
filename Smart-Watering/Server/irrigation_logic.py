import time
from config import DRY_LIMIT, LIMIT_AKTIF, COOLDOWN_SECONDS

last_watering = 0
pump_active = False


def evaluate_feedback_control(soil_value):
    global last_watering, pump_active

    now = time.time()

    if pump_active:
        if soil_value <= LIMIT_AKTIF:
            pump_active = False
            last_watering = now
            return "OFF"

        return None

    else:
        if now - last_watering < COOLDOWN_SECONDS:
            return None

        if soil_value > DRY_LIMIT:
            pump_active = True
            return "ON"

        return None


def force_pump_off():
    global last_watering, pump_active

    pump_active = False
    last_watering = time.time()
