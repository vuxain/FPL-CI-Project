import random
import sys
import time
from collections import Counter

import aiohttp
import asyncio
from fpl import FPL


class Individual:
    def __init__(self, gks, dfs, mfs, fws):
        # [gk, gk, df, df, df, df, df, mf, mf, mf, mf, mf, fw, fw, fw]
        self.code = []

        self.players = [[], gks.copy(), dfs.copy(), mfs.copy(), fws.copy()]
        self.numberOfPlayers = [0, len(gks), len(dfs), len(mfs), len(fws)]
        self.positions = [0, 2, 5, 5, 3]
        self.sameTeam = [3 for _ in range(21)]

        i = 1
        for workingPosition in self.positions[1:]:
            while workingPosition:
                index = random.randint(0, self.numberOfPlayers[i] - 1)
                if self.sameTeam[self.players[i][index].team] == 0:
                    continue
                self.code.append(self.players[i][index])
                self.positions[i] -= 1
                self.sameTeam[self.players[i][index].team] -= 1
                workingPosition -= 1
            i += 1

        self.correctNonFeasible()
        self.fitness = self.fitnessFunction()

    def fitnessFunction(self):
        evaluation = 0.0
        for i in self.code:
            evaluation += i.evaluation

        return evaluation

    def __lt__(self, other):
        return self.fitness > other.fitness

    def correctNonFeasible(self):
        self.UpdateTeams()

        # for i in range(1, 21):
        #     if self.sameTeam[i] > 3:
        #         break
        #

        while True:
            result = [i for key in (key for key, count in Counter(self.code).items() if count > 1) for i, x in
                      enumerate(self.code) if x == key]
            if len(result) == 0:
                break
            invalidPlayer = self.code[result[0]]
            self.sameTeam[invalidPlayer.team] += 1
            self.code.remove(invalidPlayer)
            newPlayer = self.returnRandomPlayerByPosition(invalidPlayer.element_type)
            self.code.append(newPlayer)
            self.sameTeam[newPlayer.team] -= 1
            self.code = sorted(self.code, key=lambda x: x.element_type)

    def returnRandomPlayerByPosition(self, position):
        while True:
            index = random.randint(0, self.numberOfPlayers[position] - 1)
            if self.sameTeam[self.players[position][index].team] == 0:
                continue
            else:
                return self.players[position][index]

    def printTeam(self):
        [print(x, x.status, x.element_type, x.now_cost / 10) for x in self.code]
        print()

    def UpdateTeams(self):
        self.sameTeam = [0 for _ in range(21)]
        for player in self.code:
            self.sameTeam[player.team] += 1


def selection(population):
    max = float('-inf')
    k = -1
    for i in range(3):
        j = random.randrange(100)
        if population[j].fitness > max:
            max = population[j].fitness
            k = j
    return k


def crossover(parent1, parent2, child1, child2):
    length = len(parent1.code)
    i = random.randrange(length)
    for j in range(i):
        child1.code[j] = parent1.code[j]
        child2.code[j] = parent2.code[j]
    for j in range(i, length):
        child1.code[j] = parent2.code[j]
        child2.code[j] = parent1.code[j]
    child1.correctNonFeasible()
    child2.correctNonFeasible()


def mutation(individual):
    length = len(individual.code)
    for i in range(length):
        if random.random() > 0.005:
            continue
        if 0 <= i <= 1:
            index = random.randint(0, len(individual.gks) - 1)
            tmp = individual.code[i]
            individual.code[i] = individual.gks[index]
            individual.gks.append(tmp)
            individual.gks.pop(index)
        if 2 <= i <= 6:
            index = random.randint(0, len(individual.dfs) - 1)
            tmp = individual.code[i]
            individual.code[i] = individual.dfs[index]
            individual.dfs.append(tmp)
            individual.dfs.pop(index)
        if 7 <= i <= 11:
            index = random.randint(0, len(individual.mfs) - 1)
            tmp = individual.code[i]
            individual.code[i] = individual.mfs[index]
            individual.mfs.append(tmp)
            individual.mfs.pop(index)
        if 12 <= i <= 14:
            index = random.randint(0, len(individual.fws) - 1)
            tmp = individual.code[i]
            individual.code[i] = individual.fws[index]
            individual.fws.append(tmp)
            individual.fws.pop(index)


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
    fixturesByTeam = [[] for _ in range(len(teams))]
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
        evMin = evMin if evMin < player.average_points_conceded else player.average_points_conceded
        evMax = evMax if evMax > player.average_points_conceded else player.average_points_conceded
        tpMin = tpMin if tpMin < player.total_points else player.total_points
        tpMax = tpMax if tpMax > player.total_points else player.total_points
        formMin = formMin if formMin < float(player.form) else float(player.form)
        formMax = formMax if formMax > float(player.form) else float(player.form)

    for player in players:
        player.average_points_conceded = 1 - ((player.average_points_conceded - evMin) / (evMax - evMin))
        player.total_points = (player.total_points - tpMin) / (tpMax - tpMin)
        player.form = (float(player.form) - formMin) / (formMax - formMin)


def evaluation(players):
    for player in players:
        player.evaluation = 0.4 * player.total_points + 0.4 * player.average_points_conceded + 0.2 * player.form
        player.evaluation = round(player.evaluation, 2)


def init(players=None):
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
                fdr = await fpl.FDR()
                break
            except aiohttp.ClientResponseError:
                print("Waiting for server to respond...", file=sys.stderr)
                await asyncio.sleep(3)

        # Collecting all necessary data
        fixtures = list(filter(lambda fix: fix.finished is False, await fpl.get_fixtures()))
        teams = await fpl.get_teams()
        # Filtering out the players that are unavailable or injured
        players = list(filter(lambda player: player.status != 'i' and player.status != 'u', await fpl.get_players()))

    print("Process started")
    sTimeStart = time.time()

    fixtureAnalyzer(players, teams, fixtures, fdr)
    normalization(players)
    evaluation(players)
    playersSorted = sorted(players, key=lambda player: player.evaluation, reverse=True)
    gks, dfs, mfs, fws = init(playersSorted)

    population = []
    newPopulation = []
    for i in range(100):
        population.append(Individual(gks, dfs, mfs, fws))
        newPopulation.append(Individual(gks, dfs, mfs, fws))

    for iteration in range(1000):
        population = sorted(population, key=lambda individual: individual.fitness, reverse=True)
        for i in range(19):
            newPopulation[i] = population[i]
        for i in range(20, 100, 2):
            k1 = selection(population)
            k2 = selection(population)
            crossover(population[k1], population[k2], newPopulation[i], newPopulation[i + 1])
            # mutation(newPopulation[i])
            # mutation(newPopulation[i + 1])
            newPopulation[i].fitness = newPopulation[i].fitnessFunction()
            newPopulation[i + 1].fitness = newPopulation[i + 1].fitnessFunction()
        population = newPopulation

    population = sorted(population, key=lambda individual: individual.fitness, reverse=True)

    population[0].printTeam()
    print('Value:', population[0].fitness)
    print('Price:', sum(x.now_cost / 10 for x in population[0].code), "M")


if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
