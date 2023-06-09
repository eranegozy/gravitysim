# gravitysim: gravity / planetary motion simulation example using python and kivy

## Installation

- Download latest python.
- Create a virtual env if desired.
- Install Kivy (See [installation instructions](https://kivy.org/doc/stable/gettingstarted/installation.html) for more details): `python -m pip install "kivy[base]"`
- Install numpy: `python -m pip install numpy`

## Running
- `python app.py`

## About
- This example simulates the Sun and 3 planetary bodies orbiting the sun.
- See `app.py` for constants / assumptions
- Resize the window as you wish. The simulation will adapt and scale according to the window width
- `MainWidget` is the main window that sets up all the drawing and simulation code
- `Body` is the class that models a planetary body. These are instantiated in `MainWidget`
- `pos_to_screen()` and `scalar_to_screen()` deal with converting world coordinates (in units of km) to screen space (pixels).
- `calculate_forces()` computes gravitational forces that are then applied to the objects.
