'''
Main ui classes and interfaces
'''
import tdl
# from ..creatures.base import Creature
from ..creatures.pcs import new_PC
from ..dungeon.mapgen import Dungeon
from ..config import BLACK, DIM_FG1, DIM_FG2, LIGHT0
from ..config import FOV_ALG, FOV_RADIUS1, FOV_RADIUS2, LIGHT_WALLS
from ..config import BAR_WIDTH, PANEL_HEIGHT
from ..config import NEUTRAL_RED, NEUTRAL_YELLOW, NEUTRAL_AQUA, NEUTRAL_GREEN
from ..config import BRIGHT_RED, BRIGHT_YELLOW, BRIGHT_AQUA, BRIGHT_GREEN
from ..config import FADED_RED, FADED_YELLOW, FADED_AQUA, FADED_GREEN


class Screen:
    '''
    Control class that handles setting tdl config options
    and manages the overall UI
    Alternate fonts:
        guildmaster/fonts/dejavu_wide16x16_gs_tc.png True
        guildmaster/fonts/terminal16x16_gs_ro.png False
    '''
    def __init__(self, height=60, width=90, fps=30,
                 panel_height=PANEL_HEIGHT, alt_layout=True,
                 font='guildmaster/fonts/dejavu_wide12x12_gs_tc.png'):
        self.width = width
        self.height = height
        self.map_height = height - panel_height
        self.panel_height = panel_height
        self.panel_y = self.height - self.panel_height
        self.fps = fps
        self.font = font
        self.alt_layout = alt_layout

        # Initialise Multiple characters
        self.char1 = new_PC(1, 1, NEUTRAL_RED, 'Red')
        self.char2 = new_PC(2, 1, NEUTRAL_YELLOW, 'Yellow')
        self.char3 = new_PC(1, 2, NEUTRAL_AQUA, 'Blue')
        self.char4 = new_PC(2, 2, NEUTRAL_GREEN, 'Green')

        self.objects = [self.char2, self.char3, self.char4, self.char1]
        self.visible_tiles = set()
        self.visible_tiles2 = set()

        # Focus on the first charcter
        self.current_char = self.char1

    def render_object(self, obj):
        '''Render an object to the console'''
        if obj.visible:
            self.con.draw_char(obj.x, obj.y, obj.char, obj.colour, bg=None)

    def send_obj_to_back(self, obj):
        '''Cause an object to be rendered first, under everything else'''
        self.objects.remove(obj)
        self.objects.insert(0, obj)

    def send_obj_to_front(self, obj):
        '''Cause an object to be rendered last, on top of everything else'''
        self.objects.remove(obj)
        self.objects.append(obj)

    def clear_object(self, obj):
        '''Remove an object from the console'''
        self.con.draw_char(obj.x, obj.y, ' ', obj.colour, bg=None)

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
            visible_tiles = set()
            visible_tiles2 = set()
            for char in [self.char1, self.char2, self.char3, self.char4]:
                if char.alive:
                    visible_tiles.update(tdl.map.quickFOV(
                        char.x, char.y, visible_tile, fov=FOV_ALG,
                        radius=FOV_RADIUS1, lightWalls=LIGHT_WALLS,
                        sphere=True))
                    visible_tiles2.update(tdl.map.quickFOV(
                        char.x, char.y, visible_tile, fov=FOV_ALG,
                        radius=FOV_RADIUS2, lightWalls=LIGHT_WALLS,
                        sphere=True))

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

    def run(self):
        '''
        Main rendering loop: calls handle_keys
        '''
        tdl.set_font(self.font, greyscale=True, altLayout=self.alt_layout)
        self.root = tdl.init(self.width, self.height,
                             title="GuildMaster", fullscreen=False)
        self.con = tdl.Console(self.width, self.map_height)
        self.panel = Panel(self.width, self.panel_height)
        tdl.set_fps(self.fps)

        self.dungeon = Dungeon(height=self.map_height, width=self.width)
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
            self.root.blit(self.con, 0, 0, self.width, self.map_height, 0, 0)

            # Blit the panel
            self.panel.render_bg()
            self.panel.render_bar(
                1, 2, BAR_WIDTH, 'HP', self.char1.HP,
                self.char1.MAX_HP, BRIGHT_RED, FADED_RED)
            self.panel.render_bar(
                1, 3, BAR_WIDTH, 'HP', self.char2.HP,
                self.char2.MAX_HP, BRIGHT_YELLOW, FADED_YELLOW)
            self.panel.render_bar(
                1, 4, BAR_WIDTH, 'HP', self.char3.HP,
                self.char3.MAX_HP, BRIGHT_AQUA, FADED_AQUA)
            self.panel.render_bar(
                1, 5, BAR_WIDTH, 'HP', self.char4.HP,
                self.char4.MAX_HP, BRIGHT_GREEN, FADED_GREEN)

            self.root.blit(self.panel.panel, 0, self.panel_y, self.width,
                           self.panel_height, 0, 0)

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
            # XXX: return dead objects so they can be sent to the back?
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
        if character.alive:
            self.current_char = character
            self.send_obj_to_front(character)
            # TODO: set AI on other characters


class Panel:
    '''An info panel for the UI'''
    def __init__(self,  width, height, bg=DIM_FG1):
        self.width = width
        self.height = height
        self.bg = bg
        self.panel = tdl.Console(self.width, self.height)

    def render_bg(self):
        '''Render a background colour'''
        self.panel.clear(fg=(0, 0, 0), bg=(0, 0, 0))
        self.panel.draw_rect(0, 0, self.width, self.height, None, bg=self.bg)
        self.panel.draw_rect(0, 1, self.width, self.height-1, None, bg=DIM_FG2)

    def render_bar(self, x, y, width, name, val, max_val, fg, bg):
        '''Render an info bar: hp, xp etc'''
        bar_width = int(val / max_val * width)
        text = '{} :: {}/{}'.format(name, str(val), str(max_val))
        text_x = x + (width - len(text)) // 2

        self.panel.draw_rect(x, y, width, 1, None, bg=bg)

        if bar_width > 0:
            self.panel.draw_rect(x, y, bar_width, 1, None, bg=fg)

        self.panel.draw_str(text_x, y, text, fg=LIGHT0, bg=None)
