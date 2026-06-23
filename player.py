# player.py
from config import *


class Player:
    def __init__(self, player_id, x, y, name="Player"):
        self.id = player_id
        self.x = x * TILE_SIZE + TILE_SIZE // 2
        self.y = y * TILE_SIZE + TILE_SIZE // 2
        self.vx = 0
        self.vy = 0
        self.name = name
        self.speed = 4
        self.jump_power = 10
        self.on_ground = False
        self.finished = False
        self.alive = True
        self.spawn_x = self.x
        self.spawn_y = self.y
        self.game_map = None
        self.hook_active = False

    def respawn(self):
        self.x = self.spawn_x
        self.y = self.spawn_y
        self.vx = 0
        self.vy = 0
        self.alive = True
        self.finished = False

    def update(self):
        pass  # Физика обновляется в PhysicsEngine