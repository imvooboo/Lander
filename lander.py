#!/opt/bin/python
import pygame as pg
from pygame.locals import *
import random
import sys
import math
'''
Lander
'''

#
#          ----- Initialization Section -----
#
# Seed random number generator.
random.seed()

# Pseudo constants, indicated by leading underscore (some settable at the beginning of a game).
_screen_x = 1200              # x extent of the screen in pixels
_screen_y = 650               # y extent of the screen in pixels
_fps = 30                     # frames per second
_g = 0.1                      # gravitational constant, pixels per frame
_at = 0.3                     # acceleration due to thrust
_drag = 0.01                  # atmospheric drag
_y_increment = 20             # y increment for generating land segments, larger is more jagged
_land_pts = _screen_x * 10    # total number of points making up the land; 20 screens
_base_size = int(0.10 * _screen_x)  # size of landing base in pixels
_lander_size = int(_base_size * 0.20)  # side length for bounding box as a percentage of landing base
_max_fuel = 500.0

# Build the land array of points, y vales, that will be connected by lines to form the
# surface of the planet on which the lander must land.  We only need y values since
# x can be calculated on the fly.
_land = list()
_land.append(2 * _screen_y / 3)  # start land two thirds of the way down the screen
for n in range(1, _land_pts):
    k = random.randint(1, 100)
    if k < 20:
        y = max(_land[n-1] - random.randint(1, _y_increment), _screen_y / 3)
    elif k < 80:
        y = _land[n-1]
    else:
        y = min(_land[n-1] + random.randint(1, _y_increment), 5 * _screen_y / 6)
    _land.append(y)

# Randomly locate a landing base between 20% and 40% of the way through the land
base_n = random.randint(int(_land_pts * 0.20), int(_land_pts * 0.40))
flat = [_land[base_n] for x in range(_base_size + 1)]
_land[base_n:base_n+_base_size] = flat

# Initialize pygame engine, the game window, and colors.
pg.init()
fps_clock = pg.time.Clock()
ds = pg.display.set_mode((_screen_x, _screen_y))
pg.display.set_caption('Lander ({}, {})'.format(_screen_x, _screen_y))
black = (0, 0, 0)
white = (255, 255, 255)
green = (0, 255, 0)
yellow = (255, 255, 0)
blue = (0, 0, 255)
red = (255, 0, 0)

# Draw the lander as separate pygame surfaces.  That surface forms the bounding rectangle that will
# be used to check for collisions with the land.  The lander graphic is drawn inside the surface
# which is later blitted onto the screen during the animation.  There are two separate surfaces, one
# with thrust and one without thrust.  The appropriate surface will be blitted to the screen in the
# main loop.
lander_no_thrust = pg.Surface((_lander_size+2, _lander_size+2))
lander_no_thrust.fill(black)
# "Magic" calculations for the points outlining the lander.
x1 = 0; x2 = int(_lander_size / 3); x3 = int(_lander_size / 2); x4 = _lander_size - x2; x5 = _lander_size
x6 = x5; x7 = x3; x8 = x1
y1 = int(_lander_size / 2); y2 = int(_lander_size / 3); y3 = 0; y4 = y2; y5 = y1; y6 = _lander_size
y7 = y1; y8 = y6
lander_outline = [(x1,y1), (x2,y2), (x3,y3), (x4,y4), (x5,y5), (x6,y6), (x7,y7), (x8,y8)]
pg.draw.polygon(lander_no_thrust, blue, lander_outline, 0)

lander_thrust = pg.Surface((_lander_size+2, _lander_size+2))
lander_thrust.fill(black)
thrust_outline = [(x1,y1), (x5,y5), (x3,y8)]
pg.draw.polygon(lander_thrust, yellow, thrust_outline, 0)
pg.draw.polygon(lander_thrust, blue, lander_outline, 0)

# Set up text for safe landing and crash
# set up fonts
basicFont = pg.font.Font('sans.ttf', 48)
data_font = pg.font.Font('Andale Mono.ttf', 24)
# set up the text
landed_text = basicFont.render('Landed Safely!', True, white, black)
crashed_text = basicFont.render('Crashed! :-(', True, white, black)
landed_rect = landed_text.get_rect()
landed_rect.centerx = ds.get_rect().centerx
landed_rect.centery = ds.get_rect().centery
crashed_rect = crashed_text.get_rect()
crashed_rect.centerx = ds.get_rect().centerx
crashed_rect.centery = ds.get_rect().centery

#
#          ----- End Initialization Section -----


#          ----- Main Loop -----
#
# Set up some variables to control the main loop and then loop in the usual pygame way.
#
lander_x = _screen_x / 3  # never changes; always draw the lander at this x location
lander_y = int(_screen_y * 0.1)  # this value will change in the main loop
current_x = 1             # pointer into the _land list used to translate between screen x and
                          # the larger array
rotation = 0              # rotation angle of the lander
thrust = False            # is thrust being applied
Vlx = 5                   # lander x velocity
Vly = -1                  # lander y velocity
landed = False            # have we landed safely
crashed = False           # have we crashed
fuel = float(_max_fuel)          # fill the tank

while (not landed) and (not crashed):
    ds.fill(black)

    # check for quit event and exit
    for event in pg.event.get():
        if event.type == QUIT:
            pg.quit()
            sys.exit()

    # check for left or right arrow key and set rotation accordingly
    keys = pg.key.get_pressed()
    if keys[K_LEFT] != 0:
        rotation += 1
    elif keys[K_RIGHT] != 0:
        rotation -= 1

    # check for space key pressed and set lander to show thrust if it is
    if keys[K_SPACE] != 0 and fuel:
        lander = lander_thrust
        thrust = True
        fuel -= 1
    else:
        lander = lander_no_thrust
        thrust = False

    assert(current_x + _screen_x < _land_pts)
    for n in range(current_x, _screen_x + current_x):
        if (n > base_n) and (n < base_n + _base_size):
            pg.draw.line(ds, green, (n-1-current_x, _land[n-1]), (n-current_x, _land[n]), 2)
        else:
            pg.draw.line(ds, white, (n-1-current_x, _land[n-1]), (n-current_x, _land[n]), 2)

    # apply physics! (remember y axis is positive in the downward direction)
    angle = rotation * math.pi / 180
    if Vlx < 0:
        drag = _drag
    else:
        drag = -_drag
    if thrust:

        new_v_x = Vlx + _at * math.sin(-angle) + drag
        new_v_y = Vly + (_g - (_at * math.cos(angle)))
    else:
        new_v_x = Vlx + drag
        new_v_y = Vly + _g

    current_x += int(new_v_x)
    lander_y += int(new_v_y)
    Vlx = new_v_x
    Vly = new_v_y

    adjusted_lander = pg.transform.rotate(lander, rotation)
    lander_rect = ds.blit(adjusted_lander, (lander_x, lander_y))
    lander_bounding_box = lander_rect.move(current_x, 0)
    vx_data = data_font.render('Vx: ' + '%5.2f' % Vlx, True, white, black)
    vy_data = data_font.render('Vy: ' + '%5.2f' % -Vly, True, white, black)
    rot_data = data_font.render('Rot: ' + '%2d deg' % rotation, True, white, black)
    fuel_ratio = 100. * fuel / _max_fuel
    fuel_data = data_font.render('Fuel: ' + '%5.2f%%' % fuel_ratio, True, white, black)
    fuel_rect = pg.Rect(5, _screen_y * 0.20, _lander_size * 5, _lander_size)
    fuel_status = pg.Rect(5, _screen_y * 0.20 + 2, _lander_size * 5 * fuel / _max_fuel + 2, _lander_size - 2)
    ds.blit(vx_data, (5, _screen_y * 0.01))
    ds.blit(vy_data, (5, _screen_y * 0.05))
    ds.blit(rot_data, (5, _screen_y * 0.10))
    ds.blit(fuel_data, (5, _screen_y * 0.15))
    pg.draw.rect(ds, white, fuel_rect, 2)
    if fuel_ratio > 60.:
        pg.draw.rect(ds, green, fuel_status, 0)
    elif fuel_ratio > 40.:
        pg.draw.rect(ds, yellow, fuel_status, 0)
    else:
        pg.draw.rect(ds, red, fuel_status, 0)

    # check for crash or landing
    for n in range(current_x + lander_x, current_x + lander_x + _lander_size):
        if lander_bounding_box.collidepoint(n, _land[n]):   # could be a crash, need to check for base
            crashed = True
            if (n > base_n) and (n < base_n + _base_size):  # on the base so this could be a landing
                if math.fabs(rotation) < 5.1:               # not rotated too far
                    if math.fabs(Vlx < 2.1):                # not moving too fast sideways
                        if math.fabs(Vly < 2.1):            # or vertically...safe landing!
                            crashed = False
                            landed = True

    if landed:
        ds.blit(landed_text, landed_rect)
    elif crashed:
        ds.blit(crashed_text, crashed_rect)

    pg.display.update()
    fps_clock.tick(_fps)

# freeze the last screen until exit
while True:
    # check for quit event and exit
    for event in pg.event.get():
        if event.type == QUIT:
            pg.quit()
            sys.exit()
#
#          ----- End of main loop -----






