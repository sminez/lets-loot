'''
Pathfinding on a map.
'''
import heapq


class PathFinder:
    def __init__(self, map):
        '''A pathfinder works from a dungeon of floors'''
        self.map = map

    @staticmethod
    def build_path(came_from, start, target):
        '''Rebuild the path from the search'''
        current = target
        path = [current]

        while current is not start:
            current = came_from[current]
            path.append(current)

        path.reverse()
        return path

    def a_star(self, start, target):
        '''A* search on tiles'''
        # Avoid repeated tuple index lookups while we iterate
        sx, sy = start
        tx, ty = target
        X, Y = (sx - tx), (sy - ty)

        def heuristic(tile):
            # see here for more on heuristics
            # http://theory.stanford.edu/~amitp/GameProgramming/index.html
            x, y = (tile[0] - tx), (tile[1] - ty)
            heuristic = abs(tx - tile[0]) + abs(ty - tile[1])
            cross = abs(x*Y - X*y)  # compute the vector cross product
            return heuristic + (cross * 0.001)

        open_set = []
        heapq.heappush(open_set, (0, start))

        came_from = {start: None}
        cost_so_far = {start: 0}

        while len(open_set) > 0:
            current = heapq.heappop(open_set)[1]

            if current == target:
                break

            x, y = current

            # NOTE: True here is a flag to return the coordinates as well
            #       as the Tile objects themselves
            for coords, tile in self.map.neighbouring_tiles(x, y, True):
                if tile.path_cost is not None:  # None -> can't get through
                    cost = cost_so_far[current] + tile.path_cost
                    if (x - coords[0] != 0) and (y - coords[1] != 0):
                        # Penalise diagonal movement to avoid crazy paths
                        cost += 1

                    if coords not in cost_so_far or cost < cost_so_far[coords]:
                        cost_so_far[coords] = cost
                        visit_cost = cost + heuristic(coords)
                        heapq.heappush(open_set, (visit_cost, coords))
                        came_from[coords] = current

        return self.build_path(came_from, start, target)

    def has_los(self, map_id, start, target):
        '''Check for straight line LOS using Bresenham's algorithm'''
        dx = target[0] - start[0]
        dy = target[1] - start[1]

        if dx == 0:
            # Simple case for vertical lines
            y1, y2 = min(start[1], target[1]), max(start[1], target[1])
            for tile in self.map.lmap[y1:y2+1][start[0]]:
                if tile.block_sight:
                    return False
            return True
        else:
            derr = abs(dy/dx)
            error = derr - 0.5
            y = start[1]
            for x in range(start[0], target[0]+1):
                if tile.block_sight:
                    return False

                error += derr

                if error >= 0.5:
                    y += 1
                    error -= 1
        return True

    def agro_heatmap(self, player, additional_coords=[]):
        '''
        Player agro is modelled as a Dijkstra heatmap that both follows the
        player and any other points where they have made sound/been seen.

        Coordinates can be returned from actions in the form:
            ((x, y), weight)

        The assignment of weights is based on the following:
            0:   normal creature moving around
            > 0: quieter than normal footsteps
            < 0: louder than normal footsteps

        Each enemy has an agro range that gives the highest weight that they
        can be drawn from: higher agro_range == quicker to follow the
        player.
        In addition, if an enemy gains LineOfSight to the player, they will
        follow that LOS as closely as possible if the player is within their
        vision distance.

        NOTE: It is not always the case that vision_distance > agro_range
        '''
        x, y = player.x, player.y
        open_set = []
        heapq.heappush(open_set, (0, (x, y)))
        cost_so_far = {(x, y): 0}

        for point, weight in additional_coords:
            heapq.heappush(open_set, (weight, point))
            cost_so_far = {point: weight}

        while len(open_set) > 0:
            current = heapq.heappop(open_set)[1]
            x, y = current

            # NOTE: True here is a flag to return the coordinates as well
            #       as the Tile objects themselves
            for coords, tile in self.map.neighbouring_tiles(x, y, True):
                cost = cost_so_far[current] + tile.agro_cost

                if coords not in cost_so_far or cost < cost_so_far[coords]:
                    cost_so_far[coords] = cost
                    heapq.heappush(open_set, (cost, coords))

        # Bind the new agro weights to the tiles (creatures check with the map)
        for coords in cost_so_far:
            x, y = coords
            self.map.lmap[y][x].agro_weight = cost_so_far[coords]
