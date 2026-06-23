# map_parser.py
import struct
import os
import zlib
import sys
from config import *


def load(self, path):
    with open(path, 'rb') as f:
        # Проверяем первые 4 байта
        header = f.read(4)

        # Если это текстовый файл (начинается с # или буквы)
        if header and (header[0] == 35 or header[0] > 127):  # '#' или не ASCII
            print(f"⚠️ Text file detected, using test map")
            self.create_test_map()
            return

class DDMap:
    def __init__(self, path):
        self.tiles = []
        self.width = 0
        self.height = 0
        self.spawn = None
        self.finish = None

        if not os.path.exists(path):
            print(f"⚠️ Map not found: {path}")
            self.create_test_map()
            return

        try:
            self.load(path)
        except Exception as e:
            print(f"❌ Error loading map: {e}")
            print("📝 Creating test map instead...")
            self.create_test_map()

    def load(self, path):
        with open(path, 'rb') as f:
            # Проверяем первые 4 байта
            header = f.read(4)

            if header == b'DDMP':
                print("📦 DDNet format detected")
                self.load_ddmp(f)
            elif header == b'DATA':
                print("📦 Teeworlds DATA format detected")
                self.load_teeworlds_safe(f)
            else:
                print(f"⚠️ Unknown header: {header[:4]}")
                self.create_test_map()

    def load_teeworlds_safe(self, f):
        """Безопасная загрузка Teeworlds карты"""
        try:
            # Пытаемся прочитать версию
            version_data = f.read(4)
            if len(version_data) < 4:
                print("⚠️ File too small")
                self.create_test_map()
                return

            version = struct.unpack('<I', version_data)[0]
            print(f"  Version: {version}")

            # Пытаемся прочитать размеры
            size_data = f.read(8)
            if len(size_data) < 8:
                print("⚠️ Cannot read map size")
                self.create_test_map()
                return

            width, height = struct.unpack('<II', size_data)

            # Проверяем разумность размеров
            if width > 5000 or height > 5000 or width < 1 or height < 1:
                print(f"⚠️ Suspicious map size: {width}x{height}")
                print("  Using default size 50x50")
                width, height = 50, 50

            print(f"  Map size: {width}x{height}")

            self.width = width
            self.height = height
            self.tiles = [[TILE_AIR] * width for _ in range(height)]

            # Пытаемся найти игровой слой
            self.find_game_layer(f, width, height)

            # Если не нашли спавн, создаем по центру
            if self.spawn is None:
                self.spawn = (width // 2, height // 2)
                if 0 <= self.spawn[1] < height and 0 <= self.spawn[0] < width:
                    self.tiles[self.spawn[1]][self.spawn[0]] = TILE_START

            if self.finish is None:
                self.finish = (width - 3, height - 3)
                if 0 <= self.finish[1] < height and 0 <= self.finish[0] < width:
                    self.tiles[self.finish[1]][self.finish[0]] = TILE_FINISH

            print(f"✅ Map loaded: {self.width}x{self.height}")
            print(f"📍 Spawn: {self.spawn}")
            print(f"🏁 Finish: {self.finish}")

        except Exception as e:
            print(f"❌ Error loading map: {e}")
            self.create_test_map()

    def find_game_layer(self, f, width, height):
        """Поиск игрового слоя в файле"""
        # Возвращаемся к началу
        f.seek(0)
        data = f.read()

        # Ищем паттерны тайлов
        patterns = [
            b'\x80\x00',  # Старт (128)
            b'\x81\x00',  # Финиш (129)
            b'\x01\x00',  # Стена (1)
            b'\x02\x00',  # Пол (2)
            b'\x03\x00',  # Лава (3)
            b'\x04\x00',  # Смерть (4)
        ]

        found_any = False

        for i in range(len(data) - 1):
            for pattern in patterns:
                if data[i:i + 2] == pattern:
                    # Нашли возможный тайл
                    if not found_any:
                        print("  Found tile data in file")
                        found_any = True

                    # Пытаемся интерпретировать как тайлы
                    self.extract_tiles_from_data(data[i:], width, height)
                    return

        if not found_any:
            print("  No tile data found, creating default map")
            self.create_default_tiles(width, height)

    def extract_tiles_from_data(self, data, width, height):
        """Извлечение тайлов из данных"""
        tile_count = 0
        pos = 0

        while pos < len(data) - 1 and tile_count < width * height:
            index = data[pos]
            flags = data[pos + 1] if pos + 1 < len(data) else 0
            pos += 2

            x = tile_count % width
            y = tile_count // width

            if y < height:
                tile_type = self.get_tile_type(index, flags)
                self.tiles[y][x] = tile_type

                if index == 128:
                    self.spawn = (x, y)
                    self.tiles[y][x] = TILE_START
                elif index == 129:
                    self.finish = (x, y)
                    self.tiles[y][x] = TILE_FINISH

            tile_count += 1

            if tile_count % 1000 == 0:
                print(f"    Parsed {tile_count} tiles...")

        print(f"  Parsed {tile_count} tiles")

    def create_default_tiles(self, width, height):
        """Создание карты по умолчанию"""
        self.tiles = [[TILE_AIR] * width for _ in range(height)]

        # Границы
        for i in range(width):
            if 0 < i < height:
                self.tiles[0][i] = TILE_WALL
                self.tiles[height - 1][i] = TILE_WALL
        for i in range(height):
            if 0 < i < width:
                self.tiles[i][0] = TILE_WALL
                self.tiles[i][width - 1] = TILE_WALL

        # Несколько платформ
        platforms = [
            (height // 4, width // 5, width // 3),
            (height // 2, width // 4, width // 2),
            (height // 4 * 3, width // 3, width // 5 * 4),
        ]

        for y, x_start, x_end in platforms:
            for x in range(x_start, x_end):
                if 0 <= y < height and 0 <= x < width:
                    self.tiles[y][x] = TILE_FLOOR

    def get_tile_type(self, index, flags):
        """Определение типа тайла"""
        tile_map = {
            0: TILE_AIR,
            1: TILE_WALL,
            2: TILE_FLOOR,
            3: TILE_LAVA,
            4: TILE_DEATH,
            5: TILE_FINISH,
            6: TILE_START,
            7: TILE_HOOKABLE,
            8: TILE_NOHOOK,
            128: TILE_START,
            129: TILE_FINISH,
        }

        # Проверяем флаги
        if flags & 1:
            return TILE_WALL
        elif flags & 2:
            return TILE_FLOOR
        elif flags & 4:
            return TILE_LAVA
        elif flags & 8:
            return TILE_DEATH
        elif flags & 16:
            return TILE_FINISH
        elif flags & 32:
            return TILE_START
        elif flags & 64:
            return TILE_HOOKABLE
        elif flags & 128:
            return TILE_NOHOOK

        return tile_map.get(index, TILE_AIR)

    def load_ddmp(self, f):
        """Загрузка DDMP формата"""
        try:
            version = struct.unpack('<I', f.read(4))[0]
            print(f"  Version: {version}")

            layer_count = struct.unpack('<I', f.read(4))[0]
            print(f"  Layers: {layer_count}")

            for i in range(layer_count):
                layer_type = struct.unpack('<I', f.read(4))[0]
                if layer_type == 1:
                    self.parse_tile_layer_ddmp(f)
                else:
                    # Пропускаем другие слои
                    size_data = f.read(4)
                    if size_data:
                        size = struct.unpack('<I', size_data)[0]
                        f.seek(size, 1)

            if self.spawn is None or self.finish is None:
                self.create_test_map()

        except Exception as e:
            print(f"  Error loading DDMP: {e}")
            self.create_test_map()

    def parse_tile_layer_ddmp(self, f):
        try:
            version = struct.unpack('<I', f.read(4))[0]
            flags = struct.unpack('<I', f.read(4))[0]

            width = struct.unpack('<I', f.read(4))[0]
            height = struct.unpack('<I', f.read(4))[0]

            self.width = width
            self.height = height
            self.tiles = [[TILE_AIR] * width for _ in range(height)]

            data_size = struct.unpack('<I', f.read(4))[0]

            if data_size > 0:
                compressed_data = f.read(data_size)
                try:
                    tile_data = zlib.decompress(compressed_data)
                except:
                    tile_data = compressed_data

                pos = 0
                for y in range(height):
                    for x in range(width):
                        if pos + 2 <= len(tile_data):
                            index = tile_data[pos]
                            flags = tile_data[pos + 1]
                            pos += 2

                            self.tiles[y][x] = self.get_tile_type(index, flags)

                            if index == 128:
                                self.spawn = (x, y)
                            elif index == 129:
                                self.finish = (x, y)

            print(f"  Tile layer: {width}x{height}")

        except Exception as e:
            print(f"  Error parsing tile layer: {e}")

    def create_test_map(self):
        """Создание тестовой карты"""
        print("🏗️ Creating test map...")

        self.width = 30
        self.height = 20
        self.tiles = [[TILE_AIR] * self.width for _ in range(self.height)]

        # Границы
        for i in range(self.width):
            self.tiles[0][i] = TILE_WALL
            self.tiles[self.height - 1][i] = TILE_WALL
        for i in range(self.height):
            self.tiles[i][0] = TILE_WALL
            self.tiles[i][self.width - 1] = TILE_WALL

        # Платформы
        platforms = [
            (8, 5, 14),
            (12, 3, 8),
            (15, 20, 27),
        ]

        for y, x_start, x_end in platforms:
            for x in range(x_start, x_end):
                if 0 <= y < self.height and 0 <= x < self.width:
                    self.tiles[y][x] = TILE_FLOOR

        # Хукабельные стены
        hookable = [(6, 7), (6, 8), (7, 7), (7, 8)]
        for y, x in hookable:
            if 0 <= y < self.height and 0 <= x < self.width:
                self.tiles[y][x] = TILE_HOOKABLE

        # Лава
        lava = [(14, 10), (14, 11), (14, 12)]
        for y, x in lava:
            if 0 <= y < self.height and 0 <= x < self.width:
                self.tiles[y][x] = TILE_LAVA

        # Спавн
        self.spawn = (5, 3)
        if 0 <= self.spawn[1] < self.height and 0 <= self.spawn[0] < self.width:
            self.tiles[self.spawn[1]][self.spawn[0]] = TILE_START


        # Финиш
        self.finish = (25, 17)
        if 0 <= self.finish[1] < self.height and 0 <= self.finish[0] < self.width:
            self.tiles[self.finish[1]][self.finish[0]] = TILE_FINISH

        print("✅ Test map created successfully!")
        print(f"📍 Spawn: {self.spawn}")
        print(f"🏁 Finish: {self.finish}")