'''
Generation of Party Characters
'''
from ..config import LIGHT0
from .races import Human
from .classes import Adventurer


def new_PC(name, race=Human, PC_class=Adventurer):
    '''
    Make a new playable character
    This will eventually work for all races and classes but for now
    it will raise an exception on anything other than a Human Adventurer.
    '''
    char = race(PC_class, 0, 0, LIGHT0, '@')
    char.PC_class = PC_class
    char.name = name
    char.level = 1
    char.current_xp = 0
    char.next_level = 50
    char.player_character = True
    return char
