# -*- coding: utf-8 -*-
"""
Created on Fri Mar  5 16:31:14 2021

@author: vuxain
"""


import asyncio

import aiohttp

from prettytable import PrettyTable

from fpl import FPL


async def main():
    async with aiohttp.ClientSession() as session:
        fpl = FPL(session)
        
        


        class Item:
            def __init__(self, weight, value):
                self.weight = weight
                self.value = value
                
        
        knapsackWeight = 100.0
        # ulazne vrednosti su zadate tako da su sortirane prema odnosu vrednost/tezina
        # inace bi trebalo na pocetku izvrsiti njihovo sortiranje zbog algoritma za bound
        
        players = await fpl.get_players()
        
        
        
        items = [Item(1.98, 100),  Item(2, 40), Item(5, 95), Item(3.14, 50), Item(3, 30)]
        print('Maksimalna vrednost:', bnb(knapsackWeight, items))

        


if __name__ == "__main__":
    asyncio.create_task(main())
    
    