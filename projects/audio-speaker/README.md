# audio-speaker

**Receives a WAV file over USB serial from a host Pi and plays it through a speaker via I2S.**

Designed to pair with the [Morning Chaos Briefing](https://github.com/thebardchat/morning-chaos-briefing) — espeak-ng generates the briefing on the Pi, streams it over serial to this Pico, and you hear it out loud at 6 AM.

---

## Hardware Required

See [wiring.md](wiring.md) for full pinout and BOM. ~$15 in parts:
- Raspberry Pi Pico 2 (RP2350)
- Adafruit MAX98357A I2S Amp Breakout
- 3" 4Ω 3W speaker
- 10kΩ resistor

---

## Flash the Firmware

```bash
# Stop any service using the port first if needed
sudo systemctl stop tts-briefing 2>/dev/null || true

# Flash via mpremote
mpremote connect /dev/pico-audio cp firmware/main.py :main.py
mpremote connect /dev/pico-audio reset
```

Or use Thonny: File → Save as → MicroPython device → `main.py`

---

## Host Setup (Pi 5)

**1. Install dependencies:**
```bash
sudo apt install -y espeak-ng sox
pip install pyserial --break-system-packages
```

**2. Install udev rule** (stable `/dev/pico-audio` symlink):
```bash
# Get the Pico's serial first:
udevadm info /dev/ttyACM1 | grep ID_SERIAL_SHORT
# Fill in <NEW_PICO_SERIAL> in shared/udev/99-pico-serial.rules, then:
sudo cp ../../shared/udev/99-pico-serial.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules && sudo udevadm trigger
```

**3. Test manually:**
```bash
python3 host/tts_briefing.py --dry-run     # generate WAV, no serial send
python3 host/tts_briefing.py               # generate + stream to /dev/pico-audio
```

**4. Install systemd timer (6:01 AM daily):**
```bash
sudo cp system/tts-briefing.service system/tts-briefing.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now tts-briefing.timer
```

---

## Serial Protocol

The host streams a framed WAV over USB serial:

```
b"BRDG" + uint32(wav_size) + uint32(crc32) + wav_bytes + b"DONE"
```

Pico responds `b"ACK\n"` on success, `b"ERR\n"` on failure. WAV must be 8kHz 8-bit mono (≤300KB ≈ 37 seconds).

---

## Fork This

Clone and adapt for any TTS/audio use case. Change the text in `host/tts_briefing.py → build_briefing_text()` to say whatever you want. The Pico firmware is generic — it plays any valid WAV you send it.
