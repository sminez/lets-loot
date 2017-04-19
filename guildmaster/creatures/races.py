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

    def __init__(self, class_, x, y, colour):
        abilities = class_.get_ability_scores()

        # Humans get +1 to all abilities
        for ability in abilities:
            if ability != 'MAX_HP':
                abilities[ability] += 1

        super().__init__(AC=10+abilities['DEX'], x=x, y=y, char='@',
                         colour=colour, block_move=False, **abilities)

        self.passive_perception = 10 + self.WIS_MOD
