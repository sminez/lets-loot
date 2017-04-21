'''
Base classes and methods for items and equipment
'''
from ..utils import GameObject, roll


class Item(GameObject):
    '''Base class for items'''
    name = None
    char = None
    colour = None
    block_sight = False
    block_move = False
    visible = True
    identified = False
    description = 'An item!'
    rough_description = 'An item...'
    weight = 0

    def __init__(self, x, y):
        super().__init__(
            x, y, self.char, self.colour, self.block_move,
            self.block_sight, self.visible)

    @property
    def description(self):
        '''Return a description of the item'''
        if self.identified:
            return self.description
        else:
            return self.rough_description

    def use(self, target):
        '''What happens when you use the item'''
        raise NotImplementedError


class Equipment(Item):
    allowed_slots = []

    def on_equip(self, wearer):
        '''Handle equip effects'''
        return []


class Armour(Item):
    allowed_slots = ['chest']
    AC_base = 10
    type = 'light'
    stealth_disadvantage = False

    @classmethod
    def dex_mod(cls, wearer):
        if cls.type == 'heavy':
            return 0
        elif cls.type == 'medium':
            return max(2, wearer.modifier('DEX'))
        else:
            return wearer.modifier('DEX')


class Weapon(Equipment):
    atk_mod = 0
    dice = []
    modifier = 0
    damage_type = 'slashing'
    two_handed = False

    @classmethod
    def damage(cls):
        '''A damage roll'''
        return roll(cls.dice, cls.modifier)

    @classmethod
    def crit(cls):
        '''Damage roll for a crit'''
        return roll(cls.dice + cls.dice, cls.modifier)
