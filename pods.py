
import sys
import math

# Auto-generated code below aims at helping you parse
# the standard input according to the problem statement.
class Point:
    '''
    A point on the map
    '''
    def __init__(self, x, y):
        self.x = x
        self.y = y
    def distance_squared(self, other_point):
        return (self.x-other_point.x) ** 2 + (self.y-other_point.y) ** 2
    def distance(self, other_point):
        return math.sqrt(self.distance_squared(other_point))
    def closest(self, point_a, point_b):
        return min([self.distance_squared(point_a),self.distance_squared(point_b)])
class Unit(Point):
    '''
    Unit with an id, radius and speed
    '''
    def __init__(self, x, y, entity_id, r, vx, vy):
        self.x = x
        self.y = y
        self.entity_id = entity_id
        self.rotation = r
        self.x_velocity = vx
        self.y_velocity = vy
    def collision(self, other_unit):
        pass
    def bounce(self, other_unit):
        pass
class CheckPoint(Unit):
    '''
    A checkpoint
    '''
    def __init__(self, x, y, entity_id, r, vx, vy):
        self.x = x
        self.y = y
        self.entity_id = entity_id
        self.radius = r
        self.x_velocity = vx
        self.y_velocity = vy
    def bounce(self, other_unit):
        pass
class Pod(Unit):
    '''
    A pod
    '''
    def __init__(self, x, y, entity_id, r, vx, vy, angle, next_check_point_id, checked, timeout, partner, shield_up):
        self.x = x
        self.y = y
        self.entity_id = entity_id
        self.radius = r
        self.x_velocity = vx
        self.y_velocity = vy
        self.angle = angle
        self.next_check_point_id = next_check_point_id
        self.checked = checked
        self.timeout = timeout
        self.partner = partner
        self.shield_up = shield_up
    def get_absolute_angle(self, point):
        '''
        Returns angle to point
        '''
        distance = self.distance(point)
        x_distance = (point.x - self.x) / distance
        y_distance = (point.y - self.y) / distance
        angle = math.acos(x_distance) * 180 / math.pi
        if  y_distance < 0:
            angle = 360 - angle
        return angle
    def get_diff_angle(self, point):
        '''
        The angle a pod would need to turn to face pod
        If angle is negative turn to left
        if angle is positive turn to right
        '''
        absolute_angle = self.get_absolute_angle(point)
        if self.angle <= absolute_angle:
            right = absolute_angle - self.angle
        else:
            right = 360 - self.angle + absolute_angle
        if self.angle >= absolute_angle:
            left = self.angle - absolute_angle
        else:
            left = self.angle + 360 - absolute_angle
        if right < left:
            return right
        else:
            return left
    def rotate_towards(self, point):
        '''
        Rotate this pod towards point p
        '''
        diff_angle = self.get_diff_angle(point)
        if diff_angle > 18:
           diff_angle = 180 
        if diff_angle < -18:
            diff_angle = -18
        self.angle += diff_angle
        if self.angle >= 360:
            self.angle = self.angle - 360
        if self.angle < 0:
            self.angle += 360
    def boost(self, thrust):
        '''
        Apply thrust to pod
        '''
        if self.shield_up:
            return
        angle_radians = self.angle * math.pi / 180
        self.x_velocity = math.cos(angle_radians) * thrust
        self.y_velocity = math.sin(angle_radians) * thrust
    def move(self, turns):
        '''
        Move the pod forward by t turns 
        t can be float
        '''
        self.x += self.x_velocity * turns
        self.y += self.y_velocity * turns
    def end(self):
        '''
        Apply friction and round values
        '''
        self.x = round(self.x)
        self.y = round(self.y)
        self.x_velocity = int(self.x_velocity * 0.85)
        self.y_velocity = int(self.y_velocity * 0.85)
        self.timeout -= 1
    def play(self,point, thrust):
        '''
        Play an entire turn aiming at point with thrust
        '''
        self.rotate_towards(point)
        self.boost(thrust)
        self.move(1.0)
        self.end
    def output(self):
        pass

class Collision:
    '''
    Represents a collision that will occur at a certain time
    '''
    def __init__(self, a, b, time):
        self.a = a
        self.b = b
        self.time = time
# game loop
while True:
    # next_checkpoint_x: x position of the next check point
    # next_checkpoint_y: y position of the next check point
    # next_checkpoint_dist: distance to the next checkpoint
    # next_checkpoint_angle: angle between your pod orientation and the direction of the next checkpoint
    x, y, next_checkpoint_x, next_checkpoint_y, next_checkpoint_dist, next_checkpoint_angle = [int(i) for i in input().split()]
    opponent_x, opponent_y = [int(i) for i in input().split()]

    # Write an action using print
    # To debug: print("Debug messages...", file=sys.stderr)


    # You have to output the target position
    # followed by the power (0 <= thrust <= 100)
    # i.e.: "x y thrust"
    print(str(next_checkpoint_x) + " " + str(next_checkpoint_y) + " 80")
