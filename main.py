import curses
import json
import sys
import time

from classes.SafeSkiingSimulator import SafeSkiingSimulator
from classes.SkiPass import SkiPass

def gui(stdscr, a , b):
    #stdscr = curses.initscr()
    print (a, b)
    while True:
        stdscr.addstr(0,0,"Slope {}".format(a))
        stdscr.addstr(1,0,"Slope {}".format(b))
        stdscr.move(curses.LINES - 1, 0)
        stdscr.refresh()
        time.sleep(1)

if __name__ == '__main__':
    with open('config.json') as f:
        config = json.load(f)

    #gui()
    sim = SafeSkiingSimulator(config,initial_people=100)

    for slope in sim.slopes:
        print(slope.get_info())


    sim.simulate(gui_enabled=True, n_steps=100,sleep_time=1)

    #curses.wrapper(gui, 2, 2)