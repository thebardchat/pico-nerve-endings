"""
ShaneBrain Pico 2 — Closet Monitor
===================================
Reads internal temperature sensor, pulses onboard LED as heartbeat,
sends JSON data over USB serial every 5 seconds.

Pi 5 listener reads this and feeds it to the Mega Dashboard.
No accessories needed — just the bare board.
"""

import machine
import time
import json

# Onboard LED (GPIO 25 on Pico 2)
led = machine.Pin("LED", machine.Pin.OUT)

# Internal temperature sensor (ADC channel 4)
temp_sensor = machine.ADC(4)

# Conversion factor for internal temp sensor
# RP2350: voltage = raw * 3.3 / 65535, temp = 27 - (voltage - 0.706) / 0.001721
CONVERSION = 3.3 / 65535

boot_time = time.ticks_ms()
reading_count = 0


def read_temp_f():
    """Read internal temperature in Fahrenheit."""
    raw = temp_sensor.read_u16()
    voltage = raw * CONVERSION
    temp_c = 27 - (voltage - 0.706) / 0.001721
    temp_f = temp_c * 9/5 + 32
    return round(temp_f, 1), round(temp_c, 1)


def heartbeat():
    """Quick LED flash to show we're alive."""
    led.on()
    time.sleep_ms(50)
    led.off()


# Startup flash pattern — 3 quick blinks
for _ in range(3):
    led.on()
    time.sleep_ms(100)
    led.off()
    time.sleep_ms(100)

print("ShaneBrain Pico 2 online")

while True:
    temp_f, temp_c = read_temp_f()
    reading_count += 1
    uptime_s = time.ticks_diff(time.ticks_ms(), boot_time) // 1000

    data = {
        "device": "pico2-closet",
        "temp_f": temp_f,
        "temp_c": temp_c,
        "uptime_s": uptime_s,
        "reading": reading_count,
    }

    # Send JSON over USB serial
    print(json.dumps(data))

    # Heartbeat LED
    heartbeat()

    # Read every 5 seconds
    time.sleep(5)
