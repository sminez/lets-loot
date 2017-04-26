import time
from guildmaster.dungeon.mapgen import Dungeon
from guildmaster.dungeon.pathfinding import PathFinder


def conv(l):
    return [chr(97 + r.id) for r in l]


d = Dungeon(40, 80, new_alg=True)
p = PathFinder(d.maps[0])
rooms = d.maps[0].rooms

start = time.time()
path = p.a_star(rooms[0].center, rooms[-1].center)
print(time.time() - start)
print(len(path))

for row in d.maps[0].lmap:
    for tile in row:
        if tile.room_id != -62:
            tile.room_id = -65  # ' '
        elif tile.char == '.' and tile.room_id == -62:
            tile.room_id = -65  # ' '
        elif tile.char == '+':
            tile.room_id = -54  # '+'

# Mark the paths
for x, y in path:
    d.maps[0].lmap[y][x].room_id = -51

for row in d.maps[0].lmap:
    print(''.join([chr(97 + t.room_id) for t in row]))
