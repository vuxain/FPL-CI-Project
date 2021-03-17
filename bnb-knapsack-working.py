# -*- coding: utf-8 -*-
"""
Created on Sat Mar 13 21:52:25 2021

@author: vuxain
"""

# -*- coding: utf-8 -*-
"""
Created on Fri Mar  5 16:31:14 2021

@author: vuxain
"""


import asyncio

import aiohttp

from prettytable import PrettyTable

from fpl import FPL

import queue


async def main():
    async with aiohttp.ClientSession() as session:
        fpl = FPL(session)
        
        class Node:
        
            def __init__(self, level, weight, value, inserted, parent):
                self.level = level
                self.weight = weight
                self.value = value
                self.bound = 0.0
                self.parent = parent
                self.inserted = inserted
            
            
        def bound(u, knapsackWeight, items):
        
            if (u.weight >= knapsackWeight):
                return 0
            totalValue = u.value 
            l = u.level + 1
            totalWeight = u.weight
            while l < len(items) and totalWeight + items[l].now_cost/10 <= knapsackWeight:
                totalWeight += items[l].now_cost/10
                totalValue += items[l].total_points
                l += 1
            # if l < len(items):
            #     totalValue += (knapsackWeight - totalWeight) / items[l].now_cost * items[l].total_points
            return totalValue
        
        
        
        def bnb(knapsackWeight, items):
            Q = queue.Queue()
            # pogodno je inicijalizovati cvorom na nivou -1
            u = Node(-1, 0, 0, 0, None)
            Q.put(u)
            maxValue = 0
            finalNode = None
            while not Q.empty():
                # u je trenutni cvor koji se razmatra
                u = Q.get()
                if (u.level == len(items) - 1): 
                    continue
                # v ovde predstavlja cvor za nivo nize pod pretpostavkom da je uzet cvor v
                v = Node(u.level + 1, u.weight + items[u.level + 1].now_cost/10, u.value + items[u.level + 1].total_points, 1, u)
                # provera da li se povecava maksimalna vrednost uzimajuci v u obzir 
                if v.weight <= knapsackWeight and v.value > maxValue:
                    maxValue = v.value
                    finalNode = v
                # v ce se uzeti u razmatranje ukoliko je najbolja vrednost veca od trenutne najbolje
                # u duhu BnB algoritma, ako nije veca, nema potrebe razmatrati cvor v
                v.bound = bound(v, knapsackWeight, items)
                if (v.bound > maxValue):
                    Q.put(v)
                # v ovde predstavlja cvor za nivo nize pod pretpostavkom da nije uzet cvor v
                v = Node(u.level + 1, u.weight, u.value, 0, u)
                v.bound = bound(v, knapsackWeight, items) 
                if (v.bound > maxValue):
                    Q.put(v)
            
            
            suma = 0.0
            while (finalNode.parent != None):
                if(finalNode.inserted == 1):
                    print (items[finalNode.level])
                    suma+=items[finalNode.level].now_cost/10
                finalNode = finalNode.parent
            print(suma)
            return maxValue
                
        
        
        
        knapsackWeight = 100.0
        
        players = await fpl.get_players()
                    
        playersSorted = sorted(players, key=lambda x: x.total_points/x.now_cost / 10 , reverse=True)
        
        # for x in playersSorted:
        #     print(x)
        
        print('Maksimalna vrednost:', bnb(knapsackWeight, playersSorted))

        


if __name__ == "__main__":
    asyncio.create_task(main())
    
    