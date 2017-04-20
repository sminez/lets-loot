'''
Generation of Party Characters
'''
from .races import Human
from .classes import Adventurer


def new_PC(x, y, colour, name, race=Human, PC_class=Adventurer):
    '''
    Make a new playable character
    This will eventually work for all races and classes but for now
    it will raise an exception on anything other than a Human Fighter.
    '''
    char = race(PC_class, x, y, colour, '@')
    char.name = name
    return char
