import queue
import copy

import asyncio
import aiohttp
from fpl import FPL


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
            totalValue += items[l].total_points
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
                     u.value + items[u.level + 1].total_points, u, 1, items[u.level + 1].element_type,
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


async def main():
    async with aiohttp.ClientSession() as session:
        fpl = FPL(session)

        players = await fpl.get_players()
        # Filtering out the players that are unavailable or injured
        playersSorted = sorted(filter(lambda player: player.status != 'i' and player.status != 'u', players),
                               key=lambda x: x.total_points, reverse=True)

        # filteredParameters = [0, 25, 40, 40, 40]
        # filteredPlayers = []
        # for x in playersSorted:
        #     if filteredParameters == [0, 0, 0, 0, 0]:
        #         break
        #     if filteredParameters[x.element_type] > 0:
        #         filteredPlayers.append(x)
        #         filteredParameters[x.element_type] -= 1

        knapsackWeight = 100.0
        [value, team] = bnb(knapsackWeight, playersSorted)

        print("Team value:", value)
        price = sum([x.now_cost / 10 for x in team])
        team = sorted(team, key=lambda x: x.element_type)

        [print(x, x.status, x.total_points, x.now_cost / 10) for x in team]
        print("Team price:", price)


if __name__ == "__main__":
    asyncio.run(main())
