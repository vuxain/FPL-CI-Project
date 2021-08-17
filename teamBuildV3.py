import random
import sys
import time
from collections import Counter
import copy

import aiohttp
import asyncio
from fpl import FPL

NUMBER_OF_ITERATIONS = 10000


class Solution:
    def __init__(self, gks, dfs, mfs, fws):
        # [gk, gk, df, df, df, df, df, mf, mf, mf, mf, mf, fw, fw, fw]
        self.solution = []
        self.value = 0

        self.players = [[], gks.copy(), dfs.copy(), mfs.copy(), fws.copy()]
        self.number_of_players = [0, len(gks), len(dfs), len(mfs), len(fws)]
        self.positions = [0, 2, 5, 5, 3]
        self.same_team = [3 for _ in range(21)]

        i = 1
        for working_position in self.positions[1:]:
            while working_position:
                index = random.randint(0, self.number_of_players[i] - 1)
                if self.same_team[self.players[i][index].team] == 0:
                    continue
                self.solution.append(self.players[i][index])
                self.positions[i] -= 1
                self.same_team[self.players[i][index].team] -= 1
                working_position -= 1
            i += 1

        self.correct_non_feasible()
        self.value_function()

    def value_function(self):
        fit = 0.0
        for i in self.solution:
            fit += i.evaluation

        self.value = fit

    def __lt__(self, other):
        return self.value > other.value

    def update_teams(self):
        self.same_team = [3 for _ in range(21)]
        for player in self.solution:
            self.same_team[player.team] -= 1

    def return_random_player_by_position(self, position):
        while True:
            index = random.randint(0, self.number_of_players[position] - 1)
            if self.same_team[self.players[position][index].team] == 0:
                continue
            else:
                return self.players[position][index]

    def remove_player_and_add_new_player(self, kick_player, new_player):
        if kick_player.id == new_player.id:
            return False

        self.same_team[kick_player.team] += 1
        self.solution.remove(kick_player)
        self.solution.append(new_player)
        self.same_team[new_player.team] -= 1
        self.solution = sorted(self.solution, key=lambda x: x.element_type)

        return True

    def correct_non_feasible(self):
        self.update_teams()

        all_conditions = [False, False, False]
        while any(x is False for x in all_conditions):
            result = [i for key in (key for key, count in Counter(self.solution).items() if count > 1) for i, x in
                      enumerate(self.solution) if x == key]
            # Checks duplicated players
            if len(result) == 0:
                all_conditions[0] = True
            else:
                all_conditions[0] = False
                duplicated_player = self.solution[result[0]]
                new_player = self.return_random_player_by_position(duplicated_player.element_type)
                if not self.remove_player_and_add_new_player(duplicated_player, new_player):
                    continue

            all_conditions[1] = True
            # Checks team constraint
            while any(x < 0 for x in self.same_team):
                all_conditions[1] = False
                team_index = next(x for x, val in enumerate(self.same_team) if val < 0)
                same_team_players = [x for x in self.solution if x.team == team_index]
                worst_value_payer = float('+inf')
                worst_player_index = -1
                # FIX: kick player based on the evaluation #newSeason
                for i in range(len(same_team_players)):
                    if same_team_players[i].evaluation / (same_team_players[i].now_cost / 10) < worst_value_payer:
                        worst_player_index = i
                kick_player = same_team_players[worst_player_index]
                new_player = self.return_random_player_by_position(kick_player.element_type)
                if not self.remove_player_and_add_new_player(kick_player, new_player):
                    continue

            all_conditions[2] = True
            # Checks price
            while sum([x.now_cost / 10 for x in self.solution]) > 100.00:
                all_conditions[2] = False
                index = random.randint(0, len(self.solution) - 1)
                kick_player = self.solution[index]
                new_player = self.return_random_player_by_position(kick_player.element_type)
                if not self.remove_player_and_add_new_player(kick_player, new_player):
                    continue

    def invert(self):
        index = random.randint(0, len(self.solution) - 1)
        kick_player = self.solution[index]
        new_player = self.return_random_player_by_position(kick_player.element_type)
        if not self.remove_player_and_add_new_player(kick_player, new_player):
            return False
        self.correct_non_feasible()
        self.value_function()
        return True

    def print_team(self):
        [print(x, x.status, x.evaluation, str(x.now_cost / 10) + 'M') for x in self.solution]
        print()


def position_name(pos_id):
    if pos_id == 1:
        return 'goalkeeper'
    elif pos_id == 2:
        return 'defender'
    elif pos_id == 3:
        return 'midfielder'
    else:
        return 'forward'


def fixture_analyzer(players, teams, fixtures, fdr):
    fixtures_by_team = [[] for _ in range(len(teams))]
    for fix in fixtures:
        fixtures_by_team[fix.team_h - 1].append(fix)
        fixtures_by_team[fix.team_a - 1].append(fix)

    for player in players:
        player_evaluation = 0
        fdr_sum = 0
        team = player.team - 1
        for game in fixtures_by_team[team]:
            team_facing_id, home_away_id = (game.team_h, 'A') if game.team_h != player.team else (game.team_a, 'H')
            team_facing = teams[team_facing_id - 1]
            player_evaluation += fdr[team_facing.name][position_name(player.element_type)][home_away_id]
            fdr_sum += team_facing.strength
        player.average_points_conceded = player_evaluation / len(fixtures_by_team[team])
        player.fdr = fdr_sum / len(fixtures_by_team[team])


def normalization(players):
    ev_min = float('inf')
    ev_max = float('-inf')
    tp_min = float('inf')
    tp_max = float('-inf')
    form_min = float('inf')
    form_max = float('-inf')

    for player in players:
        # ev_min = ev_min if ev_min < player.average_points_conceded else player.average_points_conceded
        # ev_max = ev_max if ev_max > player.average_points_conceded else player.average_points_conceded
        tp_min = tp_min if tp_min < player.total_points else player.total_points
        tp_max = tp_max if tp_max > player.total_points else player.total_points
        # form_min = form_min if form_min < float(player.form) else float(player.form)
        # form_max = form_max if form_max > float(player.form) else float(player.form)

    for player in players:
        # player.average_points_conceded = 1 - ((player.average_points_conceded - ev_min) / (ev_max - ev_min))
        player.total_points = (player.total_points - tp_min) / (tp_max - tp_min)
        # player.form = (float(player.form) - form_min) / (form_max - form_min)


def evaluation(players):
    for player in players:
        # TODO: new season
        # player.evaluation = 0.4 * player.total_points + 0.4 * player.average_points_conceded + 0.2 * player.form
        player.evaluation = player.total_points
        player.evaluation = round(player.evaluation, 2)


def players_by_position(players=None):
    if players is None:
        raise SystemExit('Error: Players')

    gks = []
    dfs = []
    mfs = []
    fws = []

    for p in players:
        if p.element_type == 1:
            gks.append(p)
        elif p.element_type == 2:
            dfs.append(p)
        elif p.element_type == 3:
            mfs.append(p)
        elif p.element_type == 4:
            fws.append(p)

    return gks, dfs, mfs, fws


async def main():
    async with aiohttp.ClientSession() as session:
        fpl = FPL(session)

        # If we send too many requests to the server, it will respond with `error: 429 Too Many Requests`
        while True:
            try:
                # fdr = await fpl.FDR()
                break
            except aiohttp.ClientResponseError:
                print("Waiting for server to respond...", file=sys.stderr)
                await asyncio.sleep(3)

        # Collecting all necessary data
        # TODO: new season
        # fixtures = [fix for fix in await fpl.get_fixtures() if fix.finished is False]
        # teams = await fpl.get_teams()
        # Filtering out the players that are unavailable or injured
        players = [player for player in await fpl.get_players() if player.status != 'i' and player.status != 'u']

    print("Process started")
    s_time_start = time.time()

    # TODO: new season
    # fixtureAnalyzer(players, teams, fixtures, fdr)

    normalization(players)
    evaluation(players)
    gks, dfs, mfs, fws = players_by_position(players)

    solution = Solution(gks, dfs, mfs, fws)

    current_value = solution.value
    best_value = current_value
    best_solution = copy.copy(solution)

    for i in range(1, NUMBER_OF_ITERATIONS):
        revert_solution = copy.copy(solution)
        if not solution.invert():
            continue

        new_value = solution.value
        new_solution = copy.copy(solution)
        if new_value > current_value:
            current_value = new_value
            solution = copy.copy(new_solution)
        else:
            p = 1.0 / i ** 0.5
            q = random.uniform(0, 1)
            if p > q:
                current_value = new_value
                solution = copy.copy(new_solution)
            else:
                solution = copy.copy(revert_solution)
        if new_value > best_value:
            best_value = new_value
            best_solution = copy.copy(new_solution)

    solution.print_team()
    print('Price:', sum(x.now_cost / 10 for x in best_solution.solution), "M")
    print('Value:', best_solution.value)
    s_time_stop = time.time()
    print("Finished in:", (s_time_stop - s_time_start), "s")


if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
