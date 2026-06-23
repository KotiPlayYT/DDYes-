# game_modes.py
from enum import Enum


class GameMode(Enum):
    RACE = 1
    TEAM_RACE = 2
    DEATHMATCH = 3


class GameModeManager:
    def __init__(self, mode=GameMode.RACE):
        self.mode = mode
        self.team_scores = {}
        self.player_teams = {}

    def set_mode(self, mode):
        self.mode = mode

    def get_mode_name(self):
        return self.mode.name.replace('_', ' ').title()

    def assign_team(self, player_id):
        if self.mode == GameMode.TEAM_RACE:
            if player_id not in self.player_teams:
                # Простое распределение по четности
                team = 'red' if len(self.player_teams) % 2 == 0 else 'blue'
                self.player_teams[player_id] = team
            return self.player_teams[player_id]
        return None

    def check_win_condition(self, player, finished_players):
        if self.mode == GameMode.RACE:
            return len(finished_players) == 1 and player in finished_players

        elif self.mode == GameMode.TEAM_RACE:
            # Проверяем, все ли игроки команды финишировали
            if player.id in self.player_teams:
                team = self.player_teams[player.id]
                team_players = [p for p, t in self.player_teams.items() if t == team]
                all_finished = all(p in finished_players for p in team_players)
                return all_finished

        return False