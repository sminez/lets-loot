'''
Main ui classes and interfaces
'''
import tdl
import textwrap
# from ..creatures.base import Creature
from ..creatures.pcs import new_PC
from ..dungeon.mapgen import Dungeon
from ..config import BAR_WIDTH, PANEL_HEIGHT
from ..config import BLACK, DIM_FG1, DIM_FG2, LIGHT0, LIGHT4, DARK0
from ..config import BRIGHT_RED, FADED_RED, BRIGHT_AQUA, FADED_AQUA
from ..config import FOV_ALG, FOV_RADIUS1, FOV_RADIUS2, LIGHT_WALLS


class Screen:
    '''
    Control class that handles setting tdl config options
    and manages the overall UI
    Alternate fonts:
        guildmaster/fonts/dejavu_wide16x16_gs_tc.png True
        guildmaster/fonts/dejavu_wide12x12_gs_tc.png True
        guildmaster/fonts/terminal16x16_gs_ro.png False
        guildmaster/fonts/terminal12x12_gs_ro.png False
        guildmaster/fonts/consolas_unicode_16x16.png False
    '''
    def __init__(self, height=60, width=90, fps=30, panel_height=PANEL_HEIGHT,
                 hp_bar_width=BAR_WIDTH, alt_layout=False,
                 font='guildmaster/fonts/terminal12x12_gs_ro.png'):
        self.width = width
        self.height = height
        self.map_height = height - panel_height
        self.panel_height = panel_height
        self.panel_y = self.height - self.panel_height
        self.hp_bar_width = hp_bar_width
        self.message_width = width - hp_bar_width - 2

        self.fps = fps
        self.font = font
        self.alt_layout = alt_layout

        # Initialise the player
        # TODO : character creation screen
        self.player = new_PC('Player')
        self.player_and_allies = [self.player]
        self.objects = [self.player]

        self.visible_tiles = set()
        self.visible_tiles2 = set()

        # initialise message queue
        self.messages = []

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
            for char in self.player_and_allies:
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
        self.panel = Panel(self.width, self.panel_height, self.hp_bar_width)
        tdl.set_fps(self.fps)

        self.dungeon = Dungeon(height=self.map_height, width=self.width)
        self.current_map = self.dungeon[0]
        x, y = self.current_map.rooms[0].center
        self.player.x, self.player.y = x, y

        compute_fov = True

        while not tdl.event.is_window_closed():
            self.render_map(self.current_map.lmap, compute_fov)

            for obj in self.objects:
                self.render_object(obj)

            # Blit the hidden console to the screen
            self.root.blit(self.con, 0, self.panel_height, self.width,
                           self.map_height, 0, 0)

            # Blit the panel
            self.panel.render_bg()
            self.panel.render_stats(self.player)

            self.panel.render_messages(self.messages)

            self.root.blit(self.panel.panel, 0, 0, self.width,
                           self.panel_height, 0, 0)

            tdl.flush()

            # Clear the screen
            for obj in self.objects:
                self.clear_object(obj)

            compute_fov, should_exit, tick = self.handle_keys(self)

            if tick:
                for obj in self.objects:
                    if obj is not self.player:
                        obj.action()

            if should_exit:
                break

    def handle_keys(self, lmap):
        '''
        Handle keyboard input from the user. Full keylist can be found here:
        https://pythonhosted.org/tdl/tdl.event.KeyEvent-class.html#key
        '''
        keypress = tdl.event.key_wait()
        compute_fov = tick = False
        messages = []

        # Movement
        if keypress.key in ['UP', 'DOWN', 'LEFT', 'RIGHT']:
            compute_fov = tick = True

        if keypress.key == 'UP':
            messages = self.player.move_or_melee(0, -1, lmap)
        elif keypress.key == 'DOWN':
            messages = self.player.move_or_melee(0, 1, lmap)
        elif keypress.key == 'LEFT':
            messages = self.player.move_or_melee(-1, 0, lmap)
        elif keypress.key == 'RIGHT':
            messages = self.player.move_or_melee(1, 0, lmap)

        # Menus
        elif keypress.keychar == 'i':
            item = self.menu_selection('Inventory', 40, 40, self.player.pack)
            if item is not None:
                messages = self.player.use_item(item)

        # Actions
        elif keypress.keychar == 'r' and keypress.shift:
            # R to rest
            tick = True
            messages = self.player.rest()

        # Game control
        elif keypress.key == 'ENTER' and keypress.alt:
            # Alt+Enter == toggle fullscreen
            tdl.set_fullscreen(True)
        elif keypress.key == 'ESCAPE' and keypress.alt:
            should_exit = self.menu_selection(
                'Really quit?', 20, 10, ['yes', 'no'], ['y', 'n'])
            if should_exit == 0:
                # TODO: implement run saving
                return compute_fov, True, tick

        for message in messages:
            self.add_message(message)

        return compute_fov, False, tick

    def add_message(self, message):
        '''Add a new message to the message buffer'''
        new_message_lines = textwrap.wrap(message.text, self.message_width)

        for line in new_message_lines:
            # Overflow the messages to make space if needed
            if len(self.messages) == self.panel_height - 1:
                self.messages.pop(0)
            self.messages.append((line, message.colour))

    def menu_selection(self, title, width, height, options, keys=None):
        '''Render a menu and return a selected index from options'''
        def chunked(l):
            return [l[i:i+26] for i in range(0, len(l), 26)]

        # Keep here for quicker debugging in dynamic use
        if keys is not None and len(keys) != len(options):
            raise IndexError('incorrect number of keys given for options')

        title = textwrap.wrap('.: ' + title + ' :.', width)
        chunked_options = chunked(options)

        window = tdl.Console(width, height)
        window.draw_rect(0, 0, width, height, None, fg=LIGHT0, bg=DARK0)
        for i, line in enumerate(title):
            window.draw_str(0, 0+i, title[i], bg=None)

        block_index = 0

        while True:
            y = len(title)
            if keys is None:
                ix = ord('a')
                if len(chunked_options) > 0:
                    for option in chunked_options[block_index]:
                        text = '[' + chr(ix) + '] ' + option
                        window.draw_str(0, y, text, bg=None)
                        y += 1
                        ix += 1
            else:
                for key, option in zip(keys, options):
                    text = '[' + key + '] ' + option
                    window.draw_str(0, y, text, bg=None)
                    y += 1

            x = self.width // 2 - width // 2
            y = self.height // 2 - height // 2
            self.root.blit(window, x, y, width, height, 0, 0)
            tdl.flush()

            # NOTE: The menu activation keystroke seems to hang around
            # Catch it here to avoid it acting as the selection.
            tdl.event.key_wait()

            # Read the player input
            key = tdl.event.key_wait()

            # Backspace to exit without making a choice
            if key.char == '\x08':
                return
            # Toggle pages with [, ]
            elif key.char == '[':
                if block_index != 0:
                    block_index -= 1
            elif key.char == ']':
                if block_index != len(chunked_options):
                    block_index += 1
            # Try to use the character as a selection
            else:
                # XXX:  Some keys return CHAR and some return TEXT...!
                # NOTE: ord(a) == 97 and it is our offset to convert
                #       back to a list index
                key = key.char if key.key == 'CHAR' else key.text
                try:
                    selected_index = ord(key) - 97
                except TypeError:
                    # Modifier key
                    continue

                if keys is None:
                    if 0 <= selected_index <= len(options):
                        return selected_index + block_index * 26
                else:
                    if key in keys:
                        return keys.index(key)


class Panel:
    '''An info panel for the UI'''
    def __init__(self,  width, height, hp_bar_width, bg=DIM_FG1):
        self.width = width
        self.height = height
        self.hp_bar_width = hp_bar_width
        self.msg_x = hp_bar_width + 2
        self.bg = bg
        self.panel = tdl.Console(self.width, self.height)

    def render_bg(self):
        '''Render a background colour'''
        self.panel.clear(fg=(0, 0, 0), bg=(0, 0, 0))
        self.panel.draw_rect(0, self.height-2, self.width, self.height, None,
                             bg=self.bg)
        self.panel.draw_rect(0, 0, self.width, self.height-1, None, bg=DIM_FG2)

    def render_bar(self, x, y, name, val, max_val, fg, bg):
        '''Render an info bar: hp, xp etc'''
        bar_width = int(val / max_val * self.hp_bar_width)
        text = '{}:{}/{}'.format(name, str(val), str(max_val))
        text_x = x + (self.hp_bar_width - len(text)) // 2

        self.panel.draw_rect(x, y, self.hp_bar_width, 1, None, bg=bg)

        if bar_width > 0:
            self.panel.draw_rect(x, y, bar_width, 1, None, bg=fg)

        self.panel.draw_str(text_x, y, text, fg=LIGHT0, bg=None)

    def render_stats(self, player):
        title = '.: {} :.'.format(player.name)
        text_x = 1 + (self.hp_bar_width - len(title)) // 2
        self.panel.draw_str(text_x, 1, title, bg=DIM_FG2, fg=LIGHT0)
        self.render_bar(
            1, 2, 'HP', player.HP, player.MAX_HP, BRIGHT_RED, FADED_RED)
        self.render_bar(
            1, 3, 'SP', player.SP, player.MAX_SP, BRIGHT_AQUA, FADED_AQUA)
        self.render_bar(
            1, 4, 'XP', player.current_xp, player.next_level, LIGHT0, LIGHT4)

    def render_messages(self, messages):
        '''Display the current messages'''
        y = 1
        for line, colour in messages:
            self.panel.draw_str(self.msg_x, y, line, bg=None, fg=colour)
            y += 1
