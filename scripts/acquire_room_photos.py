#!/usr/bin/env python3
"""Maintainer-only photo acquisition. Candidates are NOT automatically published."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import urllib.request
from PIL import Image, ImageOps

CANDIDATES = [
    ("sonkiki", "Cat-sleeping-curled-up.jpg", "8/87", 3648391,
     "5aaae8ddd38e7f9443df7ad725e3e75a905ee3a1", (3024, 4032), "Sonkiki"),
    ("rammya", "Sleeping_cute_cat.jpg", "6/6d", 115130,
     "abc56b77385cf5dc11bb89a42c21878b76bbed14", (1280, 960), "Rammya kannan"),
]
BUDGET = 250000
Image.MAX_IMAGE_PIXELS = 20_000_000

def verify(data, size, digest, dimensions):
    if len(data) != size or hashlib.sha1(data).hexdigest() != digest:
        raise ValueError("Source size or checksum mismatch")
    with Image.open(io.BytesIO(data)) as im:
        if im.format != "JPEG" or im.size not in (dimensions, dimensions[::-1]):
            raise ValueError("Unexpected source image format or size")
        im.verify()
    with Image.open(io.BytesIO(data)) as im:
        im.load()
        oriented = ImageOps.exif_transpose(im)
        if oriented.size != dimensions:
            raise ValueError("Unexpected oriented source dimensions")
        return oriented.convert("RGB")

def optimize(im):
    im.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
    for quality in (88, 84, 80, 76, 72):
        out = io.BytesIO()
        im.save(out, "WEBP", quality=quality, method=6)
        data = out.getvalue()
        if len(data) <= BUDGET:
            with Image.open(io.BytesIO(data)) as check:
                check.load()
                assert check.size == im.size and check.format == "WEBP"
            return data, quality, im.size
    raise ValueError("Candidate exceeds byte budget without aggressive compression")

def acquire(out):
    out.mkdir(parents=True, exist_ok=False)
    reports = []
    for key, filename, folder, size, digest, dimensions, author in CANDIDATES:
        url = f"https://upload.wikimedia.org/wikipedia/commons/{folder}/{filename}"
        req = urllib.request.Request(url, headers={"User-Agent": "FreeCat/1.0 (https://github.com/AIPMAndy/FreeCat; licensed media verification)"})
        with urllib.request.urlopen(req, timeout=40) as response:
            original = response.read(size + 1)
        im = verify(original, size, digest, dimensions)
        oriented = im.size
        data, quality, output_size = optimize(im)
        (out / f"{key}.webp").write_bytes(data)
        report = {"candidate": key, "source": "https://commons.wikimedia.org/wiki/File:" + filename,
                  "original_url": url, "author": author,
                  "license": "https://creativecommons.org/publicdomain/zero/1.0/",
                  "original_sha1": digest, "original_bytes": size,
                  "original_dimensions": dimensions, "oriented_dimensions": oriented,
                  "webp_dimensions": output_size, "webp_bytes": len(data),
                  "webp_sha256": hashlib.sha256(data).hexdigest(), "quality": quality,
                  "modifications": "EXIF orientation applied; resized without cropping or upscaling; WebP encoding; metadata removed",
                  "status": "Requires human visual review, anatomy mapping and browser acceptance before use."}
        reports.append(report)
    (out / "ATTRIBUTION.json").write_text(json.dumps(reports, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(reports, indent=2))

def self_test():
    original = io.BytesIO()
    Image.new("RGB", (120, 80), "orange").save(original, "JPEG")
    b = original.getvalue()
    h = hashlib.sha1(b).hexdigest()
    im = verify(b, len(b), h, (120, 80))
    for bad, sz, digest, dims in [(b[:-1], len(b), h, (120,80)),
                                  (b, len(b), "0"*40, (120,80)),
                                  (b, len(b), h, (80,120))]:
        try:
            verify(bad, sz, digest, dims)
        except ValueError:
            continue
        raise AssertionError("Invalid fixture accepted")
    data, _, dims = optimize(im)
    assert len(data) <= BUDGET and dims == (120,80)
    print("5 fixture checks passed; no real photo was downloaded by this test")

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
