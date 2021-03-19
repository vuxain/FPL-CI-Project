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

            
            while l < len(items)  or tempList != [0,0,0,0,0] :

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
        
        
        def bnb(knapsackWeight, items):
            Q = queue.Queue()
            # pogodno je inicijalizovati cvorom na nivou -1
            u = Node(-1, 0, 0, None, 0, None, [0,5,2,5,1])
            Q.put(u)
            maxValue = 0
            finalNode = None
           
            while not Q.empty():
                # u je trenutni cvor koji se razmatra
                u = Q.get()
                
                if (u.level == len(items) - 1): 
                    continue
                
                
                uCopyPositionState =  copy.deepcopy(u.positionState) 
                v = Node(u.level + 1, u.weight + items[u.level + 1].now_cost/10, u.value + items[u.level + 1].total_points, u, 1, items[u.level + 1].element_type,decrementList(uCopyPositionState,items[u.level + 1].element_type))
                

                if v.positionState[v.position] >=0:
                    if v.weight <= knapsackWeight and v.value > maxValue   :
                            maxValue = v.value
                            finalNode = v


                    v.bound = bound(v, knapsackWeight, items)
                    if (v.bound > maxValue)  :
                        Q.put(v)
                        #print(v.positionState)

            
            # if (v.positionState == [0,0,0,0,0]):
               
            #     print ('AAAAAAAAAAAAAA')
            #     break 
                

                v = Node(u.level + 1, u.weight, u.value, u, 0 , items[u.level + 1].element_type, u.positionState)
                v.bound = bound(v, knapsackWeight, items) 
                if (v.bound > maxValue):
                    Q.put(v)

            
                # print (items[v.level])
                #print(v.positionState)
            
            suma = 0.0
            
            while (finalNode.parent != None):
                if(finalNode.inserted == 1):
                    print (items[finalNode.level])
                    suma += items[finalNode.level].now_cost/10
                finalNode = finalNode.parent
            print(suma)            
        
    
            return maxValue
                
        
        
        
        knapsackWeight = 100.0
        
        players = await fpl.get_players()
                    
        playersSorted = sorted(players, key=lambda x: x.total_points/(x.now_cost / 10) , reverse=True)
        print(len(playersSorted))
        # for x in playersSorted[0:20]:
        #     print(x)
            
        print('\n\n')
        
        #print (decrementList([1,1,1,1],playersSorted[200].element_type))
        print('Maksimalna vrednost:', bnb(knapsackWeight, playersSorted))

        


if __name__ == "__main__":
    asyncio.run(main())
    
  # decrementList( u.positionState,items[u.level + 1].element_type)  