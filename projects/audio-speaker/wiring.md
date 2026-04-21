# Wiring — audio-speaker

## Bill of Materials (~$15)

| Part | Where | Cost |
|------|-------|------|
| Raspberry Pi Pico 2 (RP2350) | Adafruit / Pimoroni / Digikey | ~$5 |
| Adafruit MAX98357A I2S Amp Breakout (PID 3006) | Adafruit | ~$5 |
| 3" 4Ω 3W speaker | Adafruit PID 4296 / Amazon | ~$3 |
| 10kΩ resistor | any | — |
| Micro-USB data cable | any | — |

---

## Wiring Diagram

```
Pico 2 (RP2350)          MAX98357A Breakout
────────────────          ─────────────────
GP10  ─────────────────► BCLK
GP11  ─────────────────► LRC
GP12  ─────────────────► DIN
3V3   ─────────────────► VIN
GND   ─────────────────► GND
                          SD ──[10kΩ]──► VIN   (12dB gain, mono left channel)
                          +  ─────────► Speaker +
                          -  ─────────► Speaker -
```

## Gain Reference

| SD pin connection | Gain |
|-------------------|------|
| SD → 10kΩ → VIN | 12 dB (recommended) |
| SD → 100kΩ → VIN | 9 dB (quieter) |
| SD → VIN (direct) | max gain |
| SD floating | 9 dB |
| SD → GND | mute / shutdown |

## I2S Pin Reference (RP2350 MicroPython)

```python
I2S(0, sck=Pin(10), ws=Pin(11), sd=Pin(12), mode=I2S.TX, ...)
```

`id=0` uses RP2350's first I2S peripheral. If GP10/11/12 are occupied, `id=1` uses GP18/19/20.
