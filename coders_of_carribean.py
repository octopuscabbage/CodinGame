import sys
import math
import pprint
# Auto-generated code below aims at helping you parse
# the standard input according to the problem statement.

#Represents the number to add to a position to end in the next grid based on direction
EVEN_DIRS = {0: (1,0), 1: (0,-1), 2: (-1,-1), 3: (-1,0), 4: (-1,1), 5: (0,1)}
ODD_DIRS = {0: (1,0), 1: (1,-1), 2: (0,-1), 3: (-1,0), 4: (0,1), 5: (1,1)}

class BoardItem:
    def __init__(self, x, y):
        self.x = x
        self.y =y
    def get_pos(self):
        return (self.x, self.y)
    def get_x(self):
        return self.x
    def get_y(self):
        return self.y

class Ship(BoardItem):
    def __init__(self, entity_id, x, y, rotation, speed, rum, is_mine):
        self.rotation = rotation
        self.speed = speed
        self.rum = rum
        self.is_mine = is_mine
        self.x = x
        self.y = y
        self.entity_id = entity_id
    def __repr__(self):
        return "Ship " + str(self.entity_id) + " @ " + str(self.get_pos()) + ", is_mine: " + str(self.is_mine)
        
class Barrel(BoardItem):
    def __init__(self, entity_id, x, y, amount):
        self.x = x
        self.y = y
        self.amount = amount
        self.entity_id = entity_id
    def __repr__(self):
        return "Barrel " + str(self.entity_id) + " @ " + str(self.get_pos()) + " w Amount: " + str(self.amount) 

class CannonBall(BoardItem):
    def __init__(self,entity_id,x,y, fired_by, remaining_turns):
        self.entity_id = entity_id
        self.x = x
        self.y = y
        self.fired_by = fired_by
        self.remaining_turns = remaining_turns
    def __repr__(self):
        return "CannonBall " + str(self.entity_id) + " @ " + str(self.get_pos()) + " fired by " + self.fired_by + " remaining turns " + self.reremaining_turns
class Mine(BoardItem):
    def __init__(self,entity_id, x,y):
        self.x = x
        self.y = y
        self.entity_id = entity_id

##Printing
def print_debug(s):
    print >> sys.stderr, s
def pprint_debug(s):
    pprint.pprint(s,stream=sys.stderr)
    

##Pathfinding
def quick_dist(pos_1,pos_2):
    #http://keekerdc.com/2011/03/hexagon-grids-coordinate-systems-and-distance-calculations/
    x_1 = pos_1[0]
    y_1 = pos_1[1]
    z_1 = -1 * (x_1 + y_1)
    x_2 = pos_2[0]
    y_2 = pos_2[1]
    z_2 = -1 * (x_2 + y_2)
    
    return max([x_2 - x_1, y_2 - y_1, z_2 - z_1])
    
def calculate_closest_object(origin, objects):
    closest_object = None
    closest_distance = float("inf")
    for o in objects:
        current_distance = quick_dist(origin.get_pos(), o.get_pos())
        if current_distance < closest_distance:
            closest_object = o
            closest_distance = current_distance
    return closest_object, closest_distance

class Brain:
    def __init__(self, ship, my_other_ships, opponent_ships, barrels, mines, cannon_balls):
        self.ship = ship
        self.my_other_ships = my_other_ships
        self.opponent_ships = opponent_ships
        self.barrels = barrels
        self.mines = mines
        self.cannon_balls = cannon_balls

    def get_next_action(self):
        # Write an action using print
        # To debug: print >> sys.stderr, "Debug messages..."
        closest_barrel, barrel_distance = calculate_closest_object(self.ship, self.barrels)
        closest_opposing_ship, closest_opposing_ship_distance = calculate_closest_object(self.ship, self.opponent_ships)
        
        try:
            rum_value = self.calculate_rum_value(self.ship.rum, barrel_distance, closest_barrel.amount, self.ship.speed)
        except AttributeError:
            #Happens when no barrels
            rum_value = 0
            closest_barrel = Barrel("XXX",0,0,-100)
        fire_value = self.calculate_fire_value(closest_opposing_ship.rum, closest_opposing_ship_distance)
        move_towards_closest_ship_value = self.calculate_move_towards_closest_ship_value(closest_opposing_ship_distance, closest_opposing_ship.rum, self.ship.speed)
        
        weighed_options = [(rum_value, closest_barrel.get_pos(), "MOVE "), (fire_value, find_fire_pos(ship, closest_opposing_ship), "FIRE "), (move_towards_closest_ship_value, closest_opposing_ship.get_pos(), "MOVE ")]
        
        print_debug("Rum Value: " + str(rum_value))
        print_debug("Fire Value: " + str(fire_value))
        print_debug("Move towards closest ship value: " + str(move_towards_closest_ship_value))
        
        next_action = max(weighed_options)
        if next_action[2] == "MOVE ":
            next_pos = avoid_obstacles((next_action[1][0], next_action[1][1]), ship, mines + opponent_ships)
            return "MOVE " + str(next_pos[0]) + " " + str(next_pos[1])
        else:
            return next_action[2] + str(next_action[1][0]) + " " + str(next_action[1][1])

    def calculate_rum_value(self, current_rum, distance, rum_in_barrel, current_speed):
        return (100 - current_rum) ** 1.2 - distance + ((2 - current_speed) ** 10)

    def calculate_fire_value(self, enemy_rum, distance):
        if distance > 10:
            return 0
        else:
            return ((100 - enemy_rum) ** 1.15) + ((10 - distance) ** 2 ) + 3

    def calculate_move_towards_closest_ship_value(self, distance, enemy_rum, current_speed):
        return distance ** 1.6 + (100 - enemy_rum) + ((2 - current_speed) ** 10)
    
##POINT MATH
def pos_add(pos_1,pos_2):
    return (pos_1[0] + pos_2[0], pos_1[1] + pos_2[1])

def get_next_pos_based_on_heading(pos,heading):
    if(pos[1] % 2 == 0):
        direction_of_travel = EVEN_DIRS[heading]
    else:
        direction_of_travel = ODD_DIRS[heading]
    return pos_add(pos,direction_of_travel)
    

##MISC
def find_fire_pos(origin_ship, target_ship):
    '''
    Calculates where a ship should fire based on distance and current heading
    Used for leading a shot
    '''
    ship_distance = quick_dist(origin_ship.get_pos(), target_ship.get_pos())
    turns_until_hit = int(round((1 + ship_distance) / 3))

    fire_pos = target_ship.get_pos()
    
    for i in xrange(turns_until_hit * target_ship.speed):
        #TODO This doesn't account for how long it will take to hit after movement
        fire_pos = get_next_pos_based_on_heading(fire_pos,target_ship.rotation)
    print_debug("Predicting Opposing Ship will be at " + str(fire_pos))
    return fire_pos

def avoid_obstacles(desired, ship, obstacles):
    first_step = get_next_pos_based_on_heading(ship.get_pos(),ship.rotation)
    next_step = get_next_pos_based_on_heading(first_step,ship.rotation)
    
    obstacle_set = set(map(lambda a: a.get_pos(), obstacles))
    next_steps = {first_step,next_step}
    pprint_debug(next_steps)
    common = next_steps.intersection(obstacle_set)
    
    if len(common) != 0:
        print_debug("Need to avoid obstacles @ " + str(common))
        return pos_add(common.pop(),(1,1))
    else:
        return desired

# game loop
while True:
    my_ship_count = int(raw_input())  # the number of remaining ships
    entity_count = int(raw_input())  # the number of entities (e.g. ships, mines or cannonballs)
    barrels = []
    ships = []
    cannon_balls = []
    mines = []
    for i in xrange(entity_count):
        entity_id, entity_type, x, y, arg_1, arg_2, arg_3, arg_4 = raw_input().split()
        entity_id = int(entity_id)
        x = int(x)
        y = int(y)
        arg_1 = int(arg_1)
        arg_2 = int(arg_2)
        arg_3 = int(arg_3)
        arg_4 = int(arg_4)
        if(entity_type=="SHIP"):
            ships.append(Ship(entity_id, x,y,arg_1,arg_2,arg_3,arg_4 == 1))
        if(entity_type=="BARREL"):
            barrels.append(Barrel(entity_id, x,y,arg_1))
        if(entity_type=="MINE"):
            mines.append(Mine(entity_id, x, y))
        if(entity_type=="CANNONBALL"):
            cannon_balls.append(CannonBall(entity_id,x, y, arg_1, arg_2))
    my_ships = filter(lambda ship: ship.is_mine,ships)
    opponent_ships = filter(lambda ship: not ship.is_mine,ships)
    for ship in my_ships:
        brain = Brain(ship, my_ships, opponent_ships, barrels, mines, cannon_balls)
        print(brain.get_next_action())
