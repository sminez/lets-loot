'''
Main ui classes and interfaces
'''
import tdl
from ..creatures.base import Creature
from ..creatures.pcs import new_PC
from ..dungeon.mapgen import Dungeon
from ..config import FADED_RED, FADED_YELLOW, FADED_AQUA, FADED_GREEN
from ..config import BLACK, DIM_FG1, DIM_FG2
from ..config import FOV_ALG, FOV_RADIUS1, FOV_RADIUS2, LIGHT_WALLS


class Screen:
    '''
    Control class that handles setting tdl config options
    and manages the overall UI
    '''

    def __init__(self, height=60, width=90, fps=20,
                 font='guildmaster/fonts/dejavu16x16_gs_tc.png'):
        self.width = width
        self.height = height
        self.fps = fps
        self.font = font

        # Initialise Multiple characters
        self.char1 = new_PC(1, 1, FADED_RED, 'Red')
        self.char2 = new_PC(2, 1, FADED_YELLOW, 'Yellow')
        self.char3 = new_PC(1, 2, FADED_AQUA, 'Blue')
        self.char4 = new_PC(2, 2, FADED_GREEN, 'Green')

        self.objects = [self.char2, self.char3, self.char4, self.char1]
        self.visible_tiles = set()
        self.visible_tiles2 = set()

        # Focus on the first charcter
        self.current_char = self.char1

    def render_object(self, obj):
        '''Render an object to the console'''
        if obj.visible:
            self.con.draw_char(obj.x, obj.y, obj.char, obj.colour, bg=None)

    def render_map(self, lmap, compute_fov):
        '''Rended the nested list structure as the map'''
        def visible_tile(x, y):
            if x >= len(lmap[0]) or x < 0:
                return False
            elif y >= len(lmap) or y < 0:
                return False
            else:
                return not lmap[y][x].block_sight

        if compute_fov:
            visible_tiles = tdl.map.quickFOV(
                self.char1.x, self.char1.y, visible_tile, fov=FOV_ALG,
                radius=FOV_RADIUS1, lightWalls=LIGHT_WALLS, sphere=True)
            visible_tiles.update(tdl.map.quickFOV(
                self.char2.x, self.char2.y, visible_tile, fov=FOV_ALG,
                radius=FOV_RADIUS1, lightWalls=LIGHT_WALLS, sphere=True))
            visible_tiles.update(tdl.map.quickFOV(
                self.char3.x, self.char3.y, visible_tile, fov=FOV_ALG,
                radius=FOV_RADIUS1, lightWalls=LIGHT_WALLS, sphere=True))
            visible_tiles.update(tdl.map.quickFOV(
                self.char4.x, self.char4.y, visible_tile, fov=FOV_ALG,
                radius=FOV_RADIUS1, lightWalls=LIGHT_WALLS, sphere=True))
            visible_tiles2 = tdl.map.quickFOV(
                self.char1.x, self.char1.y, visible_tile, fov=FOV_ALG,
                radius=FOV_RADIUS2, lightWalls=LIGHT_WALLS, sphere=True)
            visible_tiles2.update(tdl.map.quickFOV(
                self.char2.x, self.char2.y, visible_tile, fov=FOV_ALG,
                radius=FOV_RADIUS2, lightWalls=LIGHT_WALLS, sphere=True))
            visible_tiles2.update(tdl.map.quickFOV(
                self.char3.x, self.char3.y, visible_tile, fov=FOV_ALG,
                radius=FOV_RADIUS2, lightWalls=LIGHT_WALLS, sphere=True))
            visible_tiles2.update(tdl.map.quickFOV(
                self.char4.x, self.char4.y, visible_tile, fov=FOV_ALG,
                radius=FOV_RADIUS2, lightWalls=LIGHT_WALLS, sphere=True))

            self.visible_tiles = visible_tiles
            self.visible_tiles2 = visible_tiles2 - visible_tiles

        for y, row in enumerate(lmap):
            for x, tile in enumerate(row):
                if (x, y) in self.visible_tiles:
                    tile.explored = True
                    self.con.draw_char(x, y, tile.char,
                                       fg=tile.fg, bg=tile.bg)
                elif (x, y) in self.visible_tiles2:
                    self.con.draw_char(x, y, tile.char,
                                       fg=DIM_FG2, bg=BLACK)
                else:
                    if tile.explored:
                        self.con.draw_char(x, y, tile.char,
                                           fg=DIM_FG1, bg=BLACK)
                    else:
                        self.con.draw_char(x, y, ' ',
                                           fg=None, bg=BLACK)

    def clear_object(self, obj):
        '''Remove an object from the console'''
        self.con.draw_char(obj.x, obj.y, ' ', obj.colour, bg=None)

    def run(self):
        '''
        Main rendering loop: calls handle_keys
        '''
        tdl.set_font(self.font, greyscale=True, altLayout=True)
        self.root = tdl.init(self.width, self.height,
                             title="GuildMaster", fullscreen=False)
        self.con = tdl.Console(self.width, self.height)
        tdl.set_fps(self.fps)

        self.dungeon = Dungeon(height=self.height, width=self.width)
        self.current_map = self.dungeon[0]
        x, y = self.current_map.rooms[0].center
        self.char1.x, self.char1.y = x, y
        self.char2.x, self.char2.y = x+1, y
        self.char3.x, self.char3.y = x, y+1
        self.char4.x, self.char4.y = x+1, y+1

        compute_fov = True

        while not tdl.event.is_window_closed():
            self.render_map(self.current_map.lmap, compute_fov)

            for obj in self.objects:
                self.render_object(obj)

            # Blit the hidden console to the screen
            # NOTE: 0,0s line up both consoles (my what a pythonic api...)
            self.root.blit(self.con, 0, 0, self.width, self.height, 0, 0)
            tdl.flush()

            # Clear the screen
            for obj in self.objects:
                self.clear_object(obj)

            compute_fov, should_exit, tick = self.handle_keys(self)

            # if tick:
            #     for obj in self.objects:
            #         if obj is not self.current_char:
            #             obj.action()
            if should_exit:
                break

    def handle_keys(self, lmap):
        '''
        Handle keyboard input from the user. Full keylist can be found here:
        https://pythonhosted.org/tdl/tdl.event.KeyEvent-class.html#key
        '''
        keypress = tdl.event.key_wait()
        compute_fov = tick = False

        # Movement
        if keypress.key in ['UP', 'DOWN', 'LEFT', 'RIGHT']:
            compute_fov = tick = True

        if keypress.key == 'UP':
            self.current_char.move_or_melee(0, -1, lmap)
        elif keypress.key == 'DOWN':
            self.current_char.move_or_melee(0, 1, lmap)
        elif keypress.key == 'LEFT':
            self.current_char.move_or_melee(-1, 0, lmap)
        elif keypress.key == 'RIGHT':
            self.current_char.move_or_melee(1, 0, lmap)
        # Character switch
        elif keypress.key == '1':
            self.focus_character(self.char1)
        elif keypress.key == '2':
            self.focus_character(self.char2)
        elif keypress.key == '3':
            self.focus_character(self.char3)
        elif keypress.key == '4':
            self.focus_character(self.char4)
        # Game control
        elif keypress.key == 'ENTER' and keypress.alt:
            # Alt+Enter == toggle fullscreen
            tdl.set_fullscreen(True)
        elif keypress.key == 'ESCAPE':
            return compute_fov, True, tick

        return compute_fov, False, tick

    def focus_character(self, character):
        '''
        Switch control to the selected character and make sure that they
        are rendered on top of everything else
        '''
        self.current_char = character
        self.objects.remove(character)
        self.objects.append(character)
        # TODO: set AI on other characters
