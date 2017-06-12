from random import shuffle, randrange


class Maze:
    '''A simple maze generator'''
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def set_dims(self, w, h):
        self.width = w
        self.height = h

    def generate(self):
        '''Generate the maze'''
        # TODO :: Move from walls + 2x2 cells to my single cell representation
        self.visited = [[0] * self.width + [1] for _ in range(self.height)]
        self.visited += [[1] * (self.width + 1)]
        self.ver = [["|  "] * self.width + ['|'] for _ in range(self.height)] + [[]]
        self.hor = [["+--"] * self.width + ['+'] for _ in range(self.height + 1)]

        self.walk(randrange(self.width), randrange(self.height))

        s = ""
        for (h, v) in zip(self.hor, self.ver):
            s += ''.join(h + ['\n'] + v + ['\n'])
        return s

    def walk(self, x, y):
        '''Take a step through the map and mark the maze'''
        self.visited[y][x] = 1

        directions = [(x - 1, y), (x, y + 1), (x + 1, y), (x, y - 1)]
        shuffle(directions)

        for (X, Y) in directions:
            if not self.visited[Y][X]:
                if X == x:
                    self.hor[max(y, Y)][x] = "+  "
                if Y == y:
                    self.ver[y][max(x, X)] = "   "
                self.walk(X, Y)
