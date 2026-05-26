import time
from config import (
    DRY_LIMIT,
    WATERING_DURATION,
    COOLDOWN_SECONDS
)

last_watering = 0


def should_water(soil_value):
    global last_watering

    now = time.time()

    if now - last_watering < COOLDOWN_SECONDS:
        return False

    if soil_value > DRY_LIMIT:
        last_watering = now
        return True

    return False


def watering_duration(soil_value):

    if soil_value > 850:
        return 3

    elif soil_value > 800:
        return 2

    return WATERING_DURATION