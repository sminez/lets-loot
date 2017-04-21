'''
Basic mechanics for use in other modules
'''
from random import randint
from collections import namedtuple


SkillCheckResult = namedtuple('SkillCheckResult', 'success crit')
Message = namedtuple('Message', 'text colour')


class GameObject:
    '''
    An arbitray game object, all characters and items need to inherit
    from this in order to be drawable
    '''
    def __init__(self, x, y, char, colour, block_move=False,
                 block_sight=False, visible=True):
        self.x = x
        self.y = y
        self.char = char
        self.colour = colour
        self.block_move = block_move
        self.block_sight = block_sight
        self.visible = visible

    def move(self, dx, dy, screen):
        '''
        Move from current position by an amount (dx,dy)
        '''
        new_x = self.x + dx
        new_y = self.y + dy

        destination = screen.current_map.lmap[new_y][new_x]
        if destination.block_move:
            if destination.name == 'closed_door':
                # open the door
                destination.open_door()
            return []

        for obj in screen.objects:
            if obj.x == new_x and obj.y == new_y and obj.block_move:
                return []

        self.x, self.y = new_x, new_y
        return []


def roll(dice=20, modifier=0):
    '''
    Role a dice with a modifier
    '''
    if isinstance(dice, int):
        return randint(1, dice) + modifier
    elif isinstance(dice, list):
        total = 0
        for die in dice:
            total += randint(1, die)
        return total + modifier


def stat_roll():
    '''
    Make a randomised stat roll
    '''
    rolls = [randint(1, 6) for _ in range(4)]
    return sum(rolls) - min(rolls)


def key_to_coords(key, x, y):
    '''Convert a key and position to a new position'''
    if key in ['k', 'UP']:
        return x, y-1
    elif key in ['j', 'DOWN']:
        return x, y+1
    elif key in ['h', 'LEFT']:
        return x-1, y
    elif key in ['l', 'RIGHT']:
        return x+1, y
    elif key in ['y']:
        return x-1, y-1
    elif key in ['u']:
        return x+1, y-1
    elif key in ['b']:
        return x-1, y+1
    elif key in ['n']:
        return x+1, y+1
