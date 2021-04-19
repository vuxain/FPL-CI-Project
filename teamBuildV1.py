import queue
import copy
import sys

import asyncio

import aiohttp
from fpl import FPL


# Evaluation functions:


#                               ------- BRANCH AND BOUND -------

class Node:

    def __init__(self, level, weight, value, parent, inserted, position, positionState):
        self.level = level
        self.weight = weight
        self.value = value
        self.bound = 0.0
        self.inserted = inserted
        self.parent = parent
        self.position = position
        self.positionState = positionState


def decrementList(l, index):
    l[index] -= 1

    return l


def positionStateCheck(array):
    for x in array:
        if x < 0:
            return 0
    return 1


def bound(u, knapsackWeight, items):
    if u.weight >= knapsackWeight:
        return 0
    totalValue = u.value
    l = u.level + 1
    totalWeight = u.weight

    tempList = copy.deepcopy(u.positionState)

    while l < len(items) and tempList != [0, 0, 0, 0, 0]:

        if tempList[items[l].element_type] <= 0:
            l += 1
            continue
        elif totalWeight + items[l].now_cost / 10 <= knapsackWeight:
            totalWeight += items[l].now_cost / 10
            totalValue += items[u.level + 1].evaluation
            decrementList(tempList, items[l].element_type)
            l += 1
        else:
            break

    return totalValue


def bnb(knapsackWeight, items):
    Q = queue.Queue()

    u = Node(-1, 0, 0, None, 0, None, [0, 2, 5, 5, 3])
    Q.put(u)
    maxValue = 0
    finalNode = None

    while not Q.empty():
        u = Q.get()

        if u.level == len(items) - 1:
            continue

        uCopyPositionState = copy.deepcopy(u.positionState)
        vPotentialState = decrementList(uCopyPositionState, items[u.level + 1].element_type)

        # If there is space for the new players position
        if vPotentialState[items[u.level + 1].element_type] >= 0:
            # Left node - Player inserted
            v = Node(u.level + 1, u.weight + items[u.level + 1].now_cost / 10,
                     u.value + items[u.level + 1].evaluation, u, 1, items[u.level + 1].element_type,
                     vPotentialState)

            if v.weight <= knapsackWeight and v.value > maxValue:
                maxValue = v.value
                finalNode = v

            v.bound = bound(v, knapsackWeight, items)
            if v.bound > maxValue:
                Q.put(v)

        # If the team is full, there is no need for a deeper search
        if u.positionState != [0, 0, 0, 0, 0]:
            # Right node - Player not inserted
            v = Node(u.level + 1, u.weight, u.value, u, 0, items[u.level + 1].element_type, u.positionState)
            v.bound = bound(v, knapsackWeight, items)
            if v.bound > maxValue:
                Q.put(v)

    team = []
    while finalNode is not None:
        if finalNode.inserted == 1:
            team.append(items[finalNode.level])
        finalNode = finalNode.parent

    return [maxValue, team]


def positionName(posId):
    if posId == 1:
        return 'goalkeeper'
    elif posId == 2:
        return 'defender'
    elif posId == 3:
        return 'midfielder'
    else:
        return 'forward'


def playersEvaluation(players, teams, fixtures, fdr):
    fixturesByTeam = [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []]
    for fix in fixtures:
        fixturesByTeam[fix.team_h - 1].append(fix)
        fixturesByTeam[fix.team_a - 1].append(fix)

    for player in players:
        playerEvaluation = 0
        team = player.team - 1
        for game in fixturesByTeam[team]:
            teamFacingId, HomeAwayId = (game.team_h, 'A') if game.team_h != player.team else (game.team_a, 'H')
            teamFacing = teams[teamFacingId - 1]
            playerEvaluation += fdr[teamFacing.name][positionName(player.element_type)][HomeAwayId]
        player.evaluation = playerEvaluation


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
                await asyncio.sleep(1)

        print("Calc", )
        teams = await fpl.get_teams()
        fixtures = list(filter(lambda fix: fix.finished is False, await fpl.get_fixtures()))
        players = await fpl.get_players()
        # Filtering out the players that are unavailable or injured
        players = list(filter(lambda player: player.status != 'i' and player.status != 'u', players))

        # FDR
        playersEvaluation(players, teams, fixtures, fdr)

        playersSorted = sorted(players, key=lambda player: player.total_points/(player.now_cost/10), reverse=True)
        # [print(player, player.evaluation) for player in playersSorted]

        # ToDo: CHECK: key=lambda x: x.total_points/(x.now_cost/10))
        # ToDo : Create a new player evaluation function:
        # Ratings based on: Total points, Upcoming FDR, Form , Minutes, Team placement, gw transfer in?
        # ToDo : Create formation and number of playing subs choices

        # BNB call
        knapsackWeight = 100.0
        [value, team] = bnb(knapsackWeight, playersSorted)

        # Printing team and values
        price = sum([x.now_cost / 10 for x in team])
        team = sorted(team, key=lambda x: x.element_type)

        [print(x, x.status, x.element_type, x.now_cost / 10) for x in team]
        print("\nTeam price:", price)
        print("Team value:", value)


if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
