# server.py
import socket
import threading
import time
import json
import sys
import os
import random
from config import *
from network import send_data, recv_data


class PhysicsEngine:
    def __init__(self, game_map):
        self.map = game_map
        self.gravity = 0.5
        self.jump_count = {}

    def update_player(self, player, keys):
        if player.id not in self.jump_count:
            self.jump_count[player.id] = 0

        # Горизонтальное движение
        if keys.get('left'):
            player.vx = -4
        elif keys.get('right'):
            player.vx = 4
        else:
            player.vx *= 0.85
            if abs(player.vx) < 0.1:
                player.vx = 0

        # ДВОЙНОЙ ПРЫЖОК
        if keys.get('jump'):
            if not hasattr(player, 'jump_key_was_pressed'):
                player.jump_key_was_pressed = False

            if not player.jump_key_was_pressed:
                player.jump_key_was_pressed = True

                if player.on_ground:
                    player.vy = -10
                    player.on_ground = False
                    self.jump_count[player.id] = 1

                elif self.jump_count[player.id] < 2:
                    player.vy = -9
                    self.jump_count[player.id] += 1
                    print(f"🦘 {player.id}: Double Jump!")
        else:
            player.jump_key_was_pressed = False

        # Гравитация
        player.vy += self.gravity

        # Ограничение скорости
        player.vx = max(-10, min(10, player.vx))
        player.vy = max(-15, min(15, player.vy))

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
                self.jump_count[player.id] = 0
            player.vy = 0

        # Проверка на смерть
        if self.check_death(player.x, player.y):
            player.respawn()
            self.jump_count[player.id] = 0

        # Проверка финиша
        if self.check_finish(player.x, player.y):
            player.finished = True

    def check_collision(self, x, y, player):
        margin = 3
        points = [
            (x - 10 + margin, y - 10 + margin),
            (x + 10 - margin, y - 10 + margin),
            (x - 10 + margin, y + 10 - margin),
            (x + 10 - margin, y + 10 - margin),
        ]

        for px, py in points:
            tile_x = int(px // TILE_SIZE)
            tile_y = int(py // TILE_SIZE)

            if 0 <= tile_y < len(self.map.tiles) and 0 <= tile_x < len(self.map.tiles[0]):
                tile = self.map.tiles[tile_y][tile_x]
                if tile in [TILE_WALL, TILE_FLOOR, TILE_HOOKABLE]:
                    return True
        return False

    def check_death(self, x, y):
        tile_x = int(x // TILE_SIZE)
        tile_y = int(y // TILE_SIZE)
        if 0 <= tile_y < len(self.map.tiles) and 0 <= tile_x < len(self.map.tiles[0]):
            return self.map.tiles[tile_y][tile_x] in [TILE_LAVA, TILE_DEATH]
        return False

    def check_finish(self, x, y):
        tile_x = int(x // TILE_SIZE)
        tile_y = int(y // TILE_SIZE)
        if 0 <= tile_y < len(self.map.tiles) and 0 <= tile_x < len(self.map.tiles[0]):
            return self.map.tiles[tile_y][tile_x] == TILE_FINISH
        return False


class Player:
    def __init__(self, player_id, x, y, name="Player"):
        self.id = player_id
        self.x = x * TILE_SIZE + TILE_SIZE // 2
        self.y = y * TILE_SIZE + TILE_SIZE // 2
        self.vx = 0
        self.vy = 0
        self.name = name
        self.on_ground = False
        self.finished = False
        self.alive = True
        self.spawn_x = self.x
        self.spawn_y = self.y

    def respawn(self):
        self.x = self.spawn_x
        self.y = self.spawn_y
        self.vx = 0
        self.vy = 0
        self.alive = True
        self.finished = False


class ChatSystem:
    def __init__(self):
        self.messages = []

    def add_message(self, sender, message):
        timestamp = time.strftime("%H:%M:%S")
        self.messages.append(f"[{timestamp}] {sender}: {message}")
        if len(self.messages) > 50:
            self.messages = self.messages[-50:]

    def get_messages(self, count=10):
        return self.messages[-count:]


def create_random_map():
    """Создание случайной карты с уникальным дизайном"""
    print("🎲 Generating random map...")

    # Случайный размер
    width = random.randint(25, 45)
    height = random.randint(18, 28)
    tiles = [[TILE_AIR] * width for _ in range(height)]

    # Границы
    for i in range(width):
        tiles[0][i] = TILE_WALL
        tiles[height - 1][i] = TILE_WALL
    for i in range(height):
        tiles[i][0] = TILE_WALL
        tiles[i][width - 1] = TILE_WALL

    # ВЫБИРАЕМ СЛУЧАЙНЫЙ ТИП КАРТЫ
    map_type = random.choice(['platforms', 'maze', 'towers', 'random'])

    if map_type == 'platforms':
        # Много платформ на разных уровнях
        num_platforms = random.randint(10, 20)
        for _ in range(num_platforms):
            y = random.randint(3, height - 4)
            length = random.randint(4, 12)
            x = random.randint(2, width - length - 2)
            for i in range(length):
                if 0 <= y < height and 0 <= x + i < width:
                    tiles[y][x + i] = TILE_FLOOR

        # Добавляем стены-препятствия
        num_walls = random.randint(3, 8)
        for _ in range(num_walls):
            y = random.randint(3, height - 5)
            wall_height = random.randint(2, 5)
            x = random.randint(3, width - 4)
            for i in range(wall_height):
                if 0 <= y + i < height and 0 <= x < width:
                    tiles[y + i][x] = TILE_WALL

    elif map_type == 'maze':
        # Лабиринт из стен
        for y in range(2, height - 2, 3):
            for x in range(2, width - 2, 3):
                if random.random() < 0.4:
                    tiles[y][x] = TILE_WALL
                    if random.random() < 0.5 and y + 1 < height:
                        tiles[y + 1][x] = TILE_WALL

        # Пол на дне
        for x in range(2, width - 2):
            tiles[height - 2][x] = TILE_FLOOR

        # Несколько платформ
        for _ in range(5, 10):
            y = random.randint(4, height - 4)
            x = random.randint(3, width - 4)
            if random.random() < 0.6:
                tiles[y][x] = TILE_FLOOR
                tiles[y][x + 1] = TILE_FLOOR

    elif map_type == 'towers':
        # Башни и платформы
        num_towers = random.randint(3, 6)
        for t in range(num_towers):
            x_base = random.randint(4, width - 6)
            tower_height = random.randint(4, 8)
            for y in range(height - tower_height - 1, height - 1):
                if 0 <= y < height and 0 <= x_base < width:
                    tiles[y][x_base] = TILE_WALL
                    tiles[y][x_base + 1] = TILE_WALL

            # Платформа на вершине башни
            if tower_height > 3:
                y_top = height - tower_height - 1
                for i in range(4):
                    if 0 <= y_top < height and 0 <= x_base - 1 + i < width:
                        tiles[y_top][x_base - 1 + i] = TILE_FLOOR

        # Мосты между башнями
        for _ in range(random.randint(2, 4)):
            y = random.randint(height - 8, height - 4)
            x_start = random.randint(3, width // 2)
            x_end = random.randint(width // 2, width - 4)
            for x in range(x_start, x_end):
                if 0 <= y < height and 0 <= x < width:
                    if random.random() < 0.7:
                        tiles[y][x] = TILE_FLOOR

    else:  # random
        # Полностью случайная карта
        for y in range(2, height - 2):
            for x in range(2, width - 2):
                if random.random() < 0.15:
                    tiles[y][x] = random.choice([TILE_WALL, TILE_FLOOR, TILE_HOOKABLE])

        # Гарантируем путь по дну
        for x in range(2, width - 2):
            tiles[height - 2][x] = TILE_FLOOR

        # Добавляем лаву
        num_lava = random.randint(2, 5)
        for _ in range(num_lava):
            y = random.randint(3, height - 3)
            x = random.randint(2, width - 3)
            if random.random() < 0.5:
                tiles[y][x] = TILE_LAVA
                tiles[y][x + 1] = TILE_LAVA

    # ВСЕГДА добавляем лаву в разных местах
    lava_patterns = [
        (height - 3, width // 4, width // 4 + 3),
        (height - 6, width // 2, width // 2 + 2),
        (height - 9, width // 4 * 3, width // 4 * 3 + 2),
    ]
    for y, x_start, x_end in lava_patterns:
        if random.random() < 0.6:
            for x in range(x_start, x_end):
                if 0 <= y < height and 0 <= x < width:
                    tiles[y][x] = TILE_LAVA

    # Хукабельные стены в случайных местах
    num_hookable = random.randint(3, 8)
    for _ in range(num_hookable):
        y = random.randint(3, height - 4)
        x = random.randint(2, width - 3)
        if tiles[y][x] == TILE_AIR:
            tiles[y][x] = TILE_HOOKABLE
            if random.random() < 0.5 and x + 1 < width:
                tiles[y][x + 1] = TILE_HOOKABLE

    # Спавн и финиш (всегда на полу)
    spawn = (3, height - 2)
    finish = (width - 3, height - 2)

    tiles[spawn[1]][spawn[0]] = TILE_START
    tiles[finish[1]][finish[0]] = TILE_FINISH

    # УНИКАЛЬНОЕ НАЗВАНИЕ с типом карты
    map_name = f"{map_type.upper()}_{width}x{height}"

    return tiles, width, height, spawn, finish, map_name


class GameMap:
    def __init__(self, tiles, width, height, spawn, finish, name):
        self.tiles = tiles
        self.width = width
        self.height = height
        self.spawn = spawn
        self.finish = finish
        self.name = name


class GameServer:
    def __init__(self):
        print("=" * 60)
        print("🚀 Starting DDNet Server with DOUBLE JUMP!")
        print("=" * 60)

        self.players = {}
        self.finished_players = []
        self.clients = {}
        self.player_counter = 0
        self.running = True
        self.chat = ChatSystem()
        self.map_number = 0

        # Генерируем первую карту
        self.current_map = None
        self.generate_new_map()
        self.physics = PhysicsEngine(self.current_map)

    def generate_new_map(self):
        """Генерация новой случайной карты"""
        self.map_number += 1

        print("\n" + "=" * 60)
        print(f"🔄 Generating NEW map #{self.map_number}...")
        print("=" * 60)

        tiles, width, height, spawn, finish, name = create_random_map()

        self.current_map = GameMap(tiles, width, height, spawn, finish, name)
        self.physics = PhysicsEngine(self.current_map)

        # Сбрасываем финишировавших
        self.finished_players = []

        # Обновляем спавн для всех игроков
        for player in self.players.values():
            if self.current_map.spawn:
                player.spawn_x = self.current_map.spawn[0] * TILE_SIZE + TILE_SIZE // 2
                player.spawn_y = self.current_map.spawn[1] * TILE_SIZE + TILE_SIZE // 2
                player.respawn()
                player.finished = False

        print(f"✅ Map #{self.map_number}: {name}")
        print(f"📐 Size: {width}x{height}")
        print(f"📍 Spawn: {spawn}")
        print(f"🏁 Finish: {finish}")
        print(f"👥 Players: {len(self.players)}")
        print(f"🎨 Type: {name.split('_')[0]}")
        print("=" * 60)

        # Отправляем новую карту всем игрокам
        self.broadcast_map_change()

    def broadcast_map_change(self):
        """Уведомление всех игроков о смене карты"""
        if not hasattr(self, 'clients') or not self.clients:
            return

        map_data = {
            'type': 'map_change',
            'map_name': self.current_map.name,
            'map_number': self.map_number,
            'width': self.current_map.width,
            'height': self.current_map.height,
            'spawn': self.current_map.spawn,
            'finish': self.current_map.finish,
            'tiles': self.current_map.tiles
        }

        print(f"📤 Sending new map to {len(self.clients)} clients...")

        disconnected = []
        for conn in list(self.clients.keys()):
            try:
                send_data(conn, map_data)
            except Exception as e:
                print(f"   ❌ Failed to send: {e}")
                disconnected.append(conn)

        for conn in disconnected:
            if conn in self.clients:
                del self.clients[conn]

    def handle_client(self, conn, addr):
        try:
            player_id = f"Player_{self.player_counter}"
            self.player_counter += 1

            print(f"👤 New player: {player_id} from {addr}")

            if self.current_map and self.current_map.spawn:
                spawn_x, spawn_y = self.current_map.spawn
            else:
                spawn_x, spawn_y = 5, 5

            player = Player(player_id, spawn_x, spawn_y, player_id)
            self.players[player_id] = player
            self.clients[conn] = addr

            print(f"📍 Player spawn at: ({player.x}, {player.y})")
            print(f"👥 Total players: {len(self.players)}")

            welcome_data = {
                'type': 'welcome',
                'player_id': player_id,
                'spawn_x': player.x,
                'spawn_y': player.y,
                'map_name': self.current_map.name if self.current_map else "Unknown",
                'map_number': self.map_number,
                'map_size': (self.current_map.width, self.current_map.height) if self.current_map else (0, 0),
                'tiles': self.current_map.tiles if self.current_map else []
            }
            send_data(conn, welcome_data)

            last_state_send = time.time()

            while self.running and conn in self.clients:
                try:
                    data = recv_data(conn)
                    if data:
                        msg_type = data.get('type', '')

                        if msg_type == 'input':
                            keys = data.get('keys', {})
                            self.physics.update_player(player, keys)

                            if player.finished and player_id not in self.finished_players:
                                self.finished_players.append(player_id)
                                self.chat.add_message("System", f"🎉 {player_id} finished the race!")

                                if len(self.finished_players) >= len(self.players) and len(self.players) > 0:
                                    self.chat.add_message("System", "🏁 All players finished! Generating new map...")
                                    self.generate_new_map()

                        elif msg_type == 'chat':
                            message = data.get('message', '')
                            if message:
                                if message.startswith('/'):
                                    self.handle_command(player_id, message)
                                else:
                                    self.chat.add_message(player.name, message)
                                    self.broadcast_chat(player.name, message)

                        elif msg_type == 'skip_map':
                            # КЛАВИША O - пропуск карты
                            self.chat.add_message("System", f"⏭️ {player_id} skipped the map!")
                            self.generate_new_map()

                        elif msg_type == 'get_state':
                            self.send_game_state(conn, player_id)

                    current_time = time.time()
                    if current_time - last_state_send > 0.05:
                        self.send_game_state(conn, player_id)
                        last_state_send = current_time

                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"⚠️ Error: {e}")
                    break

        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            if player_id in self.players:
                self.chat.add_message("System", f"{player_id} left the game")
                del self.players[player_id]
                print(f"👋 Player disconnected: {player_id}")
                print(f"👥 Total players: {len(self.players)}")

            if conn in self.clients:
                del self.clients[conn]
            try:
                conn.close()
            except:
                pass

    def handle_command(self, player_id, command):
        if command == '/newmap' or command == '/next':
            self.chat.add_message("System", f"🔄 {player_id} requested new map!")
            self.generate_new_map()
        elif command == '/help':
            self.chat.add_message("System", "Commands: /newmap - change map, /help - this message")
            self.chat.add_message("System", "🦘 Double Jump: Press SPACE twice in the air!")
            self.chat.add_message("System", "🎨 Map Types: PLATFORMS, MAZE, TOWERS, RANDOM")
            self.chat.add_message("System", "⌨️  Press O key to skip current map!")
        else:
            self.chat.add_message("System", f"Unknown command: {command}. Type /help for commands")

    def send_game_state(self, conn, player_id=None):
        try:
            state = {
                'type': 'state',
                'players': {},
                'finished': self.finished_players,
                'mode': "RACE",
                'chat': self.chat.get_messages(5),
                'map_name': self.current_map.name if self.current_map else "Unknown",
                'map_number': self.map_number,
                'timestamp': time.time()
            }

            for pid, player in self.players.items():
                state['players'][pid] = {
                    'x': player.x,
                    'y': player.y,
                    'vx': player.vx,
                    'vy': player.vy,
                    'name': player.name,
                    'on_ground': player.on_ground,
                    'finished': player.finished,
                    'alive': player.alive
                }

            send_data(conn, state)
        except Exception as e:
            pass

    def broadcast_chat(self, sender, message):
        for conn in list(self.clients.keys()):
            try:
                chat_data = {
                    'type': 'chat_message',
                    'sender': sender,
                    'message': message
                }
                send_data(conn, chat_data)
            except:
                pass

    def run(self):
        try:
            server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_sock.bind((SERVER_HOST, SERVER_PORT))
            server_sock.listen(MAX_PLAYERS)
            server_sock.settimeout(1.0)

            print("=" * 60)
            print(f"✅ Server running on {SERVER_HOST}:{SERVER_PORT}")
            if self.current_map:
                print(f"📍 Current map: {self.current_map.name}")
            print("=" * 60)
            print("🦘 DOUBLE JUMP ENABLED! Press SPACE twice in the air!")
            print("🎨 4 MAP TYPES: PLATFORMS, MAZE, TOWERS, RANDOM")
            print("⏳ Waiting for players...")
            print("💬 Commands: /newmap - change map, /help - help")
            print("⌨️  Press O key to skip current map!")
            print("🔄 Map changes when all players finish!")
            print("Press Ctrl+C to stop")
            print("=" * 60)

            while self.running:
                try:
                    conn, addr = server_sock.accept()
                    print(f"📡 New connection from {addr}")

                    thread = threading.Thread(target=self.handle_client, args=(conn, addr))
                    thread.daemon = True
                    thread.start()

                except socket.timeout:
                    continue

                except Exception as e:
                    if self.running:
                        print(f"⚠️ Error: {e}")

        except KeyboardInterrupt:
            print("\n🛑 Server stopped")
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            self.running = False
            try:
                server_sock.close()
            except:
                pass

        print("👋 Server closed")


if __name__ == '__main__':
    try:
        server = GameServer()
        server.run()
    except KeyboardInterrupt:
        print("\n🛑 Stopped")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback

        traceback.print_exc()