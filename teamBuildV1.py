# -*- coding: utf-8 -*-
"""
Created on Fri Mar  5 16:31:14 2021

@author: vuxain
"""


import asyncio

import aiohttp

import numpy as np

from prettytable import PrettyTable

from fpl import FPL

import queue


async def main():
    async with aiohttp.ClientSession() as session:
        fpl = FPL(session)
        
        class Node:
        
            def __init__(self, level, weight, value, inserted, parent, position, positionState):
                self.level = level
                self.weight = weight
                self.value = value
                self.bound = 0.0
                self.parent = parent
                self.inserted = inserted
                self.position = position
                self.positionState = positionState
            
            
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
        
        def decrementList (l,index):
            
            l[index] -= 1
         
            return l
        
        
        def bnb(knapsackWeight, items):
            Q = queue.Queue()
            # pogodno je inicijalizovati cvorom na nivou -1
            u = Node(-1, 0, 0, 0, None, None, [0,2,5,5,3])
            Q.put(u)
            maxValue = 0
            finalNode = None
           
            while not Q.empty():
                # u je trenutni cvor koji se razmatra
                u = Q.get()
                if (u.level == len(items) - 1): 
                    continue
                # v ovde predstavlja cvor za nivo nize pod pretpostavkom da je uzet cvor v
                v = Node(u.level + 1, u.weight + items[u.level + 1].now_cost/10, u.value + items[u.level + 1].total_points, 1, u, items[u.level + 1].element_type,decrementList( u.positionState,items[u.level + 1].element_type))
                # provera da li se povecava maksimalna vrednost uzimajuci v u obzir 
                
                if  v.positionState[v.position] >0:
                    if v.weight <= knapsackWeight and v.value > maxValue :
                            maxValue = v.value
                            finalNode = v
                        # v ce se uzeti u razmatranje ukoliko je najbolja vrednost veca od trenutne najbolje
                        # u duhu BnB algoritma, ako nije veca, nema potrebe razmatrati cvor v
                    v.bound = bound(v, knapsackWeight, items)
                    if (v.bound > maxValue):
                        Q.put(v)
                        
                    while (finalNode.parent != None):
                        if(finalNode.inserted == 1):
                            print (items[finalNode.level])
                        finalNode = finalNode.parent        
            
                    
                    print(v.positionState)
      
                # v ovde predstavlja cvor za nivo nize pod pretpostavkom da nije uzet cvor v
                v = Node(u.level + 1, u.weight, u.value, 0, u, items[u.level + 1].element_type, u.positionState)
                v.bound = bound(v, knapsackWeight, items) 
                if (v.bound > maxValue):
                    #print('pingvin')
                    Q.put(v)
            

            
            return maxValue
                
        
        
        
        knapsackWeight = 100.0
        
        players = await fpl.get_players()
                    
        playersSorted = sorted(players, key=lambda x: x.total_points/x.now_cost / 10 , reverse=True)
        
        # for x in playersSorted:
        #     print(x)
        
        
        
        print('Maksimalna vrednost:', bnb(knapsackWeight, playersSorted))

        


if __name__ == "__main__":
    asyncio.create_task(main())
    
    