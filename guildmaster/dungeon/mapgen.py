'''
Map creation algorithms
'''
from random import randint
from ..utils import GameObject
from ..config import MIN_ROOM_SIZE, MAX_ROOM_SIZE, MAX_ROOMS
from ..config import ROCK, FLOOR, OPEN_DOOR, CLOSED_DOOR, UP, DOWN


class Room(GameObject):
    def __init__(self, x, y, width, height):
        # NOTE: (x1,y1) == top left corner and (x2,y2) == bottom right
        self.x1 = x
        self.y1 = y
        self.x2 = x + width
        self.y2 = y + height

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

    def random_point(self):
        '''Return a random point inside the room'''
        x = randint(self.x1+1, self.x2-1)
        y = randint(self.y1+1, self.y2-1)
        return (x, y)


class Dungeon:
    '''Control class for a map and its contents'''
    def __init__(self, height=40, width=60):
        self.height = height
        self.width = width
        self.max_rooms = MAX_ROOMS
        self.max_room_size = MAX_ROOM_SIZE
        self.min_room_size = MIN_ROOM_SIZE

        self.maps = []
        self.generate()  # Appends a new map to self.maps

    def __getitem__(self, ix):
        return self.maps[ix]

    def generate(self):
        '''Generate a new map'''
        new_map = Map(self.width, self.height)

        # Add the rooms
        for rm in range(self.max_rooms):
            rwidth = randint(self.min_room_size, self.max_room_size)
            rheight = randint(self.min_room_size, self.max_room_size)
            x = randint(0, self.width - rwidth - 1)
            y = randint(0, self.height - rheight - 1)

            new_room = Room(x, y, rwidth, rheight)
            for room in new_map.rooms:
                if new_room.overlaps_with(room):
                    break
            else:
                new_map.add_room(new_room)

        # Connect the rooms and add some noise
        new_map.connect()
        new_map.add_dead_ends()

        # Populate with features
        new_map.add_features()

        # Add the map to the dungeon
        self.maps.append(new_map)


class Map:
    '''Map for a floor in the dungeon'''
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.lmap = [[ROCK() for x in range(width)] for y in range(height)]
        self.rooms = []
        self.centers = {}
        self.starting_x = 0
        self.starting_y = 0

    def add_room(self, room):
        '''Add a new, non-overlapping room to the map'''
        for x in range(room.x1+1, room.x2):
            for y in range(room.y1+1, room.y2):
                self.lmap[y][x] = FLOOR()

        if len(self.rooms) == 0:
            # First room is the entry point
            self.starting_x, self.starting_y = room.random_point()
            self.lmap[self.starting_y][self.starting_x] = UP()
        else:
            pass

        self.rooms.append(room)

    def h_corridor(self, x1, x2, y):
        '''Draw a corridor from x1 to x2 and y'''
        for x in range(min(x1, x2), max(x1, x2)+1):
            self.lmap[y][x] = FLOOR()

    def v_corridor(self, y1, y2, x):
        '''Draw a corridor from y1 to y2 at x'''
        for y in range(min(y1, y2), max(y1, y2)+1):
            self.lmap[y][x] = FLOOR()

    def connect(self):
        '''Ensure that all rooms can be reached'''
        for ix, room in enumerate(self.rooms):
            neighbour = self.rooms[ix-1]

            # Check the relative positions of the two rooms
            horizontal = room.horizontal_with(neighbour)
            # Take a random point from each room to work with
            x1, y1 = room.random_point()
            x2, y2 = neighbour.random_point()

            # Connect the rooms
            if horizontal:
                xdiv = randint(min(x1, x2), max(x1, x2))
                self.h_corridor(x1, xdiv, y1)
                self.h_corridor(x2, xdiv, y2)
                self.v_corridor(y1, y2, xdiv)
            else:
                ydiv = randint(min(y1, y2), max(y1, y2))
                self.v_corridor(y1, ydiv, x1)
                self.v_corridor(y2, ydiv, x2)
                self.h_corridor(x1, x2, ydiv)

    def add_dead_ends(self):
        pass

    def add_features(self):
        pass
