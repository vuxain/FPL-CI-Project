import aiohttp
import asyncio
from fpl import FPL


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

        p.value = p.total_points / (p.now_cost/10)

    return gks, dfs, mfs, fws


async def main():
    async with aiohttp.ClientSession() as session:
        fpl = FPL(session)
    players = await fpl.get_players()
    gks, dfs, mfs, fws = init(players)

    for x in fws:
        print(x.value)



if __name__ == "__main__":
    asyncio.run(main())
