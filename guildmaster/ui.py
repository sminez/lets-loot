'''
Main ui classes and interfaces
'''
import tdl
import textwrap
from .utils import Message
from .dungeon.mapgen import Dungeon
from .player_character import new_PC
from .config import FOV_ALG, LIGHT_WALLS
from .config import BAR_WIDTH, PANEL_HEIGHT, VIM_BINDINGS
from .config import BLACK, DIM_FG1, DIM_FG2, LIGHT0, LIGHT4, DARK0
from .config import BRIGHT_RED, FADED_RED, BRIGHT_AQUA, FADED_AQUA


class GameScreen:
    '''
    Control class that handles setting tdl config options
    and manages the overall UI
    See http://mifki.com/df/fontgen/ for generating fonts.
    Requires running this on the file you get:
    convert tileset.png -background black -alpha remove <name>.png
    '''
    def __init__(self, height=60, width=90, fps=30, panel_height=PANEL_HEIGHT,
                 hp_bar_width=BAR_WIDTH, alt_layout=False,
                 font='guildmaster/fonts/terminal12x12_gs_ro.png',
                 # font='guildmaster/fonts/hack15x15.png',
                 vim_bindings=VIM_BINDINGS):
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

        self.vim_bindings = vim_bindings

        # Initialise the player
        # TODO : character creation screen
        self.player = new_PC('Player', 'Human')
        self.player_and_allies = [self.player]
        self.objects = [self.player]

        self.visible_tiles = set()
        self.visible_tiles2 = set()
        self.magically_visible = set()

        # initialise message queue
        self.messages = []

        tdl.set_font(self.font, greyscale=True, altLayout=self.alt_layout,
                     columns=16, rows=16)
        tdl.event.set_key_repeat(delay=500, interval=50)
        self.root = tdl.init(self.width, self.height,
                             title="Guild Master", fullscreen=False)
        self.con = tdl.Console(self.width, self.map_height)
        self.panel = Panel(self.width, self.panel_height, self.hp_bar_width)
        tdl.set_fps(self.fps)

    def main_menu(self):
        '''Main menu for starting / loading games'''
        # http://www.network-science.de/ascii/
        while True:
            choice = self.menu_selection(
                '''\
=============================================================================
=                                                                           =
=                   ________ ____ ___.___.____     ________                 =
=             /\   /  _____/|    |   \   |    |    \______ \    /\          =
=             \/  /   \  ___|    |   /   |    |     |    |  \   \/          =
=             /\  \    \_\  \    |  /|   |    |___  |    |   \  /\          =
=          /\ \/   \______  /______/ |___|_______ \/_______  /  \/  /\\      =
=          \/             \/                     \/        \/       \/      =
=        _____      _____    _________________________________________      =
=       /     \    /  _  \  /   _____/\__    ___/\_   _____/\______   \\     =
=      /  \ /  \  /  /_\  \ \_____  \   |    |    |    __)_  |       _/     =
=     /    Y    \/    |    \/        \  |    |    |        \ |    |   \\     =
=     \____|__  /\____|__  /_______  /  |____|   /_______  / |____|_  /     =
=             \/         \/        \/                    \/         \/      =
=============================================================================
                _         _   _       _                _   _
               | |    ___| |_( )___  | |    ___   ___ | |_| |
               | |   / _ \ __|// __| | |   / _ \ / _ \| __| |
               | |__|  __/ |_  \__ \ | |__| (_) | (_) | |_|_|
               |_____\___|\__| |___/ |_____\___/ \___/ \__(_)
''',
                80, 30, ['New', 'Continue', 'Quit'], ['n', 'c', 'q'],
                bg=None, ascii_art=True)

            if choice == 0:
                # TODO: always load persistant guild state
                # self.player_character = self.new_character()
                self.run()
            if choice == 1:
                try:
                    self.load_game()
                except:
                    self.msgbox('\n No saved game to load.\n', 24)
                    continue
                self.run()
            elif choice == 2:
                break

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

    def render_map(self, lmap, compute_fov_agro):
        '''Rended the nested list structure as the map'''
        def visible_tile(x, y):
            if x >= len(lmap[0]) or x < 0:
                return False
            elif y >= len(lmap) or y < 0:
                return False
            else:
                return not lmap[y][x].block_sight

        if compute_fov_agro:
            self.dungeon.pathfinder.agro_heatmap(self.player)
            visible_tiles = set()
            visible_tiles2 = set()
            for char in self.player_and_allies:
                if char.alive:
                    visible_tiles.update(tdl.map.quickFOV(
                        char.x, char.y, visible_tile, fov=FOV_ALG,
                        radius=self.player.vision[0], lightWalls=LIGHT_WALLS,
                        sphere=True))
                    visible_tiles2.update(tdl.map.quickFOV(
                        char.x, char.y, visible_tile, fov=FOV_ALG,
                        radius=self.player.vision[1], lightWalls=LIGHT_WALLS,
                        sphere=True))

            self.visible_tiles = visible_tiles
            self.visible_tiles2 = visible_tiles2 - visible_tiles

        for y, row in enumerate(lmap):
            for x, tile in enumerate(row):
                # XXX: Uncomment to view the agro heatmap on floor tiles
                # tile.explored = True
                # if tile.name == 'floor':
                #     tile.char = chr(96 + tile.agro_weight)

                if (x, y) in self.visible_tiles:
                    tile.explored = True
                    self.con.draw_char(x, y, tile.char, fg=tile.fg, bg=tile.bg)
                elif (x, y) in self.visible_tiles2:
                    self.con.draw_char(x, y, tile.char, fg=DIM_FG2, bg=BLACK)
                elif (x, y) in self.magically_visible:
                    self.con.draw_char(x, y, tile.char, fg=tile.fg, bg=BLACK)
                else:
                    if tile.explored:
                        self.con.draw_char(x, y, tile.char,
                                           fg=DIM_FG1, bg=BLACK)
                    else:
                        self.con.draw_char(x, y, ' ', fg=None, bg=BLACK)

    def run(self):
        '''
        Main rendering loop: calls handle_keys
        '''
        # initialise message queue
        self.messages = []

        self.dungeon = Dungeon(height=self.map_height, width=self.width)
        self.current_map = self.dungeon[0]
        x, y = self.current_map.rooms[0].center
        self.player.x, self.player.y = x, y

        compute_fov_agro = True

        while not tdl.event.is_window_closed():
            self.render_map(self.current_map.lmap, compute_fov_agro)

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

            compute_fov_agro, should_exit, tick = self.handle_keys(self)

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
        compute_fov_agro = False
        tick = True
        messages = []

        # Movement
        if self.vim_bindings:
            directions = {'k': (0, -1), 'j': (0, 1),
                          'h': (-1, 0), 'l': (1, 0),
                          'y': (-1, -1), 'u': (1, -1),
                          'b': (-1, 1), 'n': (1, 1)}
            key = keypress.keychar
        else:
            directions = {'UP': (0, -1), 'DOWN': (0, 1),
                          'LEFT': (-1, 0), 'RIGHT': (1, 0)}
            key = keypress.key

        if key in directions:
            compute_fov_agro = True
            x, y = directions[key]
            messages = self.player.move_or_melee(x, y, lmap)

        # Menus
        elif keypress.keychar == 'i':
            item = self.menu_selection('Inventory', 40, 40, self.player.pack)
            if item is not None:
                messages = self.player.use_item(item)

        # Actions
        elif keypress.keychar == '.':
            # . : Force tick with no action
            pass
        elif keypress.keychar == 'c':
            # c : close a door
            choice = self.current_map.close_door(
                self, self.player.x, self.player.y)
            if choice is not None:
                choice.closed_door()
                self.render_map(self.current_map.lmap, compute_fov_agro=True)
                messages = [Message('You close the door', LIGHT0)]
            else:
                tick = False
                messages = [Message("You don't see anything to close", LIGHT0)]
        elif keypress.keychar == 'r' and keypress.shift:
            # R : rest
            messages = self.player.rest()
        elif keypress.keychar == 's':
            # s : search adjacent squares
            messages = self.player.search(self.current_map)

        # Game control
        elif keypress.key == 'ENTER' and keypress.alt:
            tick = False
            tdl.set_fullscreen(True)
        elif keypress.keychar == 'q' and keypress.shift:
            tick = False
            should_exit = self.menu_selection(
                'Really quit?', 20, 10, ['yes', 'no'], ['y', 'n'])
            if should_exit == 0:
                # TODO: implement run saving
                self.root.clear()
                return compute_fov_agro, True, tick

        for message in messages:
            self.add_message(message)

        return compute_fov_agro, False, tick

    def add_message(self, message):
        '''Add a new message to the message buffer'''
        new_message_lines = textwrap.wrap(message.text, self.message_width)

        for line in new_message_lines:
            # Overflow the messages to make space if needed
            if len(self.messages) == self.panel_height - 2:
                self.messages.pop(0)
            self.messages.append((line, message.colour))

    def msgbox(self, text, width=50, height=50):
        '''Display a message'''
        text = textwrap.wrap(text, width)
        window = tdl.Console(width, height)
        window.draw_rect(0, 0, width, height, None, fg=LIGHT0, bg=DARK0)
        for i, line in enumerate(text):
            window.draw_str(0, 0+i, text[i], bg=None)

        x = self.width // 2 - width // 2
        y = self.height // 2 - height // 2
        self.root.blit(window, x, y, width, height, 0, 0)
        tdl.flush()
        tdl.event.key_wait()

    def menu_selection(self, title, width, height, options, keys=None,
                       bg=DARK0, ascii_art=False):
        '''Render a menu and return a selected index from options'''
        def chunked(l):
            return [l[i:i+26] for i in range(0, len(l), 26)]

        # Keep here for quicker debugging in dynamic use
        if keys is not None and len(keys) != len(options):
            raise IndexError('incorrect number of keys given for options')

        if not ascii_art:
            title = textwrap.wrap('.: ' + title + ' :.', width)
        else:
            title = title.split('\n')
        chunked_options = chunked(options)

        window = tdl.Console(width, height)
        if bg is not None:
            window.draw_rect(0, 0, width, height, None, fg=LIGHT0, bg=bg)
        for i, line in enumerate(title):
            window.draw_str(0, 0+i, title[i], bg=None)

        block_index = 0

        while True:
            y = len(title) + 1
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
    def __init__(self,  width, height, bar_width, bg=DIM_FG1):
        self.width = width
        self.height = height
        self.bar_width = bar_width
        self.msg_x = bar_width + 2
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
        if max_val > 0:
            bar_len = int(val / max_val * self.bar_width)
        else:
            bar_len = 0
        text = '{}:{}/{}'.format(name, str(val), str(max_val))
        text_x = x + (self.bar_width - len(text)) // 2

        self.panel.draw_rect(x, y, self.bar_width, 1, None, bg=bg)

        if bar_len > 0:
            self.panel.draw_rect(x, y, bar_len, 1, None, bg=fg)

        self.panel.draw_str(text_x, y, text, fg=LIGHT0, bg=None)

    def render_stats(self, player):
        title = '.: {} :.'.format(player.name)
        text_x = 1 + (self.bar_width - len(title)) // 2
        self.panel.draw_str(text_x, 1, title, bg=DIM_FG2, fg=LIGHT0)
        self.render_bar(
            1, 2, 'HP', player.HP, player.MAX_HP, BRIGHT_RED, FADED_RED)
        self.render_bar(
            1, 3, 'SP', player.SP, player.MAX_SP, BRIGHT_AQUA, FADED_AQUA)
        self.render_bar(
            1, 4, 'XP', player.current_xp, player.next_level, LIGHT4, DIM_FG1)

    def render_messages(self, messages):
        '''Display the current messages'''
        y = 1
        for line, colour in messages:
            self.panel.draw_str(self.msg_x, y, line, bg=None, fg=colour)
            y += 1
