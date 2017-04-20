'''
Global config options
'''
from .utils import tilemaker


# Colours
# Taken from https://github.com/morhetz/gruvbox-contrib/blob/master/color.table
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

DARK0 = (40, 40, 40)
DARK1 = (60, 56, 54)
DARK2 = (80, 73, 69)
DARK3 = (102, 92, 84)
DARK4 = (124, 111, 100)

GRAY = (146, 131, 116)

LIGHT0 = (251, 241, 215)
LIGHT1 = (235, 219, 178)
LIGHT2 = (213, 196, 161)
LIGHT3 = (189, 174, 147)
LIGHT4 = (168, 153, 132)

BRIGHT_RED = (251, 73, 52)
BRIGHT_GREEN = (184, 187, 38)
BRIGHT_YELLOW = (250, 189, 47)
BRIGHT_BLUE = (131, 134, 155)
BRIGHT_PURPLE = (211, 134, 155)
BRIGHT_AQUA = (142, 192, 124)
BRIGHT_ORANGE = (254, 128, 25)

NEUTRAL_RED = (204, 36, 29)
NEUTRAL_GREEN = (152, 151, 26)
NEUTRAL_YELLOW = (215, 153, 33)
NEUTRAL_BLUE = (69, 133, 136)
NEUTRAL_PURPLE = (177, 98, 134)
NEUTRAL_AQUA = (104, 157, 106)
NEUTRAL_ORANGE = (214, 93, 14)

FADED_RED = (157, 0, 6)
FADED_GREEN = (121, 116, 14)
FADED_YELLOW = (181, 118, 20)
FADED_BLUE = (7, 102, 120)
FADED_PURPLE = (143, 63, 113)
FADED_AQUA = (66, 123, 88)
FADED_ORANGE = (175, 58, 3)

# Named colours
DIM_FG1 = (25, 25, 25)
DIM_FG2 = (32, 32, 32)

# Tiles
ROCK = tilemaker("#", fg=DARK4, bg=DARK0, block_move=True,
                 block_sight=True, explored=False)
FLOOR = tilemaker(".", fg=DARK1, bg=DARK0, block_move=False,
                  block_sight=False, explored=False)
UP = tilemaker(">", fg=WHITE, bg=DARK0, block_move=False,
               block_sight=False, explored=False)
DOWN = tilemaker("<", fg=WHITE, bg=DARK0, block_move=False,
                 block_sight=False, explored=False)
CLOSED_DOOR = tilemaker("+", fg=DARK2, bg=DARK0, block_move=True,
                        block_sight=True, explored=False)
OPEN_DOOR = tilemaker("'", fg=DARK2, bg=DARK0, block_move=False,
                      block_sight=False, explored=False)
SECRET_DOOR = tilemaker("#", fg=DARK4, bg=DARK0, block_move=False,
                        block_sight=True, explored=False)

# MapGen paramaters
MIN_ROOM_SIZE = 7
MAX_ROOM_SIZE = 14
MAX_ROOMS = 60

# FOV
# BASIC, DIAMOND, SHADOW, PERMISSIVE, RESTRICTIVE
FOV_ALG = 'SHADOW'
FOV_RADIUS1 = 7
FOV_RADIUS2 = 10
LIGHT_WALLS = True


# Panel config
BAR_WIDTH = 20
PANEL_HEIGHT = 8
