#!/usr/bin/env python3
"""Maintainer-only photo acquisition. Candidates are NOT automatically published."""
import argparse
import hashlib
import io
import json
import random
from pathlib import Path
import urllib.request
from PIL import Image, ImageOps, ImageFilter

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
    # Reduce dimensions from the original, never repeatedly resample or lower
    # quality below 72. Fail closed if the smallest useful image does not fit.
    for edge in (1600, 1440, 1280, 1120, 960):
        candidate = im.copy()
        candidate.thumbnail((edge, edge), Image.Resampling.LANCZOS)
        for quality in (88, 84, 80, 76, 72):
            out = io.BytesIO()
            candidate.save(out, "WEBP", quality=quality, method=6)
            data = out.getvalue()
            if len(data) <= BUDGET:
                with Image.open(io.BytesIO(data)) as check:
                    check.load()
                    assert check.size == candidate.size and check.format == "WEBP"
                return data, quality, candidate.size
        if max(candidate.size) <= 960:
            break
    raise ValueError("Candidate exceeds byte budget at minimum accepted size and quality")


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
                  "license_status": ("CC0 on author file page; structured data also lists CC BY-SA 4.0. Hold publication until reviewed." if key == "sonkiki" else "CC0 on file page; candidate only."),
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
    # A repeatable textured fixture forces a smaller candidate while preserving
    # source dimensions, image ratio and the same byte/quality limits.
    texture = Image.frombytes("RGB", (1200, 1600),
                              random.Random(38).randbytes(1200 * 1600 * 3))
    texture = texture.filter(ImageFilter.GaussianBlur(1.2))
    data, quality, dims = optimize(texture)
    assert texture.size == (1200, 1600)
    assert 960 <= max(dims) < 1600 and dims[0] * 4 == dims[1] * 3
    assert len(data) <= BUDGET and quality >= 72
    print("6 fixture checks passed; no real photo was downloaded by this test")

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
