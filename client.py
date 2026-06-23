# client.py
import pygame
import socket
import threading
import time
import sys
import os
import math
from config import *
from map_parser import DDMap
from network import send_data, recv_data


class GameClient:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((1024, 768))
        pygame.display.set_caption("DDNet Clone")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.big_font = pygame.font.Font(None, 48)
        self.debug_font = pygame.font.Font(None, 18)

        print("🗺️ Creating empty map...")
        self.map = DDMap('')
        self.map.width = 0
        self.map.height = 0
        self.map.tiles = []
        self.map.spawn = (5, 5)
        self.map.finish = (25, 17)

        # Подключение
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(2)
            self.sock.connect((SERVER_HOST, SERVER_PORT))
            self.sock.settimeout(None)
            print("✅ Connected to server")
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            sys.exit(1)

        self.running = True
        self.players = {}
        self.finished_players = []
        self.chat_messages = []
        self.game_mode = "RACE"
        self.my_id = None
        self.connected = True
        self.map_name = "Unknown"
        self.map_number = 0
        self.map_type = "Unknown"

        # Ввод
        self.keys = {'left': False, 'right': False, 'jump': False}
        self.chat_input = ''
        self.chat_active = False

        # Камера
        self.camera_x = 0
        self.camera_y = 0
        self.camera_follow = True
        self.camera_speed = 0.1

        # Отладка
        self.debug_info = []
        self.show_debug = True
        self.frame_count = 0
        self.last_fps_update = time.time()
        self.fps = 0
        self.mouse_x = 0
        self.mouse_y = 0
        self.last_state_request = 0

    def send_input(self):
        while self.running and self.connected:
            try:
                data = {
                    'type': 'input',
                    'keys': self.keys.copy()
                }
                send_data(self.sock, data)
                time.sleep(0.02)
            except Exception as e:
                print(f"⚠️ Send error: {e}")
                self.connected = False
                break

    def request_state(self):
        while self.running and self.connected:
            try:
                current_time = time.time()
                if current_time - self.last_state_request > 0.05:
                    send_data(self.sock, {'type': 'get_state'})
                    self.last_state_request = current_time
                time.sleep(0.01)
            except Exception as e:
                print(f"⚠️ State request error: {e}")
                self.connected = False
                break

    def receive_state(self):
        while self.running and self.connected:
            try:
                data = recv_data(self.sock)
                if data:
                    msg_type = data.get('type', '')

                    if msg_type == 'welcome':
                        self.my_id = data.get('player_id')
                        spawn_x = data.get('spawn_x', 0)
                        spawn_y = data.get('spawn_y', 0)
                        self.map_name = data.get('map_name', 'Unknown')
                        self.map_number = data.get('map_number', 0)

                        # Определяем тип карты
                        if '_' in self.map_name:
                            self.map_type = self.map_name.split('_')[0]

                        tiles = data.get('tiles', [])
                        if tiles:
                            self.map.tiles = tiles
                            self.map.width = len(tiles[0]) if tiles else 30
                            self.map.height = len(tiles)
                            self.map.spawn = (int(spawn_x // TILE_SIZE), int(spawn_y // TILE_SIZE))
                            print(f"✅ Map loaded from server: {self.map.width}x{self.map.height}")

                        print(f"🎮 Welcome! Your ID: {self.my_id}")
                        print(f"📍 Position: ({spawn_x}, {spawn_y})")
                        print(f"🗺️ Map: {self.map_name} #{self.map_number}")
                        print(f"🎨 Type: {self.map_type}")
                        print(f"📐 Size: {self.map.width}x{self.map.height}")
                        self.camera_x = spawn_x - 512
                        self.camera_y = spawn_y - 384

                    elif msg_type == 'map_change':
                        map_name = data.get('map_name', 'Unknown')
                        map_number = data.get('map_number', 0)
                        width = data.get('width', 30)
                        height = data.get('height', 20)
                        spawn = data.get('spawn', (5, 5))
                        finish = data.get('finish', (25, 17))
                        tiles = data.get('tiles', [])

                        # Определяем тип карты
                        if '_' in map_name:
                            self.map_type = map_name.split('_')[0]
                        else:
                            self.map_type = "Unknown"

                        print(f"\n{'=' * 60}")
                        print(f"🔄 MAP CHANGED!")
                        print(f"   Name: {map_name} #{map_number}")
                        print(f"   Type: {self.map_type}")
                        print(f"   Size: {width}x{height}")
                        print(f"   Spawn: {spawn}")
                        print(f"   Finish: {finish}")
                        print(f"   Tiles received: {len(tiles)} rows")
                        if tiles and len(tiles) > 0:
                            print(f"   First row length: {len(tiles[0])}")
                        print(f"{'=' * 60}\n")

                        # Обновляем все данные карты
                        self.map_name = map_name
                        self.map_number = map_number
                        self.map.width = width
                        self.map.height = height
                        self.map.spawn = spawn
                        self.map.finish = finish

                        # КРИТИЧЕСКИ ВАЖНО: обновляем тайлы
                        if tiles and len(tiles) > 0:
                            self.map.tiles = tiles
                            print(f"✅ Tiles updated: {len(tiles)}x{len(tiles[0])}")
                        else:
                            self.map.tiles = [[TILE_AIR] * width for _ in range(height)]
                            print("⚠️ No tiles received, creating empty map")

                        # Настраиваем камеру на новый спавн
                        if spawn:
                            self.camera_x = spawn[0] * TILE_SIZE - 512
                            self.camera_y = spawn[1] * TILE_SIZE - 384

                        # Сбрасываем игроков
                        self.players = {}
                        self.finished_players = []
                        self.my_id = None

                        print("🔄 Map update complete!")

                    elif msg_type == 'state' or 'players' in data:
                        if 'players' in data:
                            self.players = data['players']
                            if not self.my_id and self.players:
                                self.my_id = list(self.players.keys())[0]

                            if self.my_id and self.my_id in self.players:
                                player = self.players[self.my_id]
                                if self.camera_follow:
                                    target_x = player.get('x', 0) - 512
                                    target_y = player.get('y', 0) - 384
                                    self.camera_x += (target_x - self.camera_x) * self.camera_speed
                                    self.camera_y += (target_y - self.camera_y) * self.camera_speed

                        if 'finished' in data:
                            self.finished_players = data['finished']
                        if 'mode' in data:
                            self.game_mode = data['mode']
                        if 'chat' in data:
                            self.chat_messages = data['chat']
                        if 'map_name' in data:
                            self.map_name = data['map_name']
                            if '_' in self.map_name:
                                self.map_type = self.map_name.split('_')[0]
                        if 'map_number' in data:
                            self.map_number = data['map_number']

                    elif msg_type == 'chat_message':
                        sender = data.get('sender', '')
                        message = data.get('message', '')
                        self.chat_messages.append(f"{sender}: {message}")
                        if len(self.chat_messages) > 20:
                            self.chat_messages = self.chat_messages[-20:]

            except Exception as e:
                print(f"⚠️ Receive error: {e}")
                self.connected = False
                break

    def draw_map(self):
        if not self.map.tiles:
            return

        color_map = {
            TILE_AIR: (30, 30, 35),
            TILE_WALL: (80, 80, 90),
            TILE_FLOOR: (139, 90, 43),
            TILE_LAVA: (255, 60, 0),
            TILE_DEATH: (180, 0, 180),
            TILE_FINISH: (255, 215, 0),
            TILE_START: (0, 255, 100),
            TILE_HOOKABLE: (64, 164, 223),
            TILE_NOHOOK: (139, 0, 0),
        }

        for y, row in enumerate(self.map.tiles):
            for x, tile in enumerate(row):
                screen_x = x * TILE_SIZE - self.camera_x
                screen_y = y * TILE_SIZE - self.camera_y

                if screen_x < -TILE_SIZE or screen_x > 1024 + TILE_SIZE:
                    continue
                if screen_y < -TILE_SIZE or screen_y > 768 + TILE_SIZE:
                    continue

                color = color_map.get(tile, (30, 30, 35))

                if tile != TILE_AIR:
                    pygame.draw.rect(self.screen, color,
                                     (screen_x, screen_y, TILE_SIZE, TILE_SIZE))

                    if tile == TILE_WALL:
                        pygame.draw.rect(self.screen, (100, 100, 110),
                                         (screen_x, screen_y, TILE_SIZE, TILE_SIZE), 1)
                    elif tile == TILE_LAVA:
                        brightness = int(100 + 55 * abs((time.time() * 3 + x + y) % 2 - 1))
                        lava_color = (255, brightness // 2, 0)
                        pygame.draw.rect(self.screen, lava_color,
                                         (screen_x + 2, screen_y + 2,
                                          TILE_SIZE - 4, TILE_SIZE - 4))
                    elif tile == TILE_FINISH:
                        pulse = int(50 + 50 * abs((time.time() * 2 + x + y) % 2 - 1))
                        pygame.draw.rect(self.screen, (255, 215, 0),
                                         (screen_x, screen_y, TILE_SIZE, TILE_SIZE),
                                         max(1, pulse // 10))
                    elif tile == TILE_START:
                        pulse = int(20 + 30 * abs((time.time() * 1.5) % 2 - 1))
                        pygame.draw.rect(self.screen, (0, 200, 100),
                                         (screen_x, screen_y, TILE_SIZE, TILE_SIZE),
                                         max(1, pulse // 5))
                    elif tile == TILE_HOOKABLE:
                        pygame.draw.line(self.screen, (200, 200, 255),
                                         (screen_x + 8, screen_y + 8),
                                         (screen_x + 24, screen_y + 24), 2)
                        pygame.draw.line(self.screen, (200, 200, 255),
                                         (screen_x + 24, screen_y + 8),
                                         (screen_x + 8, screen_y + 24), 2)

        if self.show_debug:
            for x in range(0, self.map.width * TILE_SIZE, TILE_SIZE * 5):
                screen_x = x - self.camera_x
                if 0 <= screen_x <= 1024:
                    pygame.draw.line(self.screen, (60, 60, 70),
                                     (screen_x, 0), (screen_x, 768), 1)
            for y in range(0, self.map.height * TILE_SIZE, TILE_SIZE * 5):
                screen_y = y - self.camera_y
                if 0 <= screen_y <= 768:
                    pygame.draw.line(self.screen, (60, 60, 70),
                                     (0, screen_y), (1024, screen_y), 1)

    def draw_players(self):
        for pid, player in self.players.items():
            x = player.get('x', 0) - self.camera_x
            y = player.get('y', 0) - self.camera_y

            if x < -50 or x > 1074 or y < -50 or y > 818:
                screen_center_x = 512
                screen_center_y = 384
                player_x = player.get('x', 0)
                player_y = player.get('y', 0)
                angle = math.atan2(
                    player_y - self.camera_y - screen_center_y,
                    player_x - self.camera_x - screen_center_x
                )
                arrow_x = 512 + math.cos(angle) * 400
                arrow_y = 384 + math.sin(angle) * 300
                arrow_x = max(20, min(1004, arrow_x))
                arrow_y = max(20, min(748, arrow_y))
                pygame.draw.circle(self.screen, (255, 255, 0),
                                   (int(arrow_x), int(arrow_y)), 15, 2)
                name = player.get('name', 'Unknown')
                name_text = self.font.render(f"{name} →", True, (255, 255, 0))
                self.screen.blit(name_text, (arrow_x - 30, arrow_y - 20))
                continue

            # Тень
            pygame.draw.circle(self.screen, (0, 0, 0), (int(x + 2), int(y + 2)), 16)

            # Тело
            if pid == self.my_id:
                colors = [(0, 255, 100), (0, 200, 80)]
            else:
                colors = [(255, 140, 0), (200, 100, 0)]

            pygame.draw.circle(self.screen, colors[0], (int(x), int(y)), 16)
            pygame.draw.circle(self.screen, colors[1], (int(x), int(y)), 12)

            # Глаза
            vx = player.get('vx', 0)
            if vx > 0:
                eye_x_offset = 3
            elif vx < 0:
                eye_x_offset = -3
            else:
                eye_x_offset = 0

            pygame.draw.circle(self.screen, (255, 255, 255),
                               (int(x - 5 + eye_x_offset), int(y - 4)), 5)
            pygame.draw.circle(self.screen, (0, 0, 0),
                               (int(x - 4 + eye_x_offset), int(y - 4)), 2)
            pygame.draw.circle(self.screen, (255, 255, 255),
                               (int(x + 5 + eye_x_offset), int(y - 4)), 5)
            pygame.draw.circle(self.screen, (0, 0, 0),
                               (int(x + 6 + eye_x_offset), int(y - 4)), 2)

            # Имя
            name = player.get('name', 'Unknown')
            name_text = self.font.render(name, True, (255, 255, 255))
            name_rect = name_text.get_rect(center=(x, y - 30))
            pygame.draw.rect(self.screen, (0, 0, 0),
                             (name_rect.x - 4, name_rect.y - 2,
                              name_rect.width + 8, name_rect.height + 4))
            self.screen.blit(name_text, name_rect)

            if pid in self.finished_players:
                finish_text = self.big_font.render("🏁", True, (255, 215, 0))
                self.screen.blit(finish_text, (x - 20, y - 55))

            # Свой игрок
            if pid == self.my_id:
                pulse = int(2 + 2 * abs((time.time() * 2) % 2 - 1))
                pygame.draw.circle(self.screen, (0, 255, 0),
                                   (int(x), int(y)), 20 + pulse, 2)
                pos_text = self.debug_font.render(
                    f"({int(player.get('x', 0))}, {int(player.get('y', 0))})",
                    True, (200, 255, 200)
                )
                self.screen.blit(pos_text, (x - 40, y - 50))

                # Индикатор двойного прыжка
                if player.get('on_ground', False):
                    jump_text = self.debug_font.render("🦘 Ready", True, (100, 255, 100))
                    self.screen.blit(jump_text, (x + 25, y - 20))
                else:
                    jump_text = self.debug_font.render("🦘 x2", True, (255, 255, 100))
                    self.screen.blit(jump_text, (x + 25, y - 20))

    def draw_ui(self):
        # FPS
        fps_text = self.font.render(f"FPS: {self.fps}", True, (255, 255, 255))
        self.screen.blit(fps_text, (10, 10))

        # Режим
        mode_text = self.font.render(f"Mode: {self.game_mode}", True, (255, 255, 255))
        self.screen.blit(mode_text, (10, 35))

        # Игроки
        players_text = self.font.render(f"Players: {len(self.players)}", True, (255, 255, 255))
        self.screen.blit(players_text, (10, 60))

        # Финиш
        finished_text = self.font.render(f"Finished: {len(self.finished_players)}", True, (255, 255, 255))
        self.screen.blit(finished_text, (10, 85))

        # Карта с типом
        map_info = f"Map: {self.map_name} #{self.map_number} ({self.map.width}x{self.map.height})"
        map_text = self.font.render(map_info, True, (255, 255, 255))
        self.screen.blit(map_text, (10, 110))

        # Тип карты
        type_text = self.font.render(f"Type: {self.map_type}", True, (200, 200, 100))
        self.screen.blit(type_text, (10, 135))

        # Позиция
        if self.my_id and self.my_id in self.players:
            player = self.players[self.my_id]
            pos_text = f"Pos: ({int(player.get('x', 0))}, {int(player.get('y', 0))})"
            pos_surface = self.font.render(pos_text, True, (255, 255, 255))
            self.screen.blit(pos_surface, (10, 160))

        if self.my_id:
            id_text = self.font.render(f"ID: {self.my_id}", True, (200, 200, 200))
            self.screen.blit(id_text, (10, 185))

        # Подсказка по двойному прыжку
        jump_hint = self.font.render("🦘 Double Jump: SPACE twice in air!", True, (255, 255, 100))
        self.screen.blit(jump_hint, (10, 210))

        # Отладка
        if self.show_debug:
            y = 235
            for info in self.debug_info[-10:]:
                debug_text = self.debug_font.render(info, True, (200, 200, 200))
                self.screen.blit(debug_text, (10, y))
                y += 18

        # Чат
        y = 700
        for msg in self.chat_messages[-5:]:
            chat_text = self.font.render(msg, True, (255, 255, 255))
            self.screen.blit(chat_text, (10, y))
            y -= 25

        if self.chat_active:
            pygame.draw.rect(self.screen, (60, 60, 70), (10, 730, 600, 30))
            chat_input_text = self.font.render(f"> {self.chat_input}", True, (255, 255, 255))
            self.screen.blit(chat_input_text, (15, 735))

        # Управление
        if not self.chat_active:
            controls = [
                "←/→ - Move",
                "SPACE - Jump (x2 for double jump!)",
                "E - Hook",
                "O - Skip map",  # НОВАЯ КЛАВИША
                "T - Chat",
                "F - Toggle follow",
                "D - Toggle debug",
                "/newmap - Change map (in chat)"
            ]
            y = 730
            for control in controls:
                control_text = self.debug_font.render(control, True, (150, 150, 160))
                self.screen.blit(control_text, (800, y))
                y += 18

    def run(self):
        # Потоки
        send_thread = threading.Thread(target=self.send_input, daemon=True)
        send_thread.start()

        state_thread = threading.Thread(target=self.request_state, daemon=True)
        state_thread.start()

        receive_thread = threading.Thread(target=self.receive_state, daemon=True)
        receive_thread.start()

        print("🎮 Game started!")
        print("📋 Controls: Arrow keys to move, SPACE to jump")
        print("🦘 DOUBLE JUMP: Press SPACE twice in the air!")
        print("🎨 4 MAP TYPES: PLATFORMS, MAZE, TOWERS, RANDOM")
        print("⌨️  Press O to skip current map!")
        print("🔧 Press F to toggle camera follow, D for debug")
        print("💬 Type /newmap in chat to change map")

        while self.running:
            self.clock.tick(60)

            # FPS
            self.frame_count += 1
            if time.time() - self.last_fps_update > 1:
                self.fps = self.frame_count
                self.frame_count = 0
                self.last_fps_update = time.time()

            # События
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                elif event.type == pygame.MOUSEMOTION:
                    self.mouse_x, self.mouse_y = event.pos

                elif event.type == pygame.KEYDOWN:
                    if self.chat_active:
                        if event.key == pygame.K_RETURN:
                            if self.chat_input:
                                try:
                                    send_data(self.sock, {
                                        'type': 'chat',
                                        'message': self.chat_input
                                    })
                                except:
                                    pass
                                self.chat_input = ''
                            self.chat_active = False
                        elif event.key == pygame.K_ESCAPE:
                            self.chat_active = False
                            self.chat_input = ''
                        else:
                            self.chat_input += event.unicode
                    else:
                        # НОВАЯ КЛАВИША O - пропуск карты
                        if event.key == pygame.K_o:
                            print("⏭️ Skipping map...")
                            try:
                                send_data(self.sock, {'type': 'skip_map'})
                            except:
                                pass
                        elif event.key == pygame.K_t:
                            self.chat_active = True
                            self.chat_input = ''
                        elif event.key == pygame.K_f:
                            self.camera_follow = not self.camera_follow
                            print(f"Camera follow: {self.camera_follow}")
                        elif event.key == pygame.K_d:
                            self.show_debug = not self.show_debug
                            print(f"Debug: {self.show_debug}")
                        elif event.key == pygame.K_LEFT:
                            self.keys['left'] = True
                        elif event.key == pygame.K_RIGHT:
                            self.keys['right'] = True
                        elif event.key == pygame.K_SPACE:
                            self.keys['jump'] = True
                        elif event.key == pygame.K_e:
                            mouse_x, mouse_y = pygame.mouse.get_pos()
                            hook_data = {
                                'type': 'hook',
                                'x': mouse_x + self.camera_x,
                                'y': mouse_y + self.camera_y
                            }
                            try:
                                send_data(self.sock, hook_data)
                            except:
                                pass

                elif event.type == pygame.KEYUP:
                    if not self.chat_active:
                        if event.key == pygame.K_LEFT:
                            self.keys['left'] = False
                        elif event.key == pygame.K_RIGHT:
                            self.keys['right'] = False
                        elif event.key == pygame.K_SPACE:
                            self.keys['jump'] = False

            # Отладка
            if self.show_debug:
                self.debug_info = [
                    f"Camera: ({int(self.camera_x)}, {int(self.camera_y)})",
                    f"Follow: {self.camera_follow}",
                    f"My ID: {self.my_id}",
                    f"Players: {len(self.players)}",
                    f"Connected: {self.connected}",
                    f"Map: {self.map_name} #{self.map_number}",
                    f"Type: {self.map_type}",
                ]

                if self.my_id and self.my_id in self.players:
                    player = self.players[self.my_id]
                    on_ground = "YES" if player.get('on_ground', False) else "NO"
                    self.debug_info.append(f"On ground: {on_ground}")
                    self.debug_info.append(f"Player pos: ({int(player.get('x', 0))}, {int(player.get('y', 0))})")

                world_x = self.mouse_x + self.camera_x
                world_y = self.mouse_y + self.camera_y
                tile_x = int(world_x // TILE_SIZE)
                tile_y = int(world_y // TILE_SIZE)
                if 0 <= tile_y < self.map.height and 0 <= tile_x < self.map.width:
                    tile_type = self.map.tiles[tile_y][tile_x]
                    tile_names = {
                        TILE_AIR: "AIR",
                        TILE_WALL: "WALL",
                        TILE_FLOOR: "FLOOR",
                        TILE_LAVA: "LAVA",
                        TILE_DEATH: "DEATH",
                        TILE_FINISH: "FINISH",
                        TILE_START: "START",
                        TILE_HOOKABLE: "HOOKABLE",
                        TILE_NOHOOK: "NOHOOK",
                    }
                    self.debug_info.append(f"Tile: ({tile_x}, {tile_y}) = {tile_names.get(tile_type, 'UNKNOWN')}")

            # Рендеринг
            self.screen.fill((30, 30, 35))
            self.draw_map()
            self.draw_players()
            self.draw_ui()

            pygame.display.flip()

        self.running = False
        self.connected = False
        try:
            self.sock.close()
        except:
            pass
        pygame.quit()
        print("👋 Game closed")


if __name__ == '__main__':
    client = GameClient()
    client.run()