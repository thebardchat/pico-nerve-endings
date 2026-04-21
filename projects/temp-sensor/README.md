# temp-sensor

**Reads the RP2350 onboard temperature sensor and streams JSON over USB serial to the host Pi.**

No extra hardware needed — just a Pico 2 and a USB cable. Powers the closet temperature display in the ShaneBrain mega-dashboard and triggers heat alerts via the Discord bot.

---

## Hardware Required

Just the Pico 2 itself. See [wiring.md](wiring.md).
- Raspberry Pi Pico 2 (RP2350)
- Micro-USB data cable

---

## Flash the Firmware

> ⚠️ The `firmware/main.py` in this repo is a best-reconstruction placeholder. The production firmware lives on the physical pico2-closet unit. To extract the real firmware, see the comment at the top of `firmware/main.py`.

```bash
# Stop the listener first so it doesn't hold the serial port
sudo systemctl stop pico-listener

# Flash via mpremote
mpremote connect /dev/pico-temp cp firmware/main.py :main.py
mpremote connect /dev/pico-temp reset

# Restart the listener
sudo systemctl start pico-listener
```

---

## Host Setup (Pi 5)

**1. Install dependencies:**
```bash
pip install pyserial --break-system-packages
```

**2. Install udev rule** (stable `/dev/pico-temp` symlink):
```bash
sudo cp ../../shared/udev/99-pico-serial.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules && sudo udevadm trigger
```

**3. Install the listener service:**
```bash
sudo cp system/pico-listener.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now pico-listener
```

**4. Verify it's working:**
```bash
systemctl status pico-listener
cat /mnt/shanebrain-raid/mega-dashboard/pico-data.json
```

---

## Output

The host script writes live data to `/mnt/shanebrain-raid/mega-dashboard/pico-data.json`:

```json
{
  "uptime_s": 3600,
  "device": "pico2-closet",
  "temp_f": 72.3,
  "temp_c": 22.4,
  "reading": 720,
  "last_update": "2026-04-21 06:00:01 AM"
}
```

This feeds the mega-dashboard temp panel, the morning briefing, and the Pironman5 LED heat alerts.

---

## Fork This

Change `DEVICE_NAME` in `firmware/main.py` for each unit. Works on any Pi, any OS. On Windows, replace `/dev/ttyACM0` with the correct COM port in `host/pico-listener.py`.
