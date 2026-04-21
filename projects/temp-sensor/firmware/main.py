# firmware/main.py — Pico 2 Temperature Sensor
# ⚠️  PLACEHOLDER — firmware lives on the physical pico2-closet device.
#
# To extract:
#   1. sudo systemctl stop pico-listener
#   2. Open Thonny → connect to /dev/pico-temp
#   3. File browser → copy main.py from Pico to this file
#   4. sudo systemctl start pico-listener
#   5. git add firmware/main.py && git commit -m "feat(temp-sensor): extract firmware from pico2-closet"
#
# What it does (from observed output in pico-data.json):
#   - Reads RP2350 onboard temperature sensor
#   - Sends JSON over USB serial at 115200 baud, newline-terminated
#   - Format: {"uptime_s": int, "device": "pico2-closet", "temp_f": float, "temp_c": float, "reading": int}
#
# MicroPython v1.24+ on RP2350

import machine
import ujson
import utime

sensor_temp = machine.ADC(4)
CONVERSION_FACTOR = 3.3 / (65535)
DEVICE_NAME = "pico2-closet"

reading = 0
start_ms = utime.ticks_ms()

while True:
    raw = sensor_temp.read_u16() * CONVERSION_FACTOR
    temp_c = 27 - (raw - 0.706) / 0.001721
    temp_f = temp_c * 9 / 5 + 32
    uptime_s = utime.ticks_diff(utime.ticks_ms(), start_ms) // 1000
    reading += 1

    payload = ujson.dumps({
        "uptime_s": uptime_s,
        "device": DEVICE_NAME,
        "temp_f": round(temp_f, 1),
        "temp_c": round(temp_c, 1),
        "reading": reading,
    })
    print(payload)
    utime.sleep(5)
