"""
Pure Python PNG icon generator for CIF Chrome Extension (Standard Library only).
Generates RGBA icons of sizes 16x16, 32x32, 48x48, and 128x128.
"""
import os
import zlib
import struct

def create_png(width: int, height: int, output_path: str):
    # Palette colors: Dark background with vibrant cyan/blue badge
    # RGBA format
    raw_data = bytearray()
    center_x = width / 2.0
    center_y = height / 2.0
    radius = min(center_x, center_y) * 0.88

    for y in range(height):
        # Filter byte 0 for scanline
        raw_data.append(0)
        for x in range(width):
            dx = x - center_x
            dy = y - center_y
            dist = (dx * dx + dy * dy) ** 0.5

            if dist <= radius:
                # Gradient from primary blue #2563eb (37, 99, 235) to cyan #06b6d4 (6, 182, 212)
                t = (x + y) / float(width + height)
                r = int(37 * (1 - t) + 6 * t)
                g = int(99 * (1 - t) + 182 * t)
                b = int(235 * (1 - t) + 212 * t)
                a = 255

                # Inner highlight ring
                if abs(dist - radius * 0.6) < (radius * 0.12):
                    r = min(255, r + 70)
                    g = min(255, g + 70)
                    b = 255
                # Center core dot
                if dist < radius * 0.25:
                    r, g, b = 255, 255, 255
            else:
                r, g, b, a = 0, 0, 0, 0

            raw_data.extend([r, g, b, a])

    # Compress IDAT chunk
    compressed = zlib.compress(bytes(raw_data), level=9)

    def make_chunk(chunk_type: bytes, data: bytes) -> bytes:
        length = struct.pack(">I", len(data))
        crc = struct.pack(">I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF)
        return length + chunk_type + data + crc

    # PNG Header
    png = b"\x89PNG\r\n\x1a\n"
    # IHDR chunk: width, height, bit_depth=8, color_type=6 (RGBA), compression=0, filter=0, interlace=0
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    png += make_chunk(b"IHDR", ihdr_data)
    # IDAT chunk
    png += make_chunk(b"IDAT", compressed)
    # IEND chunk
    png += make_chunk(b"IEND", b"")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(png)

def generate_all_icons(target_dir: str):
    sizes = [16, 32, 48, 128]
    for s in sizes:
        p = os.path.join(target_dir, f"icon{s}.png")
        create_png(s, s, p)
        print(f"Generated {p} ({s}x{s})")

if __name__ == "__main__":
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "extension", "icons")
    generate_all_icons(out)
