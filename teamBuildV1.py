# -*- coding: utf-8 -*-
"""
Created on Fri Mar  5 16:31:14 2021

@author: vuxain
"""


import asyncio

import aiohttp

#import numpy as np

from prettytable import PrettyTable

from fpl import FPL

import queue

import copy


async def main():
    async with aiohttp.ClientSession() as session:
        fpl = FPL(session)
        
        class Node:
        
            def __init__(self, level, weight, value,  parent, inserted ,position, positionState):
                self.level = level
                self.weight = weight
                self.value = value
                self.bound = 0.0
                self.inserted = inserted
                self.parent = parent
                self.position = position
                self.positionState = positionState
            
            
        def bound(u, knapsackWeight, items):

            if (u.weight >= knapsackWeight):
                return 0
            totalValue = u.value
            l = u.level + 1
            totalWeight = u.weight

            tempList =  copy.deepcopy(u.positionState)


            while l < len(items)  and tempList != [0,0,0,0,0] :

                if  tempList[items[l].element_type] <=0:
                    l+=1
                    continue
                elif totalWeight + items[l].now_cost/10 <= knapsackWeight:

                    totalWeight += items[l].now_cost/10
                    totalValue += items[l].total_points
                    decrementList(tempList,items[l].element_type)
                    l += 1
                else:
                    break
            # if l < len(items):
            #     totalValue += (knapsackWeight - totalWeight) / items[l].now_cost * items[l].total_points
            return totalValue
        
        def decrementList (l,index):
            
            l[index] -= 1
         
            return l

        def positionStateCheck ( array):
            for x in array:
                if x<0:
                    return 0
            return 1
        
        
        def bnb(knapsackWeight, items):

            Q = queue.Queue()

            u = Node(-1, 0, 0, None, 0, None, [0,2,5,5,3])
            Q.put(u)
            maxValue = 0
            finalNode = None
           
            while not Q.empty():
                # u je trenutni cvor koji se razmatra
                u = Q.get()
                
                if (u.level == len(items) - 1): 
                    continue



                uCopyPositionState =  copy.deepcopy(u.positionState) 
                vPotentinalState = decrementList(uCopyPositionState, items[u.level + 1].element_type)


                # If there is space for the player the position or in the team overall
                if vPotentinalState[items[u.level + 1].element_type] >=0 and positionStateCheck(vPotentinalState):

                    # Left node - Player inserted

                    v = Node(u.level + 1, u.weight + items[u.level + 1].now_cost / 10,
                             u.value + items[u.level + 1].total_points, u, 1, items[u.level + 1].element_type,
                             vPotentinalState)

                    if v.weight <= knapsackWeight and v.value > maxValue:
                            maxValue = v.value
                            finalNode = v


                    v.bound = bound(v, knapsackWeight, items)
                    if (v.bound > maxValue)  :
                        Q.put(v)
                        #print(v.positionState)

                # Right node - Player not inserted

                v = Node(u.level + 1, u.weight, u.value, u, 0 , items[u.level + 1].element_type, u.positionState)
                v.bound = bound(v, knapsackWeight, items) 
                if (v.bound > maxValue):
                    Q.put(v)


            team = []
            while (finalNode != None):
                if(finalNode.inserted == 1):
                    team.append(items[finalNode.level])
                finalNode = finalNode.parent

            return [maxValue,team]
                
        
        
        
        knapsackWeight = 100.0
        
        players = await fpl.get_players()
                    
        playersSorted = sorted(players, key=lambda x: x.total_points , reverse=True)



        filteredParameters = [0,15,20,20,20]
        filteredPlayers = []
        for x in playersSorted:
            if filteredParameters == [0,0,0,0,0]:
                break
            if filteredParameters[x.element_type] > 0 :
                filteredPlayers.append(x)
                filteredParameters[x.element_type] -= 1

        # for x in filteredPlayers:
        #     print(x)
        # print(len(filteredPlayers))

        print('\n\n')

        #print (positionStateCheck([0,0,-1,0,0]))
        #print (decrementList([1,1,1,1],playersSorted[200].element_type))

        [value,team] = bnb(knapsackWeight, filteredPlayers)

        print ("Vrednost tima je", value)
        suma=0.0
        for x in team:
            print(x)
            suma+= x.now_cost/10
        print("Cena tima je", suma)

        


if __name__ == "__main__":
    asyncio.run(main())
    
  # decrementList( u.positionState,items[u.level + 1].element_type)  