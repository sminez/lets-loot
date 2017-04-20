'''
Instances for martial weapons
'''
from ..config import LIGHT1
from .base import Weapon


class ShortSword(Weapon):
    type = 'sword'
    name = 'Short Sword'
    char = '|'
    colour = LIGHT1
    rough_description = 'A common short sword'
    description = 'Forged from cold steel, this short sword has a wicked edge'
    allowed_slots = ['main', 'offhand']
    atk_mod = 0
    dice = [6]
    modifier = 0
    damage_type = 'piercing'
    weight = 2


class LongSword(Weapon):
    type = 'sword'
    name = 'Long Sword'
    char = '|'
    colour = LIGHT1
    rough_description = 'A common long sword'
    description = 'Forged from cold steel, this long sword has a wicked edge'
    allowed_slots = ['main', 'offhand']
    atk_mod = 0
    dice = [8]
    modifier = 0
    damage_type = 'slashing'
    weight = 3


class Axe(Weapon):
    type = 'axe'
    name = 'Axe'
    char = '|'
    colour = LIGHT1
    rough_description = 'A common war axe'
    description = 'Forged from cold steel, this war axe has a wicked edge'
    allowed_slots = ['main', 'offhand']
    atk_mod = 0
    dice = [8]
    modifier = 0
    damage_type = 'slashing'
    weight = 4


class Maul(Weapon):
    type = 'hammer'
    name = 'Maul'
    char = '|'
    colour = LIGHT1
    rough_description = 'A common spiked maul'
    description = 'Covered in sharp spikes, this maul looks...painful.'
    allowed_slots = ['main', 'offhand']
    two_handed = True
    atk_mod = 0
    dice = [6, 6]
    modifier = 0
    damage_type = 'bludgeoning'
    weight = 10
