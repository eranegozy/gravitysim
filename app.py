#####################################################################
#
# Copyright (c) 2023 Eran Egozy
# License: MIT
#
#####################################################################


from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.graphics import Ellipse, Color, Line
from kivy.graphics.instructions import InstructionGroup

import numpy as np
from math import atan2, sin, cos

# Define size and center coordinate of world
WORLD_WIDTH = 5e8     # world length (in km) visible in window's width
WORLD_CENTER = (0, 0) # coordinates of world center

# mass in kg
MASS_EARTH = 5.9722e24
MASS_SUN = 333000 * MASS_EARTH
MASS_VENUS = 0.815 * MASS_EARTH
MASS_MERCURY = 0.0553 * MASS_EARTH

# radius in km
RAD_SUN = 695700
RAD_EARTH = 6378.1
RAD_VENUS = 6052
RAD_MERCURY = 2439.4

# distances to sun in km
DIST_EARTH = 149600000
DIST_VENUS = 108200000
DIST_MERCURY = 57900000

# speeds in km/s
SPEED_EARTH = 29.7848
SPEED_MERCURY = 47
SPEED_VENUS = 35.02

# gravity constant in km^3 / (kg s^2)
GRAVITY_CONST = 6.6743e-20

# each simulation step advances time by this many seconds
DELTA_T = 100

# run this many simulation steps for each graphical update
STEPS_PER_RENDER = 100


def pos_to_screen(pos):
    'Given a position (2D vector in world coordinates), return screen coordinates in pixels'
    w,h = Window.width, Window.height
    ratio = w / WORLD_WIDTH
    return (pos - np.array(WORLD_CENTER)) * ratio + np.array((w,h)) / 2

def scalar_to_screen(s):
    'Given a scalar in world coordinates (like size), return it in units of pixels'
    ratio = Window.width / WORLD_WIDTH
    return s * ratio

def calculate_forces(objects):
    '''For a given list of objects, calculate all accumulated forces on each object, and set the force. 
    Each object must have self.pos, self.mass, and set_force() '''

    # forces will be accumulated per object
    forces = { obj:np.zeros((2)) for obj in objects }

    # iterate through all pairs of objects, such that each pair is addressed once
    num_objects = len(objects)
    for i1 in range(num_objects-1):
        for i2 in range(i1+1, num_objects):
            obj1 = objects[i1]
            obj2 = objects[i2]

            # dx, dy and distance between 2 objects
            delta = obj2.pos - obj1.pos
            dist = np.linalg.norm(delta)

            # force calculation
            f_mag = GRAVITY_CONST * obj1.mass * obj2.mass / dist**2

            # find force components in x and y
            theta = atan2(delta[1], delta[0]) # angle between the two objects
            fx = f_mag * cos(theta)
            fy = f_mag * sin(theta)
            f = np.array((fx, fy))
            
            # accumulate forces for each object
            forces[obj1] += f
            forces[obj2] += -f

    # set accumulated force on each object
    for obj in forces:
        obj.set_force(forces[obj])


class MainWidget(Widget):
    def __init__(self, **kwargs):
        super(MainWidget, self).__init__(**kwargs)

        # schedule a polling function callback every graphics frame
        Clock.schedule_interval(self.on_update, 0)

        # text display
        self.info = Label(pos=(200, 200), halign='left', valign='bottom', text_size = (400, 400))
        self.add_widget(self.info)

        # global simulation time, in seconds
        self.time = 0

        # objects of the simulation
        self.objects = []

        # For enhanced visibility, scale object radii by some factor
        # Sun
        self.objects.append(Body(pos = (0, 0), vel = (0, 0), radius = RAD_SUN * 20, mass = MASS_SUN, hue = 0.2))
        # Mercury
        self.objects.append(Body(pos = (DIST_MERCURY, 0), vel = (0, SPEED_MERCURY), radius = RAD_MERCURY * 1000, mass = MASS_MERCURY, hue = 0.4))
        # Venus
        self.objects.append(Body(pos = (DIST_VENUS, 0), vel = (0, SPEED_VENUS), radius = RAD_VENUS * 1000, mass = MASS_VENUS, hue = 0.8))
        # Earth
        self.objects.append(Body(pos = (DIST_EARTH, 0), vel = (0, SPEED_EARTH), radius = RAD_EARTH * 1000, mass = MASS_EARTH, hue = 0.6))

        # add objects to canvas so they are displayed
        for obj in self.objects:
            self.canvas.add(obj)

    # called every graphics frame
    def on_update(self, dt):
        # dt is normally the time in seconds between graphics frames.
        # instead, use a constant to advance time much faster.
        dt = DELTA_T

        # run simulation for many time steps, and then render once after that
        for s in range(STEPS_PER_RENDER):
            self.time += dt

            calculate_forces(self.objects)

            for obj in self.objects:
                obj.update_state(dt)

        # update graphics
        for obj in self.objects:
            obj.update_graphics()

        # update text info
        self.info.text = f'time: {self.time / (3600*24):.2f} days\n'


class Body(InstructionGroup):
    'A celestial body with initial position and velocity, mass, radius, and color (hue)'
    def __init__(self, pos, vel, mass, radius, hue):
        super(Body, self).__init__()

        # state variables
        self.pos = np.array(pos)
        self.vel = np.array(vel)
        self.mass = mass
        self.radius = radius

        # force is a 2D vector, set by external calculation
        self.force = np.zeros((2))

        # create trail (draw first so it is behind the circle)
        self.trail = Trail()
        self.add(self.trail)

        # create a color and a circle to represent this object
        self.circle = Ellipse(pos=self.pos, size=(2 * self.radius, 2 * self.radius))
        self.add( Color(hsv = (hue, .8, 1)))
        self.add( self.circle )

    def set_force(self, f):
        # apply externally calculated force to this object
        self.force = f

    def update_state(self, dt):
        # F = m * a
        a = self.force / self.mass

        # 1st order Euler integration step (this could be improved!!)
        self.pos = self.pos + self.vel * dt
        self.vel = self.vel + a * dt

    def update_graphics(self):
        # convert from world parameters to screen coordinates:
        sr = scalar_to_screen(self.radius)
        self.circle.size = (sr*2, sr*2)
        self.circle.pos =  pos_to_screen(self.pos - self.radius) # registration point of ellipse is bottom-left corner. We want circles centered

        # update trail
        self.trail.set_pos(self.pos)
        self.trail.update_graphics()


class Trail(InstructionGroup):
    'Draws a trail to highlight recent motion of object'
    def __init__(self):
        super(Trail, self).__init__()

        # list of points that make up the trail
        self.points = []

        # A white line. Points of line are calculated in update_graphics()
        self.add(Color(1,1,1))
        self.line = Line(width=2)
        self.add(self.line)

    def set_pos(self, pos):
        'set a new position in units of world coordinates'

        # must have at least two points to make a line
        if len(self.points) < 2:
            self.points.append(pos)

        # if new pos is very close to last pos, don't add the point. Just update the last pos to current.
        elif np.linalg.norm(self.points[-2] - pos) < (WORLD_WIDTH * 0.01):
            self.points[-1] = pos
        
        # if new pos is far away from previous pos, add it.
        else:
            self.points.append(pos)

        # remove old points.
        if len(self.points) > 100:
            self.points = self.points[1:]

    def update_graphics(self):
        # convert points to screen coordinates and set the line's points
        screen_points = []
        for p in self.points:
            screen_points = screen_points + pos_to_screen(p).tolist()
        self.line.points = screen_points
            

# Build and run the app
class MainApp(App):
    def build(self):
        return MainWidget()
    
MainApp().run()
