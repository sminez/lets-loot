'''
Character control classes for Guild Members and Enemies.
--------------------------------------------------------
Most enemies and guild members will be randomly generated but bosses and
special NPCs will be possible through passing 0 for the rand_range.

Core Stats
----------
HP  - Hit Points
DEF - Physical Defence
ATK - Base Physical Attack Power
INT - Natural Intellegence
KNW - Aquired Knowledge
CHR - Charm
WLK - Walking Speed
CAP - Carrying Capacity
VIS - Vision Distance
BRV - Bravery
SAN - Sanity
'''
from random import randint

CORE_STATS = 'HP DEF ATK INT KNW CHR WLK CAR VIS BRV SAN'.split()
DEFAULT_STATS = dict(zip(CORE_STATS, (50 for _ in range(len(CORE_STATS)))))


class NPC:
    ''' Base class for all sentient characters. '''

    def __init__(self, core_stats, sym, name, rand_range=50):
        '''
        core_stats is a dict of the core stats (default values are 50)
        sym is the symbol that will represent the character
        name is the in game name for the charater
        rand_range is the randomisation range for the character.
        '''
        core = self.get_core_stats(core_stats, rand_range)
        self.__dict__.update(core)
        self.sym = sym
        self.backpack = []
        self.equipment = {
            'head': None,
            'chest': None,
            'larm': None,
            'rarm': None,
            'legs': None,
            'feet': None,
            'special': []
        }

    @staticmethod
    def randomise_core_stats(stats, rand_range):
        '''
        Randomise the default stats for a character class.
        Negative values bump up to 0.
        '''
        for key in CORE_STATS:
            if key not in stats:
                raise KeyError('Missing core stat: %s', key)

        for key in stats:
            stats[key] += randint(-rand_range, rand_range)
            stats[key] = 0 if stats[key] < 0 else stats[key]
        return stats
