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
        self.atk_range = 1  # 1/2/3 -> close/medium/long
        self.EQUIPMENT = {
            k: None for k in
            ['head', 'chest', 'larm', 'rarm', 'legs', 'feet', 'special']
        }
        self.x = 0
        self.y = 0

    def __repr__(self):
        '''Pretty print this NPCs stats'''
        extra = ['NAME', 'SYM', 'MAX_HP']
        d = self.__dict__
        stats = ('{}: {}'.format(stat, d[stat]) for stat in extra + CORE_STATS)
        return 'CLASS: {}\n'.format(self.CLASS) + '\n'.join(stats)

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
        if self.distance_to(target) <= self.atk_range:
            outcome = target.get_hit(self.ATK, self.BRV, self.SAN)
            self.process_attack_outcome(outcome)
        else:
            raise FailedAttack('Out of range')

    def distance_to(self, other):
        '''Integer distance to another object (rounded down)'''
        return int(((self.x - other.x)**2 + (self.y - other.y)**2)**0.5)

    def get_hit(self, atk, brv, san):
        '''Take a hit from an attack'''
        damage = atk - self.DEF
        outcome = {'damage': damage, 'stat_based': {}}

        if damage > 0:
            self.HP -= damage
            if self.HP <= 0:
                self.die()

        if san <= 20 and self.SAN > 20:
            # Crazy people freak out normal people
            reduction = ((self.SAN - san) // 10) + 1
            self.BRV -= reduction
            outcome['stat_based']['BRV'] = -reduction
        elif brv >= 55 and self.SAN < 20:
            # Heroically brave people beat insanity out you
            increase = ((brv - self.SAN) // 10) + 1
            self.SAN += increase
            outcome['stat_based']['SAN'] = increase

        return self.effects_on_attacked(outcome)

    def effects_on_attacked(self, outcome):
        '''For subclasses to add additional effects'''
        return outcome

    def process_attack_outcome(self, outcome):
        '''Deal with post-attack effects on the attacker'''
        if outcome['damage'] <= 0:
            # Failed attacks demoralise
            self.BRV -= 1
        if outcome['damage'] <= -10:
            # That REALLY failed
            self.BRV -= 2

        for k, v in outcome['stat_based'].items():
            self.__dict__[k] += v

    def die(self):
        '''Handle character death effects'''
        print('{} died...'.format(self.NAME))
