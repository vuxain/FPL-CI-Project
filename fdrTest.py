import asyncio

import aiohttp
from colorama import Fore, init
from prettytable import PrettyTable
import time


from fpl import FPL


async def main():
    async with aiohttp.ClientSession() as session:
        fpl = FPL(session)
        team = await fpl.get_team(13)

        tekme = await team.get_fixtures()

        [print(x) for x in tekme]

        #----------


        fdr = await fpl.FDR()
        fdr_table = PrettyTable()
        fdr_table.field_names = [
            "Team", "All (H)", "All (A)", "GK (H)", "GK (A)", "DEF (H)", "DEF (A)",
            "MID (H)", "MID (A)", "FWD (H)", "FWD (A)"]

        for team, positions in fdr.items():
            row = [team]
            for difficulties in positions.values():
                for location in ["H", "A"]:
                    if difficulties[location] == 5.0:
                        row.append(Fore.RED + "5.0" + Fore.RESET)
                    elif difficulties[location] == 1.0:
                        row.append(Fore.GREEN + "1.0" + Fore.RESET)
                    else:
                        row.append(f"{difficulties[location]:.2f}")

            fdr_table.add_row(row)

        fdr_table.align["Team"] = "l"
        print(fdr_table)

        ####################

        # def positionName(posId):
        #     if posId == 1:
        #         return 'goalkeeper'
        #     elif posId == 2:
        #         return 'defender'
        #     elif posId == 3:
        #         return 'midfielder'
        #     else:
        #         return 'forward'
        #
        # player = await fpl.get_player(302)
        # team = await fpl.get_team(player.team)
        # remainingGWs = await team.get_fixtures()
        # fdr = await fpl.FDR()
        #
        # playerEvaluation = 0
        #
        # for game in remainingGWs:
        #     teamFacingId, HomeAwayId = (game['team_h'], 'A') if game['team_h'] != player.team else (game['team_a'], 'H')
        #     teamFacing = await fpl.get_team(teamFacingId)
        #
        #     playerEvaluation += fdr[teamFacing.name][positionName(player.element_type)][HomeAwayId]
        #
        # print( playerEvaluation )

        # kurac = await fpl.get_points_against()
        #
        # print(kurac)

        print([3 for x in range(21)])

if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
