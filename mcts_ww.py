import sys
import math
import datetime
import random
import pprint

DEBUG = True

ME = 1
ENEMY = 2
NEUTRAL = None

CUBE_HASH = {-1: -3, 0: 0, 1: 3, 2: 8, 3: 27, 4: -3, 5: -3}


def current_time():
    return datetime.datetime.utcnow()


def fmap_2dmatrix(f, x):
    for i, l in enumerate(x):
        for j, c in enumerate(l):
            l[j] = f(c)
        x[i] = l
    return x


def freeze_board_(x):
    def __():
        new_x = []
        for row in x:
            new_x.append(tuple(row))
        new_x = tuple(new_x)
        return new_x

    return add_timing("Freeze Board", __)


def thaw_board_(x):
    def __():
        new_x = []
        for row in x:
            new_x.append(list(row))
        return new_x

    return add_timing("Thaw Board", __)


'''
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
'''


def write_to_2d_tuple(t, i, j, v):
    def __():
        l_board = list(t)
        l_row = list(t[j])
        l_row[i] = v
        l_board[j] = tuple(l_row)
        l_board = tuple(l_board)
        return l_board

    return add_timing("Write to 2d tuple", __)


def weighted_choice(choices):
    def __():
        total = sum(w for w, c in choices)
        r = random.uniform(0, total)
        upto = 0
        for w, c in choices:
            if upto + w >= r:
                return c
            upto += w

    return add_timing("Weighted Choice", __)


MOVE_ADDITIONALS = [((-1, -1), "NW"), ((0, -1), "N"), ((1, - 1), "NE"),
                    ((-1, 0), "W"), ((1, 0), "E"),
                    ((-1, 1), "SW"), ((0, 1), "S"), ((+1, +1), "SE")]

BOARD = 0
MY_UNITS = 1
ENEMY_UNITS = 2
CURRENT_PLAYER = 3


def print_d(msg):
    if DEBUG:
        print(msg, file=sys.stderr)


def pprint_d(msg):
    if DEBUG:
        pprint.pprint(msg, stream=sys.stderr)


def print_d_important(msg):
    print(msg, file=sys.stderr)


timing_map = {}


def add_timing(operation_name, f, *args):
    if not DEBUG:
        return f(*args)
    else:
        begin = current_time()
        out = f(*args)
        elapsed = current_time() - begin
        if not operation_name in timing_map:
            timing_map[operation_name] = (elapsed, 1)
        else:
            current_elapsed, current_recorded = timing_map[operation_name]
            timing_map[operation_name] = (current_elapsed + elapsed, current_recorded + 1)
        return out


def print_timings():
    print_d("%-20.20s %-14s %-14s %s" % ("NAME", "TOTAL", "AVG RUNTIME", "TOTAL RUNs"))
    for key, value in sorted(timing_map.items()):
        total_elapsed, total_runnings = value
        avg = total_elapsed / total_runnings
        print_d("%-20.20s %-14s %-14s %-5i" % (key, str(total_elapsed), str(avg), total_runnings))


def inside_2d_square(l, i, j):
    size = len(l)
    return 0 <= i < size and 0 <= j < size


class AIBoard(object):
    def __init__(self):
        self.next_state_hashtable = {}
        self.next_legal_hashtable = {}
        self.winner_hashtable = {}
        self.legal_plays_fo_cache = {}

    def on_update(self, board, my_units, enemy_units):
        # Board is a size x size where each cell is height (height -1 is impassible)
        # Called on each iter of the while loop
        self.initial_state = (freeze_board_(board), tuple(my_units), tuple(enemy_units), ME)

    def get_start(self):
        # Returns a representation of the starting state of the game.
        # state is (board, current_player) where current_player is  who is playing right now 1 (me) 2 (enemy)
        # board is a 3d array size x size where each cell is (height, current player) where height is 0 1 2 3 or -1 if impassible and current player is 1 (me) 2 (enemy) or None (neutral)
        return self.initial_state

    def current_player(self, state):
        # Takes the game state and returns the current player's number.
        return state[CURRENT_PLAYER]

    def next_state(self, state, play):
        if (state, play) in self.next_state_hashtable:
            add_timing("Next State $", lambda: 1)
            return self.next_state_hashtable[state, play]

        def __():
            # Takes the game state, and the move to be applied.
            # Returns the new game state.
            unit_number = play[0]
            move = play[1][0]
            if state[CURRENT_PLAYER] == ME:
                enemy_units = state[ENEMY_UNITS]
                my_units = list(state[MY_UNITS])
                my_units[unit_number] = move
                my_units = tuple(my_units)
                next_player = ENEMY
            else:
                my_units = state[MY_UNITS]
                enemy_units = list(state[ENEMY_UNITS])
                enemy_units[unit_number] = move
                enemy_units = tuple(enemy_units)
                next_player = ME
            build_x, build_y = play[2][0]

            new_board = write_to_2d_tuple(state[BOARD], build_x, build_y, state[BOARD][build_x][build_y] + 1)

            next_state = (new_board, my_units, enemy_units, next_player)
            if next_player == ENEMY and not self.team_has_legal_plays([next_state]):
                next_state = (new_board, my_units, enemy_units, ME)
            return next_state

        out = add_timing("Next State", __)
        self.next_state_hashtable[(state, play)] = out
        return out

    def team_has_legal_plays(self, state_history):
        if state_history[-1] in self.legal_plays_fo_cache:
            return add_timing("Legal Play? $", lambda: self.legal_plays_fo_cache[state_history[-1]])

        def __():
            state = state_history[-1]

            if state[CURRENT_PLAYER] == ME:
                units = state[MY_UNITS]
            else:
                units = state[ENEMY_UNITS]
            for x, y in units:
                for move, label in MOVE_ADDITIONALS:
                    x_a, y_a = move
                    new_x, new_y = (x + x_a, y + y_a)
                    if inside_2d_square(state[BOARD], new_x, new_y) and 0 <= state[BOARD][new_y][new_x] < 4:
                        return True
            return False

        out = add_timing("Legal Play?", __)
        self.legal_plays_fo_cache[state_history[-1]] = out
        return out

    def legal_plays(self, state_history):

        if state_history[-1] in self.next_legal_hashtable:
            return add_timing("Legal Plays $", lambda: self.next_legal_hashtable[state_history[-1]])

        def __(self):
            # Takes a sequence of game states representing the full
            # game history, and returns the full list of moves that
            # are legal plays for the current player.
            state = state_history[-1]
            if state[CURRENT_PLAYER] == ME:
                current_units = state[MY_UNITS]
            else:
                current_units = state[ENEMY_UNITS]

            possible_moves_and_builds = []
            board = state[BOARD]
            for i, p in enumerate(current_units):
                x, y = p
                other_units = set(state[MY_UNITS] + state[ENEMY_UNITS]).difference({p})

                for added_point, move_label in MOVE_ADDITIONALS:
                    x_a, y_a = added_point
                    move_point = (x + x_a, y + y_a)
                    new_x, new_y = move_point
                    if inside_2d_square(board, new_x, new_y):
                        new_cell = board[new_y][new_x]
                        current_cell = board[y][x]
                        if 0 <= new_cell < 4 and new_cell <= current_cell + 1 and move_point not in other_units:
                            # Look up builds
                            for build_added_point, build_label in MOVE_ADDITIONALS:
                                x_a, y_a = build_added_point
                                build_point = (new_x + x_a, new_y + y_a)
                                build_x, build_y = build_point
                                if inside_2d_square(board, build_x, build_y) and build_point not in other_units:
                                    cell_at = board[build_y][build_x]
                                    if 0 <= cell_at < 4:
                                        possible_moves_and_builds.append(
                                            (i, (move_point, move_label), (build_point, build_label)))
            return possible_moves_and_builds

        out = add_timing("Legal Plays", __, self)
        self.next_legal_hashtable[state_history[-1]] = out
        return out

    def winner(self, state_history):
        if state_history[-1] in self.winner_hashtable:
            add_timing("Find Winner $", lambda: 1)
            return self.winner_hashtable[state_history[-1]]

        def __():
            # Takes a sequence of game states representing the full
            # game history.  If the game is now won, return the player
            # number.  If the game is still ongoing, return zero.  If
            # the game is tied, return a different distinct value, e.g. -1.
            state = state_history[-1]
            board = state[BOARD]
            for x, y in state[MY_UNITS]:
                if board[y][x] == 3:
                    return ME
            for x, y in state[ENEMY_UNITS]:
                if board[y][x] == 3:
                    return ENEMY
            if not self.team_has_legal_plays(state_history):  # Idiom for empty
                return -1
            return 0

        out = add_timing("Find winner", __)
        self.winner_hashtable[state_history[-1]] = out
        return out


class MonteCarlo(object):
    def __init__(self):

        self.wins = {}
        self.plays = {}

    def on_update(self, board, calculation_time_ms=40, max_moves=50, C=1.4):
        # Called on each iteration of the while loop
        # Initialize the list of game states and stats tables
        self.board = board
        self.states = [board.get_start()]
        self.calculation_time = datetime.timedelta(milliseconds=calculation_time_ms)
        self.max_moves = max_moves
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
            games += 1
            remaining = current_time() - begin

        moves_states = [(p, self.board.next_state(state, p)) for p in legal]
        print_d_important("Games: " + str(games) + ", Sim Time: " + str(current_time() - begin))
        percent_wins, move = max(
            (wins.get((player, S), 0) / plays.get((player, S), 1), p) for p, S in moves_states)
        # Display the stats for each possible play.
        '''
        if DEBUG:
            for x in sorted(
                    ((100 * self.wins.get((player, S), 0) /
                          self.plays.get((player, S), 1),
                      self.wins.get((player, S), 0),
                      self.plays.get((player, S), 0), p)
                     for p, S in moves_states),
                    reverse=True
            ): print_d("{3}: {0:.2f}% ({1} / {2})".format(*x))
    '''
        print_d("Maximum depth searched: %i" % (self.max_depth))
        print_d("Using move %s because it has a %f of winning." % (move, percent_wins))
        return move

    def run_sim(self):
        def __():
            total_points = 0
            # Play out random game from current position, update stats table w result
            plays, wins = self.plays, self.wins

            visited_states = set()
            states_copy = self.states[:]
            state = states_copy[-1]
            player = self.board.current_player(state)

            expand = True
            for t in range(1, self.max_moves + 1):
                legal = self.board.legal_plays(states_copy)
                if len(legal) == 0:
                    break
                moves_states = [(p, self.board.next_state(state, p)) for p in legal]
                # pprint_d(moves_states)
                if all(plays.get((player, S)) for p, S in moves_states):
                    # If we have stats on all of the legal moves here, use them.
                    log_total = math.log(sum(plays[(player, S)] for p, S in moves_states))

                    value, move, state = max(
                        (-1 if wins[(player, S)] < 0 else 1 * (wins[(player, S)] / plays[(player, S)]) +
                                                          self.C * math.sqrt(log_total / plays[(player, S)]), p, S)
                        for p, S in moves_states
                    )
                else:
                    # Otherwise, just make an arbitrary decision.
                    weighed_choices = []
                    for move, state in moves_states:
                        outcome = board.next_state(state, move)
                        if outcome[CURRENT_PLAYER] == ME:
                            units = outcome[MY_UNITS]
                        else:
                            units = outcome[ENEMY_UNITS]
                        weight_sum = 0
                        for x, y in units:
                            '''
                            for move_additional, _ in MOVE_ADDITIONALS:
                                x_a,y_a = move_additional
                                new_x, new_y = (x + x_a, y + y_a)
                                if inside_2d_square(outcome[BOARD],new_x,new_y):
                                    #TODO Use hash table instead of every single mult
                                    weight_sum += CUBE_HASH[outcome[BOARD][new_y][new_x]]
                            '''
                            weight_sum += CUBE_HASH[outcome[BOARD][y][x]]
                        weighed_choices.append((weight_sum, (move, state)))

                    move, state = weighted_choice(weighed_choices)

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
                if winner == ME:
                    total_points += 1

                if winner == ENEMY:
                    total_points -= 1
                '''
                if winner == -1 and player == ME:
                    total_points -= 10

                if winner == -1 and player == ENEMY:
                    total_points += 10
                 '''

            for player, state in visited_states:
                if (player, state) not in plays:
                    continue
                plays[(player, state)] += 1
                wins[(player, state)] += total_points

        return add_timing("Run sim", __)

'''
# Auto-generated code below aims at helping you parse

# the standard input according to the problem statement.
size = int(input())
units_per_player = int(input())
turn = 0
board = AIBoard()
brain = MonteCarlo()
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
        timeout = 40

    if turn < 10:
        c = 100
        max_moves = 5
    elif i > 20:
        max_moves = 3
        c = 10
    else:
        c = 10
        max_moves = 3
    print_d("Moves %i C %f Turn # %i" % (max_moves, c, turn))
    board.on_update(raw_board, my_units, enemy_units)

    brain.on_update(board, calculation_time_ms=timeout, C=c, max_moves=max_moves)
    play = brain.get_play()

    # Write an action using print
    # To debug: print("Debug messages...", file=sys.stderr)
    turn += 1
    print("MOVE&BUILD " + str(play[0]) + " " + play[1][1] + " " + play[2][1])
    print_timings()
    timings = {}
    '''
raw_board = [[0, 3, 4, 0],
             [0, 4, 4, 0],
             [0, 0, 0, 0],
             [0, 0, 0, 0]]
my_units = [(1, 0)]
enemy_units = [(3, 3)]
board = AIBoard()
board.on_update(raw_board, my_units, enemy_units)
brain = MonteCarlo()
brain.on_update(board, calculation_time_ms=1000)
play = brain.get_play()
new_state = board.next_state(board.get_start(), play)
print_timings()
'''
while(not board.winner([new_state])):
    new_state = board.next_state(board.get_start(), play)
    board = AIBoard(new_state[BOARD], new_state[MY_UNITS], new_state[ENEMY_UNITS])
    brain = MonteCarlo(board, calculation_time_ms=1000)
    play = brain.get_play()
    pprint_d(new_state[BOARD])
    print_timings()
    timing_map = {}
    '''
print(play)
