'''
Common races that are used for PCs, NPCs and enemies
As we are randomly generating characters the free choice options
are made randomly.
'''
from .base import Creature


class Human(Creature):
    '''Humans get +1 to all abilities'''
    size = 'medium'
    race = 'Human'
    type = 'Humanoid'
    skills = []

    def __init__(self, class_, x, y, colour, char):
        abilities = class_.get_ability_scores()

        # Humans get +1 to all abilities
        for ability in abilities:
            if ability not in ['MAX_HP', 'MAX_SP']:
                abilities[ability] += 1

        super().__init__(x=x, y=y, char=char, colour=colour,
                         block_move=False, **abilities)

        # Get some starting equipment based on class
        starting_gear = class_.get_starting_gear(self)
        self.equipment = starting_gear['equipped']
        self.pack = starting_gear['pack']
        self.gold = starting_gear['gold']
