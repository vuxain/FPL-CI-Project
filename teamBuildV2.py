import random

import aiohttp
import asyncio
from fpl import FPL


class Individual:

    def __init__(self, gks, dfs, mfs, fws):
        # [gk, gk, df, df, df, df, df, mf, mf, mf, mf, mf, fw, fw, fw]
        self.code = []
        self.gks = gks.copy()
        self.dfs = dfs.copy()
        self.mfs = mfs.copy()
        self.fws = fws.copy()
        for i in range(2):
            index = random.randint(0, len(self.gks) - 1)
            self.code.append(self.gks[index])
            self.gks.pop(index)
        for i in range(5):
            index = random.randint(0, len(self.dfs) - 1)
            self.code.append(self.dfs[index])
            self.dfs.pop(index)
        for i in range(5):
            index = random.randint(0, len(self.mfs) - 1)
            self.code.append(self.mfs[index])
            self.mfs.pop(index)
        for i in range(3):
            index = random.randint(0, len(self.fws) - 1)
            self.code.append(self.fws[index])
            self.fws.pop(index)

        # self.correctNonFeasible()
        self.fitness = self.fitnessFunction()

    def fitnessFunction(self):
        value = 0.0
        for i in self.code:
            value += i.value

        return value

    def __lt__(self, other):
        return self.fitness > other.fitness

    # def correctNonFeasible(self):


def selection(population):
    min = float('inf')
    k = -1
    for i in range(6):
        j = random.randrange(100)
        if population[j].fitness < min:
            min = population[j].fitness
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


def init(players=None):
    if players is None:
        raise SystemExit('Error: Players')

    gks = []
    dfs = []
    mfs = []
    fws = []

    for p in players:
        if p.total_points == 0:
            continue
        if p.element_type == 1:
            gks.append(p)
        elif p.element_type == 2:
            dfs.append(p)
        elif p.element_type == 3:
            mfs.append(p)
        elif p.element_type == 4:
            fws.append(p)

        p.value = p.total_points / (p.now_cost / 10)

    return gks, dfs, mfs, fws


async def main():
    async with aiohttp.ClientSession() as session:
        fpl = FPL(session)
    players = await fpl.get_players()
    gks, dfs, mfs, fws = init(players)

    population = []
    newPopulation = []
    for i in range(100):
        population.append(Individual(gks, dfs, mfs, fws))
        newPopulation.append(Individual(gks, dfs, mfs, fws))

    for iteration in range(500):
        population.sort()
        for i in range(30):
            newPopulation[i] = population[i]
        for i in range(30, 100, 2):
            k1 = selection(population)
            k2 = selection(population)
            crossover(population[k1], population[k2], newPopulation[i], newPopulation[i + 1])
            mutation(newPopulation[i])
            mutation(newPopulation[i + 1])
            newPopulation[i].fitness = newPopulation[i].fitnessFunction()
            newPopulation[i + 1].fitness = newPopulation[i + 1].fitnessFunction()
        population = newPopulation

    population.sort()
    print('Solution:', population[0].fitness)
    print('Price:', sum(x.now_cost for x in population[0].code) / 10, "M")



if __name__ == "__main__":
    asyncio.run(main())
