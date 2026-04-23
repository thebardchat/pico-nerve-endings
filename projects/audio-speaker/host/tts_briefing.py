#!/usr/bin/env python3
"""
tts_briefing.py — Morning Chaos Briefing Audio
Generates briefing text, converts to WAV via espeak-ng + sox,
streams over USB serial to Pico 2 audio speaker.

Dependencies: espeak-ng, sox (apt), pyserial (pip)
Usage: python3 tts_briefing.py [--port /dev/pico-audio] [--dry-run]
"""

import argparse
import struct
import subprocess
import sys
import zlib
from pathlib import Path

sys.path.insert(0, "/mnt/shanebrain-raid/shanebrain-core/shanebrain-briefing")
from briefing import build_briefing

SERIAL_PORT   = "/dev/pico-audio"
BAUD_RATE     = 115200
WAV_RAW_PATH  = Path("/tmp/chaos_briefing_raw.wav")
WAV_OUT_PATH  = Path("/tmp/chaos_briefing.wav")
CHUNK_SIZE    = 4096


def build_briefing_text() -> str:
    return build_briefing()


def generate_wav(text: str) -> None:
    subprocess.run(
        ["espeak-ng", "-v", "en-us", "-s", "145", "-a", "180", "-g", "5",
         "-w", str(WAV_RAW_PATH), text],
        check=True, capture_output=True, timeout=30
    )
    subprocess.run(
        ["sox", str(WAV_RAW_PATH), "-r", "8000", "-b", "8", "-c", "1",
         "-e", "unsigned-integer", str(WAV_OUT_PATH)],
        check=True, capture_output=True, timeout=15
    )
    WAV_RAW_PATH.unlink(missing_ok=True)


def stream_wav(port: str) -> bool:
    import serial

    wav_bytes = WAV_OUT_PATH.read_bytes()
    size      = len(wav_bytes)
    checksum  = zlib.crc32(wav_bytes) & 0xFFFFFFFF
    header    = b"BRDG" + struct.pack("<II", size, checksum)

    print(f"[tts] WAV: {size} bytes ({size/8000:.1f}s @ 8kHz), CRC32: {checksum:#010x}")
    print(f"[tts] Opening {port} ...")

    with serial.Serial(port, BAUD_RATE, timeout=15) as ser:
        ser.reset_input_buffer()
        ser.write(header)
        offset = 0
        while offset < size:
            ser.write(wav_bytes[offset: offset + CHUNK_SIZE])
            offset += CHUNK_SIZE
        ser.write(b"DONE")
        ser.flush()
        print(f"[tts] Sent — waiting for ACK ...")
        ack = ser.read(4).strip()
        if ack == b"ACK":
            print("[tts] Pico ACK — playback started")
            return True
        print(f"[tts] Unexpected response: {ack!r}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Morning Chaos Briefing TTS")
    parser.add_argument("--port",     default=SERIAL_PORT, help="Serial port for Pico 2")
    parser.add_argument("--dry-run",  action="store_true",  help="Generate WAV only, no serial send")
    parser.add_argument("--local",    action="store_true",  help="Play via local audio (aplay) instead of Pico 2")
    parser.add_argument("--text",     default=None,         help="Override briefing text")
    args = parser.parse_args()

    text = args.text or build_briefing_text()
    print(f"[tts] Briefing: {text[:100]}...")

    print("[tts] Generating WAV ...")
    generate_wav(text)
    print(f"[tts] WAV ready: {WAV_OUT_PATH.stat().st_size} bytes")

    if args.dry_run:
        print(f"[tts] Dry run — WAV at {WAV_OUT_PATH}, skipping playback")
        return

    if args.local:
        subprocess.run(["aplay", str(WAV_OUT_PATH)], check=True)
        return

    success = stream_wav(args.port)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
