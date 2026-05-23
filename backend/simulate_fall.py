"""
Quick demo script — sends a real JPEG to the backend to test the pipeline.

Usage:
  python simulate_fall.py [image.jpg] [--device-id <id>] [--url <server_url>]

Defaults:
  - Generates a small blank JPEG if no image is given (just tests connectivity)
  - device-id: demo-device
  - url: http://localhost:8080
"""

import argparse
import io
import sys

import requests
from PIL import Image


def make_blank_jpeg() -> bytes:
    """Generate a minimal 320x240 grey JPEG for connectivity testing."""
    img = Image.new("RGB", (320, 240), color=(128, 128, 128))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("image", nargs="?", help="Path to JPEG file")
    parser.add_argument("--device-id", default="demo-device")
    parser.add_argument("--url", default="http://localhost:8080")
    args = parser.parse_args()

    if args.image:
        with open(args.image, "rb") as f:
            image_bytes = f.read()
        print(f"Sending {args.image} ({len(image_bytes)} bytes)…")
    else:
        image_bytes = make_blank_jpeg()
        print(f"No image provided — sending blank JPEG ({len(image_bytes)} bytes)…")

    resp = requests.post(
        f"{args.url}/analyze",
        data=image_bytes,
        headers={
            "X-Device-ID": args.device_id,
            "Content-Type": "image/jpeg",
        },
        timeout=30,
    )

    print(f"Status: {resp.status_code}")
    print(resp.json())


if __name__ == "__main__":
    main()
