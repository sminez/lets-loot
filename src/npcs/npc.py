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


# All NPCs share the same core stats
CORE_STATS = 'HP ATK DEF INT KNW OBS BRV SAN CHR CAP'.split()


class FailedAttack(Exception):
    pass


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
        self.PACK = []
        self.NAME = name
        self._atk_range = 0  # 0/1/2 -> close/medium/long
        self.EQUIPMENT = {
            k: None for k in
            ['head', 'chest', 'larm', 'rarm', 'legs', 'feet', 'special']
        }

    @property
    def stats(self):
        '''Pretty print this NPCs stats'''
        extra = ['NAME', 'SYM', 'MAX_HP']
        d = self.__dict__
        stats = ('{}: {}'.format(stat, d[stat]) for stat in extra + CORE_STATS)
        print('CLASS: {}\n'.format(self.CLASS) + '\n'.join(stats))

    def _randomise_core_stats(self, spread):
        '''Randomise the default stats for a character class.'''
        base = self.__class__.DEFAULT_STATS.items()
        stats = {k: v + int(v * (2 * random() - 1) * spread) for k, v in base}
        return stats

    def attack(self, target):
        '''
        Make a basic attack against another character/object.
        The target must be inside of the attack range.
        Attacker's bravery and sanity may affect the target as well.
        '''
        if self._target_in_range(target):
            outcome = target.get_hit(self.ATK, self.BRV, self.SAN)
            self._process_attack_outcome(outcome)
        else:
            raise FailedAttack('Out of range')

    def _target_in_range(self, target):
        return get_range(self, target) <= self._atk_range
