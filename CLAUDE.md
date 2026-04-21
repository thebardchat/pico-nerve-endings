# CLAUDE.md — pico-nerve-endings

> Pico 2 (RP2350) firmware + host scripts — the peripheral nervous system of ShaneBrain.
> Repo: `/mnt/shanebrain-raid/shanebrain-core/pico-nerve-endings/`
> Governing doc: [CONSTITUTION.md](CONSTITUTION.md)

---

## What This Repo Is

Two Raspberry Pi Pico 2 (RP2350) units connected to the Pi 5 via USB serial.
Each project under `projects/` is **fully self-contained** — firmware, host script, systemd files, wiring docs. Fork any one folder and it stands alone.

| Unit | udev symlink | Role | Project dir |
|------|-------------|------|-------------|
| pico2-closet | `/dev/pico-temp` | Closet temp sensor → JSON over serial | `projects/temp-sensor/` |
| pico2-audio | `/dev/pico-audio` | WAV receiver → I2S → MAX98357A speaker | `projects/audio-speaker/` |

---

## Hardware Pinout — audio-speaker

```
Pico 2 GP10  →  MAX98357A BCLK
Pico 2 GP11  →  MAX98357A LRC
Pico 2 GP12  →  MAX98357A DIN
Pico 2 3V3   →  MAX98357A VIN
Pico 2 GND   →  MAX98357A GND
MAX98357A SD → 10kΩ → VIN   (12dB gain, mono)
MAX98357A +/- → speaker terminals
```

Full details: [projects/audio-speaker/wiring.md](projects/audio-speaker/wiring.md)

---

## Serial Protocol — audio-speaker

Host → Pico framing over USB serial (115200 baud, USB CDC):

```
[4B]  Magic:    b"BRDG"
[4B]  WAV size: uint32 little-endian
[4B]  CRC32:    uint32 little-endian (zlib.crc32 of WAV bytes)
[N B] WAV data: 8kHz 8-bit mono PCM (≤300KB)
[4B]  Trailer:  b"DONE"
```

Pico → Host: `b"ACK\n"` on success · `b"ERR\n"` on CRC fail / bad frame / size exceeded

---

## Flashing Firmware

**Requirements:** MicroPython v1.24+ on RP2350. `mpremote` or Thonny.

```bash
# Install mpremote
pip install mpremote --break-system-packages

# Flash audio-speaker
sudo systemctl stop tts-briefing 2>/dev/null || true
mpremote connect /dev/pico-audio cp projects/audio-speaker/firmware/main.py :main.py
mpremote connect /dev/pico-audio reset

# Flash temp-sensor
sudo systemctl stop pico-listener
mpremote connect /dev/pico-temp cp projects/temp-sensor/firmware/main.py :main.py
mpremote connect /dev/pico-temp reset
sudo systemctl start pico-listener
```

---

## udev Serial Symlinks

Both Picos share `shared/udev/99-pico-serial.rules`. Symlinks are pinned by USB serial number so ttyACM numbering never shifts.

Current serials:
- pico2-closet (`/dev/pico-temp`): `a7b626e34aa62cfe`
- pico2-audio (`/dev/pico-audio`): `<fill in after flashing>`

```bash
# Find a new Pico's serial
udevadm info /dev/ttyACM1 | grep ID_SERIAL_SHORT

# Install / update rules
sudo cp shared/udev/99-pico-serial.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules && sudo udevadm trigger
ls -la /dev/pico-*
```

---

## Installing Services

```bash
# temp-sensor listener (persistent)
sudo cp projects/temp-sensor/system/pico-listener.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now pico-listener

# audio-speaker TTS timer (6:01 AM daily)
sudo cp projects/audio-speaker/system/tts-briefing.* /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now tts-briefing.timer

# Status check
systemctl status pico-listener tts-briefing.timer
journalctl -u pico-listener -f
```

---

## Data Flow

```
pico2-closet (/dev/pico-temp)
  → pico-listener.service
  → /mnt/shanebrain-raid/mega-dashboard/pico-data.json
  → mega-dashboard temp panel · morning briefing · Pironman5 LED alerts

Pi 5 (tts-briefing.timer, 06:01)
  → tts_briefing.py
  → espeak-ng + sox → 8kHz 8-bit WAV
  → /dev/pico-audio
  → pico2-audio → MAX98357A → speaker
```

---

## Adding a New Project

1. `mkdir projects/<name>/{firmware,host,system}`
2. Write `firmware/main.py` (MicroPython), `host/<name>.py` (Pi-side), `wiring.md`, `README.md`
3. Add udev rule in `shared/udev/99-pico-serial.rules` with the new unit's serial
4. Add systemd files in `system/` if needed
5. Add a row to the root `README.md` project table
6. Update this file's hardware table

---

## MicroPython Linting Note

Firmware files import MicroPython-only modules: `machine`, `ujson`, `utime`, `uos`. Standard Python linters (pylance, ruff) will flag these as missing imports. **Do not fix them.** They are correct for the target environment.

---

*Part of the [thebardchat](https://github.com/thebardchat) ecosystem · Faith · Family · Sobriety · Local AI*
