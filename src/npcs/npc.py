'''
Character control classes for Guild Members and Enemies.
--------------------------------------------------------
Most enemies and guild members will be randomly generated but bosses and
special NPCs will be possible through passing 0 for the rand_range.

Core Stats
----------
HP  - Hit Points
ATK - Base Physical Attack Power
DEF - Base Physical Defence
INT - Natural Intellegence
KNW - Aquired Knowledge
OBS - Observation
BRV - Bravery
SAN - Sanity
CHR - Charm
CAP - Carrying Capacity
'''
from random import random


CORE_STATS = 'HP ATK DEF INT KNW OBS BRV SAN CHR CAP'.split()


class NPC:
    ''' Base class for all sentient characters. '''
    CLASS = 'NPC'
    DEFAULT_STATS = dict(zip(CORE_STATS, (50 for _ in range(len(CORE_STATS)))))

    def __init__(self, sym, name, spread=0.3, stats=None):
        '''
        Initialise an NPC by either specifying a full stats dictionary or by
        giving a spread to randomise with.
        '''
        if not stats:
            stats = self._randomise_core_stats(spread)
        self.__dict__.update(stats)
        self.MAX_HP = self.HP
        self.SYM = sym
        self.CLASS = self.__class__.CLASS
        self.PACK = []
        self.NAME = name
        self.EQUIPMENT = {
            'head': None,
            'chest': None,
            'larm': None,
            'rarm': None,
            'legs': None,
            'feet': None,
            'special': []
        }

    @property
    def stats(self):
        extra = ['NAME', 'SYM', 'CLASS', 'MAX_HP']
        d = self.__dict__
        stats = ('{}: {}'.format(stat, d[stat]) for stat in extra + CORE_STATS)
        return '\n'.join(stats)

    def _randomise_core_stats(self, spread):
        '''Randomise the default stats for a character class.'''
        base = self.__class__.DEFAULT_STATS.items()
        stats = {k: v + int(v * (2 * random() - 1) * spread) for k, v in base}
        return stats
