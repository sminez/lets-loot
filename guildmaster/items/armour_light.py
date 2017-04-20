'''
Light armour
'''
from ..config import FADED_ORANGE
from .base import Armour


class Padded(Armour):
    type = 'light'
    stealth_disadvantage = True
    name = 'Padded coat'
    char = ';'
    colour = FADED_ORANGE
    rough_description = 'A stiff padded coat'
    description = 'This padded coat smells...ripe.'
    allowed_slots = ['chest']
    AC_base = 11
    weight = 8


class Leather(Armour):
    type = 'light'
    stealth_disadvantage = False
    name = 'Leather armour'
    char = ';'
    colour = FADED_ORANGE
    rough_description = 'Common leather armour'
    description = "Common leather armour, the adventurer's friend"
    allowed_slots = ['chest']
    AC_base = 11
    weight = 10


class StuddedLeather(Armour):
    type = 'light'
    stealth_disadvantage = False
    name = 'Studded Leather armour'
    char = ';'
    colour = FADED_ORANGE
    rough_description = 'Studded leather armour'
    description = ("The metal rivets in this leather armour"
                   "improve its effectiveness")
    allowed_slots = ['chest']
    AC_base = 12
    weight = 13
