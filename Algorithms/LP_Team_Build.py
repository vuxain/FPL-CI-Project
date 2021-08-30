import sys
import time

import pulp
import asyncio
import aiohttp
from fpl import FPL

#                               ------- Evaluation parameters -------

# Identifies players position
def positionName(posId):
    if posId == 1:
        return 'goalkeeper'
    elif posId == 2:
        return 'defender'
    elif posId == 3:
        return 'midfielder'
    else:
        return 'forward'

# Used to calculate FPL's FDR (Wait for the FPL API to update before using)
def fixtureAnalyzer(players, teams, fixtures, fdr):
    fixturesByTeam = [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []]
    for fix in fixtures:
        fixturesByTeam[fix.team_h - 1].append(fix)
        fixturesByTeam[fix.team_a - 1].append(fix)

    for player in players:
        playerEvaluation = 0
        FDRSum = 0
        team = player.team - 1
        for game in fixturesByTeam[team]:
            teamFacingId, HomeAwayId = (game.team_h, 'A') if game.team_h != player.team else (game.team_a, 'H')
            teamFacing = teams[teamFacingId - 1]
            playerEvaluation += fdr[teamFacing.name][positionName(player.element_type)][HomeAwayId]
            FDRSum += teamFacing.strength
        player.average_points_conceded = playerEvaluation / len(fixturesByTeam[team])
        player.fdr = FDRSum / len(fixturesByTeam[team])


def normalization(players):
    evMin = float('inf')
    evMax = float('-inf')
    tpMin = float('inf')
    tpMax = float('-inf')
    formMin = float('inf')
    formMax = float('-inf')

    for player in players:
        evMin = evMin if evMin < float(player.selected_by_percent) else float(player.selected_by_percent)
        evMax = evMax if evMax > float(player.selected_by_percent) else float(player.selected_by_percent)
        tpMin = tpMin if tpMin < player.total_points else player.total_points
        tpMax = tpMax if tpMax > player.total_points else player.total_points
        formMin = formMin if formMin < float(player.form) else float(player.form)
        formMax = formMax if formMax > float(player.form) else float(player.form)

    for player in players:
        player.selected_by_percent = (float(player.selected_by_percent) - evMin) / (evMax - evMin)
        player.total_points = (player.total_points - tpMin) / (tpMax - tpMin)
        player.form = (float(player.form) - formMin) / (formMax - formMin)


def evaluation(players):
    for player in players:
        player.evaluation = 0.6*player.total_points + 0.3*player.form + 0.2*player.selected_by_percent
        player.evaluation = round(player.evaluation, 2)


#                               ------- LINEAR PROGRAMMING -------

def linearMethod(players):

    nPlayers = len(players)

    model = pulp.LpProblem("TeamValueMaximisation", pulp.LpMaximize)

    selectedPlayers = [
        pulp.LpVariable("x{}".format(i), lowBound=0, upBound=1, cat='Integer')
        for i in range(nPlayers)
    ]
    selectedTeams = [i + 1 for i in range(20)]

    model += sum(selectedPlayers[i] * players[i].evaluation
                 for i in range(nPlayers)), "Objective"

    model += sum(selectedPlayers[i] * players[i].now_cost / 10 for i in range(nPlayers)) <= 100.0
    model += sum(selectedPlayers) == 15

    model += sum(selectedPlayers[i] for i in range(nPlayers) if players[i].element_type == 1) == 2
    model += sum(selectedPlayers[i] for i in range(nPlayers) if players[i].element_type == 2) == 5
    model += sum(selectedPlayers[i] for i in range(nPlayers) if players[i].element_type == 3) == 5
    model += sum(selectedPlayers[i] for i in range(nPlayers) if players[i].element_type == 4) == 3

    for club_id in selectedTeams:
        model += sum(selectedPlayers[i] for i in range(nPlayers) if players[i].team == club_id) <= 3

    model.solve()

    finalTeam = []

    for i in range(len(selectedPlayers)):
        if selectedPlayers[i].value() == 1:
            finalTeam.append(players[i])

    return finalTeam


async def main():
    async with aiohttp.ClientSession() as session:

        fpl = FPL(session)

        # If we send too many requests to the server, it will respond with `error: 429 Too Many Requests`
        while True:
            try:
                fdr = await fpl.FDR()
                break
            except aiohttp.ClientResponseError:
                print("Waiting for server to respond...", file=sys.stderr)
                await asyncio.sleep(3)

        print("Process started")
        s_time_start = time.time()

        # FPL fetch
        teams = await fpl.get_teams()
        fixtures = list(filter(lambda fix: fix.finished is False, await fpl.get_fixtures()))
        players = await fpl.get_players()

        # Filtering out the players that are unavailable or injured
        players = list(filter(lambda player: player.status != 'i' and player.status != 'u', players))

        # Evaluation function calls

        # fixtureAnalyzer(players, teams, fixtures, fdr)
        normalization(players)
        evaluation(players)
        playersSorted = sorted(players, key=lambda player: player.evaluation, reverse=True)

        # LP call
        team = linearMethod(players)

        # Printing team and values
        team = sorted(team, key=lambda x: x.element_type)
        [print(x, x.now_cost / 10, "£") for x in team]

        price = sum([x.now_cost / 10 for x in team])
        print("\nTeam price:", round(price, 2),"£")
        value = sum([x.evaluation for x in team])
        print("Team value:", value)
        s_time_stop = time.time()
        print("Finished in:", round((s_time_stop - s_time_start), 1), "s")

if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
