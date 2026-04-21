# main.py — Pico 2 Audio Receiver
# Receives WAV over USB serial from Pi 5, plays via I2S to MAX98357A amp
#
# Hardware: Raspberry Pi Pico 2 (RP2350), MicroPython v1.24+
# Wiring:
#   GP10 → MAX98357A BCLK
#   GP11 → MAX98357A LRC
#   GP12 → MAX98357A DIN
#   3V3  → MAX98357A VIN
#   GND  → MAX98357A GND
#   MAX98357A SD pin → 10kΩ → VIN  (12dB gain, mono left channel)

import gc
import struct
import sys
import zlib
from machine import Pin, I2S

SERIAL_MAGIC = b"BRDG"
SERIAL_DONE  = b"DONE"
I2S_ID       = 0
I2S_SCK_PIN  = 10
I2S_WS_PIN   = 11
I2S_SD_PIN   = 12
CHUNK_SIZE   = 4096
I2S_IBUF     = 8000   # 1 second at 8kHz
WAV_HDR_SIZE = 44
WAV_SIZE_CAP = 300_000  # 300KB max (~37s at 8kHz 8-bit)


def read_exactly(n: int) -> bytes:
    buf  = bytearray(n)
    view = memoryview(buf)
    pos  = 0
    while pos < n:
        chunk = sys.stdin.buffer.read(n - pos)
        if chunk:
            ln = len(chunk)
            view[pos:pos + ln] = chunk
            pos += ln
    return bytes(buf)


def parse_wav_header(header: bytes):
    if header[:4] != b"RIFF" or header[8:12] != b"WAVE":
        raise ValueError("not WAV")
    channels    = struct.unpack_from("<H", header, 22)[0]
    sample_rate = struct.unpack_from("<I", header, 24)[0]
    bits        = struct.unpack_from("<H", header, 34)[0]
    return sample_rate, bits, channels


def play_wav(wav_bytes: bytes) -> None:
    sample_rate, bits, channels = parse_wav_header(wav_bytes[:WAV_HDR_SIZE])
    print(f"play: {sample_rate}Hz {bits}bit ch={channels}")

    audio_out = I2S(
        I2S_ID,
        sck=Pin(I2S_SCK_PIN),
        ws=Pin(I2S_WS_PIN),
        sd=Pin(I2S_SD_PIN),
        mode=I2S.TX,
        bits=bits,
        format=I2S.MONO if channels == 1 else I2S.STEREO,
        rate=sample_rate,
        ibuf=I2S_IBUF,
    )
    try:
        pcm  = memoryview(wav_bytes)[WAV_HDR_SIZE:]
        off  = 0
        size = len(pcm)
        while off < size:
            end = min(off + CHUNK_SIZE, size)
            audio_out.write(pcm[off:end])
            off = end
        audio_out.write(bytearray(CHUNK_SIZE))  # flush
    finally:
        audio_out.deinit()


def ack(msg: bytes) -> None:
    sys.stdout.buffer.write(msg)
    sys.stdout.flush()


def main():
    print("pico-audio ready")
    sys.stdout.flush()

    while True:
        gc.collect()
        try:
            magic = read_exactly(4)
            if magic != SERIAL_MAGIC:
                print(f"bad magic: {magic!r}")
                continue

            meta = read_exactly(8)
            wav_size, expected_crc = struct.unpack("<II", meta)
            print(f"incoming: {wav_size}B crc={expected_crc:#010x}")

            if wav_size > WAV_SIZE_CAP:
                print(f"too large: {wav_size}")
                ack(b"ERR\n")
                continue

            wav_bytes = read_exactly(wav_size)
            trailer   = read_exactly(4)

            if trailer != SERIAL_DONE:
                print(f"bad trailer: {trailer!r}")
                ack(b"ERR\n")
                continue

            actual_crc = zlib.crc32(wav_bytes) & 0xFFFFFFFF
            if actual_crc != expected_crc:
                print(f"CRC mismatch: got {actual_crc:#010x}")
                ack(b"ERR\n")
                continue

            ack(b"ACK\n")
            print("playing...")
            play_wav(wav_bytes)
            print("done")

        except Exception as e:
            print(f"error: {e}")
            try:
                ack(b"ERR\n")
            except Exception:
                pass


main()
