# physics.py
from config import *
import math


class PhysicsEngine:
    def __init__(self, game_map):
        self.map = game_map
        self.gravity = GRAVITY
        self.friction = 0.9

    def update_player(self, player, keys):
        # Применяем ввод
        player.vx = 0
        if keys.get('left'):
            player.vx = -player.speed
        if keys.get('right'):
            player.vx = player.speed

        # Прыжок
        if keys.get('jump') and player.on_ground:
            player.vy = -player.jump_power
            player.on_ground = False

        # Гравитация
        player.vy += self.gravity

        # Ограничение скорости
        max_speed = 15
        player.vx = max(-max_speed, min(max_speed, player.vx))
        player.vy = max(-max_speed, min(max_speed, player.vy))

        # Движение по X
        new_x = player.x + player.vx
        if not self.check_collision(new_x, player.y, player):
            player.x = new_x
        else:
            player.vx = 0

        # Движение по Y
        new_y = player.y + player.vy
        if not self.check_collision(player.x, new_y, player):
            player.y = new_y
            player.on_ground = False
        else:
            if player.vy > 0:
                player.on_ground = True
            player.vy = 0

        # Проверка на смертельные тайлы
        if self.check_death(player.x, player.y):
            player.respawn()

        # Проверка финиша
        if self.check_finish(player.x, player.y):
            player.finished = True

    def check_collision(self, x, y, player):
        # Проверяем коллизию с тайлами
        tile_x = int(x // TILE_SIZE)
        tile_y = int(y // TILE_SIZE)

        # Проверяем все углы игрока
        corners = [
            (tile_x, tile_y),
            (tile_x + 1, tile_y),
            (tile_x, tile_y + 1),
            (tile_x + 1, tile_y + 1)
        ]

        for cx, cy in corners:
            if 0 <= cy < len(self.map.tiles) and 0 <= cx < len(self.map.tiles[0]):
                tile = self.map.tiles[cy][cx]
                if tile in [TILE_WALL, TILE_FLOOR, TILE_HOOKABLE]:
                    return True
        return False

    def check_death(self, x, y):
        tile_x = int(x // TILE_SIZE)
        tile_y = int(y // TILE_SIZE)

        if 0 <= tile_y < len(self.map.tiles) and 0 <= tile_x < len(self.map.tiles[0]):
            tile = self.map.tiles[tile_y][tile_x]
            return tile in [TILE_LAVA, TILE_DEATH]
        return False

    def check_finish(self, x, y):
        tile_x = int(x // TILE_SIZE)
        tile_y = int(y // TILE_SIZE)

        if 0 <= tile_y < len(self.map.tiles) and 0 <= tile_x < len(self.map.tiles[0]):
            return self.map.tiles[tile_y][tile_x] == TILE_FINISH
        return False