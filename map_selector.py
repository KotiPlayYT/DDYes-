# map_selector.py
import os
import random
from create_map import *


def select_map():
    """Интерактивный выбор карты"""
    print("=" * 60)
    print("🗺️  MAP SELECTOR")
    print("=" * 60)

    # Список доступных карт
    maps = {
        '1': ('Easy', create_map_easy),
        '2': ('Medium', create_map_medium),
        '3': ('Hard', create_map_hard),
        '4': ('Random', create_random_map),
        '5': ('Generate all', None),
    }

    print("\nAvailable maps:")
    for key, (name, _) in maps.items():
        print(f"  {key}. {name}")

    choice = input("\nSelect map (1-5): ").strip()

    if choice == '5':
        create_all_maps()
        return

    if choice in maps:
        name, creator = maps[choice]
        if creator:
            print(f"\n🎲 Creating {name} map...")
            tiles, width, height, spawn, finish = creator()
            filename = f"{name.lower()}_{random.randint(100, 999)}"
            save_map(tiles, width, height, spawn, finish, filename)
            print(f"\n✅ Map created: maps/{filename}.map")
    else:
        print("❌ Invalid choice!")


if __name__ == '__main__':
    select_map()