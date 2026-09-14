#!/usr/bin/env python3
"""Generate or restore assets/app.ico for Windows GUI."""
from pathlib import Path
import base64
import sys

ROOT = Path(__file__).resolve().parent

def write_embedded() -> Path:
    # embedded multi-size ICO (built offline); no Pillow required
    path = ROOT / "app.ico"
    # Load from sibling if present, else minimal placeholder is wrong —
    # full payload written by repo maintainer path:
    data_path = ROOT / "app.ico.b64"
    if data_path.exists():
        path.write_bytes(base64.b64decode(data_path.read_text().strip()))
        return path
    raise SystemExit("assets/app.ico.b64 missing — run with Pillow once")

def try_pillow() -> bool:
    try:
        from PIL import Image, ImageDraw
        import struct, io
    except ImportError:
        return False

    def make_icon(size: int):
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        margin = max(1, size // 16)
        bg = (36, 40, 48, 255)
        accent = (88, 166, 255, 255)
        green = (63, 185, 80, 255)
        amber = (210, 153, 34, 255)
        d.rounded_rectangle([margin, margin, size - margin - 1, size - margin - 1],
                            radius=max(2, size // 5), fill=bg)
        d.rounded_rectangle([margin, margin, size - margin - 1, margin + max(4, size // 4)],
                            radius=max(2, size // 8), fill=accent)
        y0 = size // 2 + max(2, size // 16)
        for i, col in enumerate([accent, green, amber]):
            y = y0 + i * max(4, size // 8)
            th = max(2, size // 14)
            if y + th < size - margin:
                d.rounded_rectangle([size // 4, y, size - size // 4, y + th],
                                    radius=max(1, th // 2), fill=col)
        r = max(2, size // 12)
        d.ellipse([size - margin - 2 * r - 1, margin + 2, size - margin - 1, margin + 2 + 2 * r],
                  fill=green)
        return img

    sizes = [16, 32, 48, 64, 128, 256]
    pngs = []
    for s in sizes:
        buf = io.BytesIO()
        make_icon(s).save(buf, format="PNG")
        pngs.append((s, buf.getvalue()))
    num = len(pngs)
    header = struct.pack("<HHH", 0, 1, num)
    entries, blobs = [], []
    offset = 6 + 16 * num
    for s, data in pngs:
        w = 0 if s >= 256 else s
        h = 0 if s >= 256 else s
        entries.append(struct.pack("<BBBBHHII", w, h, 0, 0, 1, 32, len(data), offset))
        blobs.append(data)
        offset += len(data)
    ico = header + b"".join(entries) + b"".join(blobs)
    (ROOT / "app.ico").write_bytes(ico)
    (ROOT / "app.ico.b64").write_text(base64.b64encode(ico).decode("ascii"))
    make_icon(256).save(ROOT / "app.png")
    return True

def main():
    if try_pillow():
        print("OK generated with Pillow:", ROOT / "app.ico")
        return
    data_path = ROOT / "app.ico.b64"
    if data_path.exists():
        p = write_embedded()
        print("OK wrote embedded icon:", p)
        return
    print("Need Pillow once: pip install pillow && python assets/generate_icon.py", file=sys.stderr)
    sys.exit(1)

if __name__ == "__main__":
    main()
