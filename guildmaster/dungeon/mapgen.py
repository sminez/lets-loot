'''
Map creation algorithms

http://www.gridsagegames.com/blog/2014/06/procedural-map-generation/
http://dungeonmaker.sourceforge.net/DM2_Manual/manual1.html
http://www.futuredatalab.com/proceduraldungeon/
https://eskerda.com/bsp-dungeon-generation/
'''
import tdl
import math
from random import choice, randint

from ..creatures import enemy
from .pathfinding import PathFinder
from ..utils import GameObject, Message, key_to_coords, roll
from ..config import DARK0, DARK1, DARK4, WHITE, FADED_BROWN
from ..config import MIN_ROOM_SIZE, MAX_ROOM_SIZE, MAX_ROOMS, LIGHT1


class Tile:
    '''A tile in the dungeon map'''
    def __init__(self, name, room_id=-62):
        # NOTE: room_id=-62 sets char to '#' on the path_preview script
        self.explored = False
        self.path_cost = None
        self.agro_cost = 1
        self.agro_weight = None
        self.room_id = room_id
        # Initialise the tile settings
        getattr(self, name)()

    def __lt__(self, other):
        return self.path_cost <= other.path_cost

    def wall(self):
        self.name = 'wall'
        self.char = '#'
        self.fg, self.bg = DARK4, DARK1
        self.block_move, self.block_sight = True, True
        self.agro_cost = 4

    def floor(self):
        self.name = 'floor'
        self.char = '.'
        self.fg, self.bg = DARK4, DARK0
        self.block_move, self.block_sight = False, False
        self.path_cost = 1
        self.agro_cost = 1

    def closed_door(self, allow_secret_door=False):
        if allow_secret_door and roll(100) >= 98:
            self.secret_door()
        else:
            self.name = 'closed_door'
            self.char = '+'
            self.fg, self.bg = FADED_BROWN, DARK0
            self.block_move, self.block_sight = True, True
            self.path_cost = 2
            self.agro_cost = 2

    def open_door(self):
        self.name = 'open_door'
        self.char = "'"
        self.fg, self.bg = FADED_BROWN, DARK0
        self.block_move, self.block_sight = False, False
        self.path_cost = 1
        self.agro_cost = 1

    def secret_door(self):
        self.name = 'secret_door'
        self.char = "#"
        self.fg, self.bg = DARK4, DARK1
        self.block_move, self.block_sight = True, True
        self.agro_cost = 3

    def up(self):
        self.name = 'up'
        self.char = "<"
        self.fg, self.bg = WHITE, DARK0
        self.block_move, self.block_sight = False, False
        self.path_cost = 1
        self.agro_cost = 1

    def down(self):
        self.name = 'down'
        self.char = ">"
        self.fg, self.bg = WHITE, DARK0
        self.block_move, self.block_sight = False, False
        self.path_cost = 1
        self.agro_cost = 1


class Room(GameObject):
    def __init__(self, x, y, width, height, ID=None):
        # NOTE: (x1,y1) == top left corner and (x2,y2) == bottom right
        self.x1 = x
        self.y1 = y
        self.x2 = x + width
        self.y2 = y + height
        self.id = ID

    def __lt__(self, other):
        return self.id < other.id

    @property
    def center(self):
        '''Find the rough centre of the room'''
        center_x = (self.x1 + self.x2) // 2
        center_y = (self.y1 + self.y2) // 2
        return (center_x, center_y)

    def overlaps_with(self, other):
        '''
        Check if this room overlaps with another one already in the map.
        '''
        xcond = (self.x1 <= other.x2 and self.x2 >= other.x1)
        ycond = (self.y1 <= other.y2 and self.y2 >= other.y1)
        return xcond and ycond

    def horizontal_with(self, other):
        '''
        Find out if the rooms are roughly horizontally or vertically displaced
        '''
        left = self.x2 < other.x1 and self.x2 < other.x2
        right = self.x1 > other.x1 and self.x1 > other.x2
        return left or right

    def random_point(self, offset=1):
        '''Return a random point inside the room'''
        x = randint(self.x1+offset, self.x2-offset)
        y = randint(self.y1+offset, self.y2-offset)
        return (x, y)


class Map:
    '''Map for a floor in the dungeon'''
    def __init__(self, width, height, depth, player=None):
        # NOTE: these are read from config.py
        self.max_rooms = MAX_ROOMS
        self.max_room_size = MAX_ROOM_SIZE
        self.min_room_size = MIN_ROOM_SIZE

        self.width = width
        self.height = height
        self.depth = depth + 1  # depth is the depth before adding this map
        self.lmap = [[Tile('wall') for x in range(width)]
                     for y in range(height)]
        self.rooms = []
        self.enemies = []
        self.items = []
        self.player = player
        self.graph = {}
        self.centers = {}
        self.starting_x = 0
        self.starting_y = 0

        # Add the rooms
        for rm in range(self.max_rooms):
            rwidth = randint(self.min_room_size, self.max_room_size)
            rheight = randint(self.min_room_size, self.max_room_size)
            x = randint(0, self.width - rwidth - 1)
            y = randint(0, self.height - rheight - 1)

            new_room = Room(x, y, rwidth, rheight)
            for room in self.rooms:
                if new_room.overlaps_with(room):
                    break
            else:
                self.add_room(new_room)

        # Connect the rooms and populate with features
        self.generate_graph()
        self.connect()
        self.add_doors()
        self.add_features()
        self.populate()

    @property
    def objects(self):
        return self.items + self.enemies + [self.player]

    def generate_graph(self, additional_connections=True):
        '''
        Generate a randomised connected graph via an inital spanning tree
        generated using Prim's MST algorithm.
        NOTE: each edge is stored twice: a->b, b->a for path finding
        '''
        rooms = set(self.rooms)
        G = {r: set() for r in rooms}
        so_far = {self.rooms[0]}

        # Prim's MST
        while len(so_far) < len(rooms):
            remaining = rooms.difference(so_far)
            weights = [(self.room_cost(s, r), s, r)
                       for s in so_far for r in remaining]
            # Select the two rooms that are closest to one another, one from
            # 'so_far' and one from 'remaining'
            _, existing, new = min(weights, key=lambda w: w[0])
            G[existing].add(new)
            G[new].add(existing)
            so_far.add(new)

        if additional_connections:
            for n in range(randint(5, len(rooms))):
                n1 = choice(list(rooms))
                existing = G[n1]
                existing.add(n1)
                n2 = choice(list(rooms.difference(existing)))
                G[n1].add(n2)
                G[n2].add(n1)

        self.graph = G

    @property
    def graph_edges(self):
        '''return a list of edges in the graph'''
        edges = set()
        for node, connections in self.graph.items():
            for connection in connections:
                edge = (node, connection)
                if (edge in edges) or ((edge[1], edge[0]) in edges):
                    pass
                else:
                    edges.add(edge)
        return list(edges)

    def neighbouring_rooms(self, room):
        '''Return all rooms connected to this one'''
        return self.graph[room]

    def neighbouring_tiles(self, x, y, include_coords=False,
                           include_offsets=False):
        '''return all neighbouring tiles'''
        if include_coords and include_offsets:
            raise ValueError('asking for both coords and offsets')

        offsets = [(-1, 0), (1, 0), (0, -1), (0, 1),
                   (-1, -1), (-1, 1), (1, -1), (1, 1)]

        tiles = []

        for offset in offsets:
            dx, dy = offset
            X, Y = x + dx, y + dy
            if (0 <= X < len(self.lmap[0])) and (0 <= Y < len(self.lmap)):
                tiles.append(((X, Y), offset, self.lmap[Y][X]))

        if include_coords:
            return [(t[0], t[2]) for t in tiles]
        elif include_offsets:
            return [(t[1], t[2]) for t in tiles]
        else:
            return [t[2] for t in tiles]

    def room_cost(self, r1, r2):
        '''Weight edges based on displacement of room centres'''
        x1, y1 = r1.center
        x2, y2 = r2.center
        return math.sqrt((x1 - x2)**2 + (y1 - y2)**2)

    def add_room(self, room):
        '''Add a new, non-overlapping room to the map'''
        ID = len(self.rooms)
        room.id = ID

        for x in range(room.x1+1, room.x2):
            for y in range(room.y1+1, room.y2):
                self.lmap[y][x] = Tile('floor', ID)

        if len(self.rooms) == 0:
            # First room is the entry point
            self.starting_x, self.starting_y = room.random_point()
            self.lmap[self.starting_y][self.starting_x].up()
        else:
            pass

        self.rooms.append(room)

    def corridor(self, p1, p2, const, horizontal):
        '''Draw a corridor from p1 to p2 at constant x/y'''
        start, finish = min(p1, p2), max(p1, p2)

        if horizontal:
            for x in range(start, finish+1):
                self.lmap[const][x].floor()
        else:
            for y in range(start, finish+1):
                self.lmap[y][const].floor()

    def connect(self):
        '''Ensure that all rooms can be reached'''
        for room, neighbour in self.graph_edges:
            # Check the relative positions of the two rooms
            horizontal = room.horizontal_with(neighbour)
            # Take a random point from each room to work with
            x1, y1 = room.random_point(offset=3)
            x2, y2 = neighbour.random_point(offset=3)

            # Connect the rooms
            if horizontal:
                div = randint(min(x1, x2), max(x1, x2))
                p1, p2, const1, const2 = x1, x2, y1, y2
            else:
                div = randint(min(y1, y2), max(y1, y2))
                p1, p2, const1, const2 = y1, y2, x1, x2

            # This makes sure that each corridor has a bend in it
            self.corridor(p1, div, const1, horizontal)
            self.corridor(p2, div, const2, horizontal)
            self.corridor(const1, const2, div, not horizontal)

    def add_doors(self):
        '''
        Try to add some doors to the dungeon
        '''
        def valid_cell(x, y):
            x_neighbours = [self.lmap[y][x-1].name, self.lmap[y][x+1].name]
            y_neighbours = [self.lmap[y-1][x].name, self.lmap[y+1][x].name]
            x2 = len([x for x in x_neighbours if x == 'floor'])
            y2 = len([y for y in y_neighbours if y == 'floor'])
            return (x2 == 2 and y2 == 0) or (x2 == 0 and y2 == 2)

        for room in self.rooms:
            for i, cell in enumerate(self.lmap[room.y1][room.x1:room.x2]):
                if cell.name == 'floor' and valid_cell(room.x1+i, room.y1):
                    cell.closed_door(allow_secret_door=True)

            for i, cell in enumerate(self.lmap[room.y2][room.x1:room.x2]):
                if cell.name == 'floor' and valid_cell(room.x1+i, room.y2):
                    cell.closed_door(allow_secret_door=True)

            for i, row in enumerate(self.lmap[room.y1:room.y2]):
                cell = row[room.x1]
                if cell.name == 'floor' and valid_cell(room.x1, room.y1+i):
                    cell.closed_door(allow_secret_door=True)

            for i, row in enumerate(self.lmap[room.y1:room.y2]):
                cell = row[room.x2]
                if cell.name == 'floor' and valid_cell(room.x2, room.y1+i):
                    cell.closed_door(allow_secret_door=True)

    def add_features(self):
        exit_room = choice(self.rooms)
        x, y = exit_room.random_point()
        self.lmap[y][x] = Tile('down', exit_room.id)

    def close_door(self, screen, x, y):
        '''Allow the player to close a door'''
        neighbours = self.neighbouring_tiles(x, y)
        doors = [n for n in neighbours if n.name == 'open_door']

        if len(doors) == 1:
            return doors[0]
        elif len(doors) > 1:
            screen.add_message(Message('Select a door...', LIGHT1))
            screen.panel.render_messages(screen.messages)
            tdl.flush()
            tdl.event.key_wait()
            keypress = tdl.event.key_wait()
            keys = ['UP', 'DOWN', 'LEFT', 'RIGHT']
            keychars = ['h', 'j', 'k', 'l', 'y', 'u', 'b', 'n']
            if keypress.key in keys:
                key = keypress.key
            elif keypress.keychar in keychars:
                key = keypress.keychar
            else:
                return None
            x, y = key_to_coords(key, x, y)
            tile = screen.current_map.lmap[y][x]
            if tile.name == 'open_door':
                return tile
            else:
                return None
        else:
            return None

    def populate(self):
        '''Add enemies to the floor'''
        for room in self.rooms[1:]:
            x, y = room.random_point()
            self.enemies.append(enemy('Goblin', x, y))

    def bsp(self):
        '''
        Use binary space partitioning to generate a map.
        '''
        root = Container(self.width, self.height)


class Dungeon:
    '''Control class for a map and its contents'''
    def __init__(self, height=40, width=60, player=None, new_alg=False):
        self.height = height
        self.width = width

        self.player = player

        self.maps = []
        self.pathfinder = PathFinder()
        self.new_floor(new_alg)  # Appends a new map to self.maps

    def __getitem__(self, ix):
        return self.maps[ix]

    def new_floor(self, new_alg):
        '''Generate a new map'''
        # TODO: have some additional stuff set by the current level etc
        new_map = Map(self.width, self.height, len(self.maps), self.player)
        self.maps.append(new_map)
        self.pathfinder.map = new_map


class Container:
    '''Container for splitting a map using bsp'''
    def __init__(self, width, height, ratio=0.45):
        self.width = width
        self.height = height
        self.vertical_split = choice([True, False])
        self.children = []

    def split(self):
        '''create two new containers with a minimum desired ratio'''
        if self.vertical_split:
            w1 = randint(0, self.width)
            w2 = self.width - w1
            h1 = h2 = self.height
        else:
            h1 = randint(0, self.height)
            h2 = self.height - h1
            w1 = w2 = self.width

        self.children = [Container(w1, h1), Container(w2, h2)]

    def split_children(self):
        for child in self.children:
            child.split()

    def get_rooms(self):
        if self.children == []:
            # we're at the bottom level so make the rooms
            # XXX: Need to ensure correct room dimensions
            x, y = randint(1, self.width-1), randint(1, self.height-1)
        else:
            for child in self.children:
                child.get_rooms()
