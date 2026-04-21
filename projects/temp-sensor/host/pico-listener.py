#!/usr/bin/env python3
"""
Pico 2 Serial Listener — reads temperature data from USB-connected Pico 2
and writes latest reading to a shared file for the dashboard to consume.
"""

import json
import serial
import time
from pathlib import Path

SERIAL_PORT = "/dev/ttyACM0"
BAUD_RATE = 115200
DATA_FILE = Path("/mnt/shanebrain-raid/mega-dashboard/pico-data.json")


def main():
    print(f"Pico Listener: connecting to {SERIAL_PORT}")
    while True:
        try:
            with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=10) as ser:
                print("Pico Listener: connected")
                while True:
                    line = ser.readline().decode("utf-8", errors="ignore").strip()
                    if not line or not line.startswith("{"):
                        continue
                    try:
                        data = json.loads(line)
                        data["last_update"] = time.strftime("%Y-%m-%d %I:%M:%S %p")
                        DATA_FILE.write_text(json.dumps(data))
                    except json.JSONDecodeError:
                        pass
        except Exception as e:
            print(f"Pico Listener: {e} — retrying in 5s")
            time.sleep(5)


if __name__ == "__main__":
    main()
