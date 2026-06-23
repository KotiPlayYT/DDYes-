# analyze_map.py
import os
import struct


def analyze_map_safe(path):
    print(f"🔍 Analyzing: {path}")
    print("=" * 50)

    if not os.path.exists(path):
        print("❌ File not found!")
        return

    file_size = os.path.getsize(path)
    print(f"File size: {file_size} bytes")

    with open(path, 'rb') as f:
        # Пытаемся определить формат
        header = f.read(4)
        print(f"Header: {header}")

        if header == b'DDMP':
            print("✅ DDNet format")
            print("  This is a valid DDNet map")
        elif header == b'DATA':
            print("✅ Teeworlds DATA format")
            print("  This is a valid Teeworlds map")

            # Пытаемся прочитать базовую информацию
            f.seek(0)
            data = f.read()

            # Ищем паттерны тайлов
            tile_patterns = {
                b'\x80\x00': 'Start (128)',
                b'\x81\x00': 'Finish (129)',
                b'\x01\x00': 'Wall (1)',
                b'\x02\x00': 'Floor (2)',
                b'\x03\x00': 'Lava (3)',
                b'\x04\x00': 'Death (4)',
                b'\x07\x00': 'Hookable (7)',
                b'\x08\x00': 'NoHook (8)',
            }

            found_tiles = {}
            for pattern, name in tile_patterns.items():
                count = data.count(pattern)
                if count > 0:
                    found_tiles[name] = count

            if found_tiles:
                print(f"\n  Found tile patterns:")
                for name, count in found_tiles.items():
                    print(f"    {name}: {count}")

                # Пытаемся определить размер карты
                # Ищем максимальные координаты
                print("\n  Searching for map structure...")

                # Пропускаем первые 12 байт (заголовок)
                pos = 12

                # Ищем последовательности тайлов
                tile_data = []
                while pos < len(data) - 1:
                    if data[pos:pos + 2] in tile_patterns:
                        tile_data.append((pos, data[pos:pos + 2]))
                    pos += 1

                if tile_data:
                    print(f"  Found {len(tile_data)} tile positions")

            else:
                print("  No standard tile patterns found")
                print("  The map might be empty or corrupted")

        elif header == b'\x00\x00\x00\x00':
            print("✅ Old Teeworlds format")
            print("  This is a legacy Teeworlds map")
        else:
            print("⚠️ Unknown format")
            print(f"  First bytes: {header.hex()}")

        print("=" * 50)

        # Вывод первых 100 байт для анализа
        f.seek(0)
        raw = f.read(100)
        print("\nFirst 100 bytes (hex):")
        for i in range(0, len(raw), 16):
            hex_str = ' '.join(f'{b:02x}' for b in raw[i:i + 16])
            ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in raw[i:i + 16])
            print(f"  {i:04x}: {hex_str:<48} {ascii_str}")


if __name__ == '__main__':
    analyze_map_safe('maps/dm1.map')