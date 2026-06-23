# create_map.py
import os
import random
from config import *


def create_map_easy():
    """Легкая карта"""
    print("🏗️ Creating EASY map...")
    width, height = 30, 20
    tiles = [[TILE_AIR] * width for _ in range(height)]

    # Границы
    for i in range(width):
        tiles[0][i] = TILE_WALL
        tiles[height - 1][i] = TILE_WALL
    for i in range(height):
        tiles[i][0] = TILE_WALL
        tiles[i][width - 1] = TILE_WALL

    # Простые платформы
    platforms = [
        (height - 2, 2, width - 2),  # Пол
        (height - 5, 5, 12),  # Платформа
        (height - 8, 15, 22),  # Платформа
    ]
    for y, x_start, x_end in platforms:
        for x in range(x_start, x_end):
            if 0 <= y < height and 0 <= x < width:
                tiles[y][x] = TILE_FLOOR

    # Спавн и финиш
    spawn = (3, height - 3)
    finish = (width - 3, height - 3)
    tiles[spawn[1]][spawn[0]] = TILE_START
    tiles[finish[1]][finish[0]] = TILE_FINISH

    return tiles, width, height, spawn, finish


def create_map_medium():
    """Средняя карта с препятствиями"""
    print("🏗️ Creating MEDIUM map...")
    width, height = 40, 25
    tiles = [[TILE_AIR] * width for _ in range(height)]

    # Границы
    for i in range(width):
        tiles[0][i] = TILE_WALL
        tiles[height - 1][i] = TILE_WALL
    for i in range(height):
        tiles[i][0] = TILE_WALL
        tiles[i][width - 1] = TILE_WALL

    # Платформы с лавой
    platforms = [
        (height - 2, 2, width - 2),
        (height - 5, 4, 10),
        (height - 8, 12, 18),
        (height - 11, 20, 26),
        (height - 14, 28, 34),
    ]
    for y, x_start, x_end in platforms:
        for x in range(x_start, x_end):
            if 0 <= y < height and 0 <= x < width:
                tiles[y][x] = TILE_FLOOR

    # Лава
    lava_spots = [(height - 3, 14, 16), (height - 9, 22, 24)]
    for y, x_start, x_end in lava_spots:
        for x in range(x_start, x_end):
            if 0 <= y < height and 0 <= x < width:
                tiles[y][x] = TILE_LAVA

    # Хукабельные стены
    hookable = [(height - 4, 8, 10), (height - 7, 16, 18)]
    for y, x_start, x_end in hookable:
        for x in range(x_start, x_end):
            if 0 <= y < height and 0 <= x < width:
                tiles[y][x] = TILE_HOOKABLE

    spawn = (3, height - 3)
    finish = (width - 3, height - 3)
    tiles[spawn[1]][spawn[0]] = TILE_START
    tiles[finish[1]][finish[0]] = TILE_FINISH

    return tiles, width, height, spawn, finish


def create_map_hard():
    """Сложная карта с множеством препятствий"""
    print("🏗️ Creating HARD map...")
    width, height = 50, 30
    tiles = [[TILE_AIR] * width for _ in range(height)]

    # Границы
    for i in range(width):
        tiles[0][i] = TILE_WALL
        tiles[height - 1][i] = TILE_WALL
    for i in range(height):
        tiles[i][0] = TILE_WALL
        tiles[i][width - 1] = TILE_WALL

    # Много платформ с разрывами
    for i in range(5, height - 2, 3):
        x_start = random.randint(3, width // 3)
        x_end = random.randint(width // 2, width - 3)
        for x in range(x_start, x_end):
            if 0 <= i < height and 0 <= x < width:
                tiles[i][x] = TILE_FLOOR

    # Лава и опасности
    for i in range(0, height - 2, 4):
        x = random.randint(5, width - 5)
        if 0 <= i < height and 0 <= x < width:
            tiles[i][x] = TILE_LAVA
            tiles[i][x + 1] = TILE_LAVA

    # Хукабельные стены
    for i in range(3, height - 2, 5):
        x = random.randint(3, width - 3)
        if 0 <= i < height and 0 <= x < width:
            tiles[i][x] = TILE_HOOKABLE

    # Стены-препятствия
    for i in range(3, height - 2, 4):
        for j in range(3, 6):
            x = random.randint(4, width - 4)
            if 0 <= i + j < height and 0 <= x < width:
                tiles[i + j][x] = TILE_WALL

    spawn = (3, height - 3)
    finish = (width - 3, height - 3)
    tiles[spawn[1]][spawn[0]] = TILE_START
    tiles[finish[1]][finish[0]] = TILE_FINISH

    return tiles, width, height, spawn, finish


def create_random_map():
    """Полностью случайная карта"""
    print("🏗️ Creating RANDOM map...")
    width = random.randint(30, 50)
    height = random.randint(20, 30)
    tiles = [[TILE_AIR] * width for _ in range(height)]

    # Границы
    for i in range(width):
        tiles[0][i] = TILE_WALL
        tiles[height - 1][i] = TILE_WALL
    for i in range(height):
        tiles[i][0] = TILE_WALL
        tiles[i][width - 1] = TILE_WALL

    # Случайные платформы
    num_platforms = random.randint(5, 15)
    for _ in range(num_platforms):
        y = random.randint(3, height - 4)
        x_start = random.randint(2, width - 10)
        x_end = random.randint(x_start + 3, width - 2)
        for x in range(x_start, x_end):
            if 0 <= y < height and 0 <= x < width:
                tiles[y][x] = TILE_FLOOR

    # Случайные препятствия
    num_obstacles = random.randint(3, 10)
    for _ in range(num_obstacles):
        y = random.randint(3, height - 4)
        x = random.randint(2, width - 2)
        tile_type = random.choice([TILE_WALL, TILE_LAVA, TILE_DEATH, TILE_HOOKABLE])
        if 0 <= y < height and 0 <= x < width:
            tiles[y][x] = tile_type

    spawn = (2, height - 3)
    finish = (width - 3, height - 3)
    tiles[spawn[1]][spawn[0]] = TILE_START
    tiles[finish[1]][finish[0]] = TILE_FINISH

    return tiles, width, height, spawn, finish


def save_map(tiles, width, height, spawn, finish, filename):
    """Сохранение карты в файл"""
    os.makedirs('maps', exist_ok=True)

    # Сохраняем как текстовую карту
    with open(f'maps/{filename}.map', 'w') as f:
        f.write(f"# Map: {filename}\n")
        f.write(f"# Size: {width}x{height}\n")
        f.write(f"# Spawn: {spawn}\n")
        f.write(f"# Finish: {finish}\n")
        f.write("\n")

        for y in range(height):
            row = []
            for x in range(width):
                tile = tiles[y][x]
                if tile == TILE_AIR:
                    row.append('.')
                elif tile == TILE_WALL:
                    row.append('#')
                elif tile == TILE_FLOOR:
                    row.append('=')
                elif tile == TILE_LAVA:
                    row.append('~')
                elif tile == TILE_DEATH:
                    row.append('X')
                elif tile == TILE_FINISH:
                    row.append('F')
                elif tile == TILE_START:
                    row.append('S')
                elif tile == TILE_HOOKABLE:
                    row.append('H')
                elif tile == TILE_NOHOOK:
                    row.append('N')
                else:
                    row.append('?')
            f.write(''.join(row) + '\n')

    print(f"✅ Map saved: maps/{filename}.map")
    print(f"📐 Size: {width}x{height}")
    print(f"📍 Spawn: {spawn}")
    print(f"🏁 Finish: {finish}")


def create_all_maps():
    """Создание всех типов карт"""
    print("=" * 60)
    print("🗺️  MAP GENERATOR")
    print("=" * 60)

    # Создаем разные карты
    maps = [
        ("easy", create_map_easy),
        ("medium", create_map_medium),
        ("hard", create_map_hard),
        ("random1", create_random_map),
        ("random2", create_random_map),
        ("random3", create_random_map),
    ]

    for name, creator in maps:
        print("\n" + "-" * 40)
        tiles, width, height, spawn, finish = creator()
        save_map(tiles, width, height, spawn, finish, name)

    print("\n" + "=" * 60)
    print("✅ All maps created!")
    print("📁 Available maps:")
    for name, _ in maps:
        print(f"  - maps/{name}.map")
    print("=" * 60)

    # Сохраняем список карт
    with open('maps/map_list.txt', 'w') as f:
        for name, _ in maps:
            f.write(f"{name}.map\n")


if __name__ == '__main__':
    create_all_maps()