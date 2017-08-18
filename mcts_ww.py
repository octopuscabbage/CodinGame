import sys
import math
import copy
import time
import datetime
from random import choice
import pprint

ME = 1
ENEMY = 2
NEUTRAL = None


def current_time():
    return datetime.datetime.utcnow()


def fmap_2dmatrix(f, x):
    for i, l in enumerate(x):
        for i, c in enumerate(l):
            l[i] = f(c)
        x[i] = l
    return x

def freeze_board(x):
    def __():
        new_x = []
        for row in x:
            new_x.append(tuple(row))
        new_x = tuple(new_x)
        return new_x
    return add_timing("Freeze Board",__)


def thaw_board(x):
    def __():
        new_x = []
        for row in x:
            new_x.append(list(row))
        return new_x
    return add_timing("Thaw Board", __)

def freeze_state(s):
    def __():
        board, my_units, enemy_units, player = s
        return (freeze_board(board), tuple(my_units), tuple(enemy_units), player)
    return add_timing("Freeze state", __)


def thaw_state(s):
    def __():
        board, my_units, enemy_units, player = s
        return (thaw_board(board), list(my_units), list(enemy_units), player)
    return add_timing("Thaw State", __)

MOVE_ADDITIONALS = [((-1, -1), "NW"), ((0, -1), "N"), ((-1, 1), "NE"),
                    ((-1, 0), "W"), ((1, 0), "E"),
                    ((-1, 1), "SW"), ((0, 1), "S"), ((+1, +1), "SE")]

BOARD = 0
MY_UNITS = 1
ENEMY_UNITS = 2
CURRENT_PLAYER = 3


def print_d(msg):
    print(msg, file=sys.stderr)


def pprint_d(msg):
    pprint.pprint(msg, stream=sys.stderr)


timing_map = {}
def add_timing(operation_name, f):
    begin = current_time()
    out = f()
    elapsed = current_time() - begin
    if not operation_name in timing_map:
       timing_map[operation_name] = (elapsed,1)
    else:
        current_elapsed, current_recorded = timing_map[operation_name]
        timing_map[operation_name] = (current_elapsed + elapsed, current_recorded + 1)
    return out

def print_timings():
    for key,value in sorted(timing_map.items()):
        total_elapsed, total_runnings = value
        avg = total_elapsed / total_runnings
        print_d(key + " AVG: " + str(avg) + " # Run " + str(total_runnings))

class AIBoard(object):
    def __init__(self, board, my_units, enemy_units):
        # Board is a size x size where each cell is height (height -1 is impassible)
        self.initial_state = (board, my_units, enemy_units, ME)

    def get_start(self):
        # Returns a representation of the starting state of the game.
        # state is (board, current_player) where current_player is  who is playing right now 1 (me) 2 (enemy)
        # board is a 3d array size x size where each cell is (height, current player) where height is 0 1 2 3 or -1 if impassible and current player is 1 (me) 2 (enemy) or None (neutral)
        board = copy.deepcopy(self.initial_state[BOARD])
        my_units = self.initial_state[MY_UNITS][:]
        enemy_units = self.initial_state[ENEMY_UNITS][:]
        player = ME
        return (board, my_units, enemy_units, player)

    def current_player(self, state):
        # Takes the game state and returns the current player's number.
        return state[CURRENT_PLAYER]

    def next_state(self, state, play):
        def __():
            # Takes the game state, and the move to be applied.
            # Returns the new game state.
            unit_number = play[0]
            move = play[1][0]
            if state[CURRENT_PLAYER] == ME:
                enemy_units = state[ENEMY_UNITS]
                my_units = list(state[MY_UNITS])[:]
                my_units[unit_number] = move
                next_player = ENEMY
            else:
                my_units = state[MY_UNITS]
                enemy_units = list(state[ENEMY_UNITS])[:]
                enemy_units[unit_number] = move
                next_player = ME
            build_x, build_y = play[2][0]
            if not isinstance(state[BOARD], list):
                new_board = thaw_board(state[BOARD])
            else:
                new_board = state[BOARD]
            new_board[build_x][build_y] += 1

            return (new_board, my_units, enemy_units, next_player)
        return add_timing("AIBoard.next_state", __)

    def legal_plays(self, state_history):
        def __():
            # Takes a sequence of game states representing the full
            # game history, and returns the full list of moves that
            # are legal plays for the current player.
            state = state_history[-1]
            if state[CURRENT_PLAYER] == ME:
                current_units = state[MY_UNITS]
            else:
                current_units = state[ENEMY_UNITS]
            possible_moves = []
            for i, p in enumerate(current_units):
                x, y = p
                for added_point, label in MOVE_ADDITIONALS:
                    x_a, y_a = added_point
                    move_point = (x + x_a, y + y_a)
                    new_x, new_y = move_point
                    try:
                        new_cell = state[BOARD][new_x][new_y]
                    except IndexError:
                        continue
                    current_cell = state[BOARD][x][y]
                    if 0 <= new_cell < 4 and (new_cell <= current_cell or new_cell + 1 == current_cell):
                        possible_moves.append((i, (move_point, label)))
            possible_move_and_builds = []
            for i, move in possible_moves:
                move_point, move_label = move
                x, y = move_point
                for added_point, build_label in MOVE_ADDITIONALS:
                    x_a, y_a = added_point
                    build_point = (x + x_a, y + y_a)
                    try:
                        cell_at = state[BOARD][build_point[1]][build_point[0]]
                        if 0 <= cell_at < 4:
                            possible_move_and_builds.append((i, (move_point, move_label), (build_point, build_label)))
                    except IndexError:
                        # This is a dumb way to only build inside bounds
                        pass
            return possible_move_and_builds
        return add_timing("Calculate Legal Plays", __)

    def winner(self, state_history):
        def __():
            # Takes a sequence of game states representing the full
            # game history.  If the game is now won, return the player
            # number.  If the game is still ongoing, return zero.  If
            # the game is tied, return a different distinct value, e.g. -1.
            state = state_history[-1]
            for x, y in state[MY_UNITS]:
                if state[BOARD][x][y] == 3:
                    return ME
            for x, y in state[ENEMY_UNITS]:
                if state[BOARD][x][y] == 3:
                    return ENEMY
            if len(self.legal_plays(state_history)) == 0:
                return -1
            return 0
        return add_timing("Find winner", __)




class MonteCarlo(object):
    def __init__(self, board, calculation_time_ms, max_moves=100, C=1.4):
        # Initialize the list of game states and stats tables
        self.board = board
        self.states = [board.get_start()]
        self.calculation_time = datetime.timedelta(milliseconds=calculation_time_ms)
        self.max_moves = max_moves
        self.wins = {}
        self.plays = {}
        self.C = C

    def update(self, state):
        # Append game state to state history
        self.states.append(state)

    def get_play(self):
        plays, wins = self.plays, self.wins
        self.max_depth = 0
        state = self.states[-1]
        player = self.board.current_player(state)
        legal = self.board.legal_plays(self.states[:])
        if not legal:
            print_d("No Legal Moves...")
            return
        if len(legal) == 1:
            print_d("Only 1 legal move")
            return legal[0]

        games = 0
        begin = current_time()
        remaining = current_time() - begin
        while remaining < self.calculation_time:
            self.run_sim()
            games = games + 1
            remaining = current_time() - begin
        moves_states = map(lambda p: (p, freeze_state(self.board.next_state(state, p))), legal)
        print_d("Games: " + str(games) + ", Sim Time: " + str(current_time() - begin))
        percent_wins, move = max(
            (self.wins.get((player, S), 0) / self.plays.get((player, S), 1), p) for p, S in moves_states)
        print_d("Using move " + str(move) + " because it has a " + str(percent_wins) + "% of winning.")
        return move

    def run_sim(self):
        def __():
            # Play out random game from current position, update stats table w result
            plays, wins = self.plays, self.wins

            visited_states = set()
            states_copy = self.states[:]
            state = states_copy[-1]
            player = self.board.current_player(state)

            expand = True
            for t in range(1, self.max_moves + 1):
                legal = self.board.legal_plays(states_copy)
                moves_states = [(p, freeze_state(self.board.next_state(state, p))) for p in legal]
                # pprint_d(moves_states)
                if all(plays.get((player, S)) for p, S in moves_states):
                    # If we have stats on all of the legal moves here, use them.
                    log_total = math.log(sum(plays[(player, S)] for p, S in moves_states))

                    value, move, state = max(
                        ((wins[(player, S)] / plays[(player, S)]) +
                         self.C * math.sqrt(log_total / plays[(player, S)]), p, S)
                        for p, S in moves_states
                    )
                else:
                    # Otherwise, just make an arbitrary decision.
                    move, state = choice(moves_states)

                states_copy.append(state)

                # `player` here and below refers to the player
                # who moved into that particular state.
                if expand and (player, state) not in plays:
                    expand = False
                    plays[(player, state)] = 0
                    wins[(player, state)] = 0
                    if t > self.max_depth:
                        self.max_depth = t

                visited_states.add((player, state))

                player = self.board.current_player(state)
                winner = self.board.winner(states_copy)
                if winner:
                    break

            for player, state in visited_states:
                if (player, state) not in plays:
                    continue
                plays[(player, state)] += 1
                if player == winner:
                    wins[(player, state)] += 1
        return add_timing("Run sim", __)


# Auto-generated code below aims at helping you parse


# the standard input according to the problem statement.
"""
size = int(input())
units_per_player = int(input())
i = 0
# game loop
while True:
    raw_board = [None for i in range(size)]
    for i in range(size):
        raw_row = input()
        row = []
        for c in raw_row:
            if c == ".":
                row.append(-1)
            else:
                row.append(int(c))
        raw_board[i] = row
    my_units = []
    for i in range(units_per_player):
        unit_x, unit_y = [int(j) for j in input().split()]
        my_units.append((unit_x, unit_y))
    enemy_units = []
    for i in range(units_per_player):
        other_x, other_y = [int(j) for j in input().split()]
        enemy_units.append((other_x, other_y))
    legal_actions = int(input())
    for i in range(legal_actions):
        atype, index, dir_1, dir_2 = input().split()
        index = int(index)
    if i == 0:
        timeout = 1000
    else:
        timeout = 20
    board = AIBoard(raw_board, my_units, enemy_units)
    brain = MonteCarlo(board, calculation_time_ms=timeout)
    play = brain.get_play()
    # Write an action using print
    # To debug: print("Debug messages...", file=sys.stderr)
    i += 1
    print("MOVE&BUILD 0 " + play[1][1] + " " + play[2][1])
"""
raw_board = [[0,0,0,0],
         [0,0,0,0],
         [0,0,0,0],
         [0,0,0,0]]
my_units = [(0,0)]
enemy_units = [(3,3)]
board = AIBoard(raw_board, my_units, enemy_units)
brain = MonteCarlo(board, calculation_time_ms=20)
play = brain.get_play()
print_timings()
print(play)
