import copy
import sys
import time

import asyncio
import aiohttp
from fpl import FPL


#                               ------- Evaluation parameters -------

def positionName(posId):
    if posId == 1:
        return 'goalkeeper'
    elif posId == 2:
        return 'defender'
    elif posId == 3:
        return 'midfielder'
    else:
        return 'forward'


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
    # evMin = float('inf')
    # evMax = float('-inf')
    tpMin = float('inf')
    tpMax = float('-inf')
    # formMin = float('inf')
    # formMax = float('-inf')

    for player in players:
        # evMin = evMin if evMin < player.average_points_conceded else player.average_points_conceded
        # evMax = evMax if evMax > player.average_points_conceded else player.average_points_conceded
        tpMin = tpMin if tpMin < player.total_points else player.total_points
        tpMax = tpMax if tpMax > player.total_points else player.total_points
        # formMin = formMin if formMin < float(player.form) else float(player.form)
        # formMax = formMax if formMax > float(player.form) else float(player.form)

    for player in players:
        # player.average_points_conceded = 1 - ((player.average_points_conceded - evMin) / (evMax - evMin))
        player.total_points = (player.total_points - tpMin) / (tpMax - tpMin)
        #player.form = (float(player.form) - formMin) / (formMax - formMin)


def evaluation(players):
    for player in players:
        player.evaluation = player.total_points  # +  0.3*player.average_points_conceded + 0.1*player.form
        player.evaluation = round(player.evaluation, 2)



#                               ------- BRANCH AND BOUND -------

class Node:

    def __init__(self, level, weight, value, parent, inserted, position, positionState, teamsState):
        self.level = level
        self.weight = weight
        self.value = value
        self.bound = 0.0
        self.inserted = inserted
        self.parent = parent
        self.position = position
        self.positionState = positionState
        self.teamsState = teamsState


def decrementList(l, index):
    l[index] -= 1
    return l


def positionStateCheck(array):
    for x in array:
        if x < 0:
            return False
    return True


def bound(u, knapsackWeight, items):
    if u.weight >= knapsackWeight:
        return 0
    totalValue = u.value
    l = u.level + 1
    totalWeight = u.weight

    tempList1 = copy.deepcopy(u.positionState)
    tempList2 = copy.deepcopy(u.teamsState)

    while l < len(items) and tempList1 != [0, 0, 0, 0, 0]:

        # if tempList1[items[l].element_type] <= 0 or tempList2[items[l].team] <= 0 :
        #     l += 1
        if totalWeight + items[l].now_cost / 10 <= knapsackWeight and tempList1[items[l].element_type] > 0 and \
                tempList2[items[l].team] > 0:
            totalWeight += items[l].now_cost / 10
            totalValue += items[l].evaluation
            decrementList(tempList1, items[l].element_type)
            decrementList(tempList2, items[l].team)

        l += 1

    return totalValue


def bnb(knapsackWeight, items):
    Q = []
    u = Node(-1, 0, 0, None, 0, None, [0, 2, 5, 5, 3], [3 for x in range(21)])
    Q.append(u)
    maxValue = 0
    finalNode = None

    while Q:
        u = Q.pop()

        if u.level == len(items) - 1:
            continue

        uCopyPositionState = copy.deepcopy(u.positionState)
        uCopyPosition = copy.deepcopy(u.positionState)
        uCopyTeam = copy.deepcopy(u.teamsState)
        vPotentialState = decrementList(uCopyPositionState, items[u.level + 1].element_type)

        uCopyTeamsState = copy.deepcopy(u.teamsState)
        vPotentialTeamsState = decrementList(uCopyTeamsState, items[u.level + 1].team)

        # If there is space for the new players position
        if vPotentialState[items[u.level + 1].element_type] >= 0 and vPotentialTeamsState[items[u.level + 1].team] >= 0:
            # Left node - Player inserted
            v = Node(u.level + 1, u.weight + items[u.level + 1].now_cost / 10,
                     u.value + items[u.level + 1].evaluation, u, 1, items[u.level + 1].element_type,
                     vPotentialState, vPotentialTeamsState)

            if v.weight <= knapsackWeight and v.value > maxValue and v.positionState == [0, 0, 0, 0,
                                                                                         0] and positionStateCheck(
                    v.teamsState):
                maxValue = v.value
                finalNode = v

            v.bound = bound(v, knapsackWeight, items)
            if v.bound > maxValue:
                Q.append(v)

        # If the team is full, there is no need for a deeper search
        if u.positionState != [0, 0, 0, 0, 0]:
            # Right node - Player not inserted
            v = Node(u.level + 1, u.weight, u.value, u, 0, items[u.level + 1].element_type, uCopyPosition, uCopyTeam)
            v.bound = bound(v, knapsackWeight, items)
            if v.bound > maxValue:
                Q.append(v)

    team = []
    while finalNode is not None:
        if finalNode.inserted == 1:
            team.append(items[finalNode.level])
        finalNode = finalNode.parent

    return [maxValue, team]



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

        print("Process started", )

        sTimeStart = time.time()

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

        # Filtering out a certain amount of players for bnb testing
        filteredParameters1 = [0, 5, 10, 10, 5]
        filteredParameters2 = [3 for x in range(21)]
        filteredPlayers = []
        for x in playersSorted:
            if filteredParameters1 == [0, 0, 0, 0, 0]:
                break
            if filteredParameters1[x.element_type] > 0 and filteredParameters2[x.team] > 0:
                filteredPlayers.append(x)
                filteredParameters1[x.element_type] -= 1
                filteredParameters2[x.team] -= 1

        filteredPlayers = sorted(filteredPlayers, key=lambda player: (player.evaluation), reverse=True)

        # Printing players valuations
        #
        # [print(player, "Player value: " + str(player.evaluation)  , "| Average Points Conceded: " + str(player.average_points_conceded), "TP: " + str(player.total_points),
        #        "Form: " + str(player.form), "FDR: " + str(player.fdr)) for player in filteredPlayers]

        # BNB call

        knapsackWeight = 100.0
        [value, team] = bnb(knapsackWeight, filteredPlayers)
        sTimeEnd = time.time()
        print(sTimeEnd - sTimeStart, "s")

        # Printing team and values

        team = sorted(team, key=lambda x: x.element_type)
        [print(x, x.status, x.element_type, x.now_cost / 10) for x in team]

        price = sum([x.now_cost / 10 for x in team])
        print("\nTeam price:", price)
        print("Team value:", value)

        # ToDo: CHECK: key=lambda x: x.total_points/(x.now_cost/10))
        # ToDo : Create a new player evaluation function:
        # Ratings based on: Total points, Upcoming FDR, Form , Minutes, Team placement, gw transfers in?
        # ToDo : Create formation and number of playing subs choices


if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
