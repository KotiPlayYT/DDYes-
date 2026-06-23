# hooks.py
import math
from config import *


class HookSystem:
    def __init__(self):
        self.hooks = {}  # player_id -> {'active': bool, 'target_x': 0, 'target_y': 0, 'hit': False}

    def fire_hook(self, player, target_x, target_y, players):
        player_id = id(player)

        if player_id not in self.hooks:
            self.hooks[player_id] = {'active': False, 'target_x': 0, 'target_y': 0, 'hit': False}

        hook = self.hooks[player_id]

        if not hook['active']:
            hook['active'] = True
            hook['target_x'] = target_x
            hook['target_y'] = target_y
            hook['hit'] = False

            # Проверяем попадание в хукабельную стену или игрока
            hook['hit'] = self.check_hook_target(target_x, target_y, player, players)

    def update_hook(self, player, players):
        player_id = id(player)
        if player_id not in self.hooks:
            return

        hook = self.hooks[player_id]
        if not hook['active']:
            return

        # Проверяем длину хука
        dx = hook['target_x'] - player.x
        dy = hook['target_y'] - player.y
        distance = math.sqrt(dx * dx + dy * dy)

        if distance > MAX_HOOK_LENGTH:
            hook['active'] = False
            return

        # Если хук попал, тянем игрока
        if hook['hit']:
            pull_strength = 0.3
            player.vx += dx * pull_strength
            player.vy += dy * pull_strength
        else:
            # Возвращаем хук
            pass

    def check_hook_target(self, x, y, player, players):
        # Проверяем тайлы
        tile_x = int(x // TILE_SIZE)
        tile_y = int(y // TILE_SIZE)

        if 0 <= tile_y < len(player.game_map.tiles) and 0 <= tile_x < len(player.game_map.tiles[0]):
            tile = player.game_map.tiles[tile_y][tile_x]
            if tile == TILE_HOOKABLE:
                return True

        # Проверяем игроков
        for other in players:
            if other != player:
                dx = other.x - x
                dy = other.y - y
                if math.sqrt(dx * dx + dy * dy) < 20:  # Радиус попадания
                    return True

        return False

    def release_hook(self, player):
        player_id = id(player)
        if player_id in self.hooks:
            self.hooks[player_id]['active'] = False