#!/usr/bin/env python3
"""Maintainer-only acquisition of the licensed Ariadne purr; never runs on clients."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import subprocess
import tempfile
import urllib.request

SOURCE = "https://upload.wikimedia.org/wikipedia/commons/3/38/Cat_Purring.ogg"
SOURCE_PAGE = "https://commons.wikimedia.org/wiki/File:Cat_Purring.ogg"
LICENSE = "https://creativecommons.org/licenses/by-sa/3.0/"
SHA1 = "a1d96f0fdeed9c89c2a10ce1f7068f90d1a40573"
SIZE = 188608
RATE = 24000

def check_original(data, expected_size=SIZE, expected_hash=SHA1):
    if len(data) != expected_size or not data.startswith(b"OggS"):
        raise ValueError("Unexpected source container or size")
    if hashlib.sha1(data).hexdigest() != expected_hash:
        raise ValueError("Source checksum mismatch")

def pcm_metrics(path):
    raw = subprocess.check_output(["ffmpeg", "-nostdin", "-v", "error", "-i", str(path),
                                   "-ac", "1", "-ar", str(RATE), "-f", "s16le", "-"], timeout=30)
    if not raw or len(raw) % 2:
        raise ValueError("No decoded PCM")
    samples = [x[0] / 32768 for x in struct.iter_unpack("<h", raw)]
    result = {"duration": len(samples) / RATE,
              "rms": math.sqrt(sum(x*x for x in samples) / len(samples)),
              "peak": max(abs(x) for x in samples)}
    if not 12 <= result["duration"] <= 15 or result["rms"] < .003 or result["peak"] >= .999:
        raise ValueError(f"Audio quality gate failed: {result}")
    return result

def acquire(out):
    if out.exists():
        raise FileExistsError("Use a new output directory; existing assets are not overwritten")
    req = urllib.request.Request(SOURCE, headers={"User-Agent": "FreeCat/1.0 (https://github.com/AIPMAndy/FreeCat; licensed media verification)"})
    with urllib.request.urlopen(req, timeout=30) as response:
        data = response.read(SIZE + 1)
    check_original(data)
    with tempfile.TemporaryDirectory() as tmp:
        original = Path(tmp) / "ariadne.ogg"
        mp3 = Path(tmp) / "ariadne.mp3"
        original.write_bytes(data)
        original_metrics = pcm_metrics(original)
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", str(original),
                        "-map_metadata", "-1", "-ac", "1", "-ar", str(RATE),
                        "-c:a", "libmp3lame", "-b:a", "64k", str(mp3)], check=True, timeout=30)
        metrics = pcm_metrics(mp3)
        if mp3.stat().st_size > 150000:
            raise ValueError("MP3 exceeds size budget")
        report = {"source": SOURCE_PAGE, "author": "Sgerbic", "title": "Ariadne purring",
                  "license": LICENSE, "original_sha1": SHA1, "original_bytes": SIZE,
                  "original_metrics": original_metrics, "mp3_metrics": metrics,
                  "mp3_bytes": mp3.stat().st_size,
                  "mp3_sha256": hashlib.sha256(mp3.read_bytes()).hexdigest(),
                  "modifications": "Mono, 24 kHz, MP3 64 kbps; metadata removed; attribution retained in this report",
                  "limitations": "Digital signal checks only. Not a physical-speaker or listening test."}
        out.mkdir(parents=True, exist_ok=False)
        (out / "ariadne.ogg").write_bytes(data)
        (out / "ariadne.mp3").write_bytes(mp3.read_bytes())
        (out / "ATTRIBUTION.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))

def self_test():
    fixture = b"OggS test fixture"
    digest = hashlib.sha1(fixture).hexdigest()
    check_original(fixture, len(fixture), digest)
    for bad in (fixture[:-1], b"X" + fixture[1:], fixture[:-1] + b"!"):
        try:
            check_original(bad, len(fixture), digest)
        except ValueError:
            continue
        raise AssertionError("Bad fixture accepted")
    print("4 checksum/container checks passed; no real recording was downloaded by this test")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path)
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args()
    if args.self_test:
        self_test()
    elif args.out:
        acquire(args.out)
    else:
        p.error("Provide --out or --self-test")
