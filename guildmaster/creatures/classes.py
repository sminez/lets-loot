'''
Classes for PCs and NPCs
'''
from ..utils import stat_roll
from collections import namedtuple


# Actions are registered on the character when they reach the correct level
# They are stored in the actions dict which maps level to available actions
# NOTE: range == 0 will allow an action to be used at any time
Action = namedtuple('Action', 'name range func')


def random_ability_scores():
    '''Generate a randomised set of ability scores'''
    return [stat_roll() for _ in range(6)]


def search(character):
    '''Search the surrounding area for traps and secrets'''
    search_range = character.WIS_MOD * 2 if character.WIS_MOD > 0 else 2
    res = character.skill_check(stat='WIS', DC=20, modifier=character.level//2)
    if res.success:
        if res.crit:
            # They found everything in range
            pass
        else:
            # They found one thing in range
            pass


class Class:
    class_name = None
    stat_order = ['CON', 'STR', 'DEX', 'WIS', 'INT', 'CHA']
    hit_die = []
    actions = {}
    skills = []

    @classmethod
    def get_ability_scores(cls):
        '''Generate lvl1 ability scores'''
        ranked_scores = sorted(random_ability_scores(), reverse=True)
        ability_scores = dict(zip(cls.stat_order, ranked_scores))
        ability_scores['MAX_HP'] = (sum(cls.hit_die) +
                                    (ability_scores['CON'] - 10) // 2)
        return ability_scores


class Adventurer(Class):
    '''A jack of all trades'''
    class_name = 'Adventurer'
    stat_order = ['CON', 'STR', 'DEX', 'WIS', 'INT', 'CHA']
    hit_die = [10]
    actions = {2: Action('search', 0, search)}
    skills = []
