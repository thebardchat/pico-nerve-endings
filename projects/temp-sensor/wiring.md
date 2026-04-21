# Wiring — temp-sensor

## Bill of Materials

| Part | Where | Cost |
|------|-------|------|
| Raspberry Pi Pico 2 (RP2350) | Adafruit / Pimoroni / Digikey | ~$5 |
| Micro-USB data cable | any | — |

No additional hardware required. The RP2350 has an onboard temperature sensor on ADC channel 4.

---

## Wiring Diagram

```
Raspberry Pi Pico 2
───────────────────
USB (Micro-USB) ──► Pi 5 USB port

(No external wiring needed — uses onboard ADC4 temp sensor)
```

---

## Output Format

Firmware sends JSON over USB serial at 115200 baud, newline-terminated:

```json
{
  "uptime_s": 3600,
  "device": "pico2-closet",
  "temp_f": 72.3,
  "temp_c": 22.4,
  "reading": 720
}
```

`reading` is a monotonic counter (increments each cycle). `uptime_s` is seconds since Pico boot.

---

## Multiple Units

To run temp sensors on other nodes (Pulsar, Bullfrog, Jaxton):
- Flash same `firmware/main.py` with `DEVICE_NAME` changed to match the node
- On Windows nodes: COM port instead of `/dev/ttyACM*`
- Update `shared/udev/99-pico-serial.rules` with each unit's serial number
